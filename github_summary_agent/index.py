import getpass
import json
import os
import platform
import re
import subprocess
import time
from typing import Dict

import fire
import requests
from langchain_google_genai import ChatGoogleGenerativeAI

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Provide your Google API Key")

# GitHub Personal Access Token
if "GITHUB_TOKEN" not in os.environ:
    os.environ["GITHUB_TOKEN"] = getpass.getpass("Provide your Github Token Key")
token = os.environ["GITHUB_TOKEN"]
headers = {"Authorization": f"token {token}"}


def get_codes(row: Dict):
    repo = row["repo"]
    url = f"https://api.github.com/repos/{repo}/languages"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        res = response.json()
        row["codes"] = res
    return row


def get_repo(repo: str):
    url = f"https://api.github.com/repos/{repo}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        row = response.json()
        return {
            "url": row["html_url"],
            "description": row["description"],
            "topics": row["topics"],
            "repo": row["full_name"],
        }


def process_url(url: str):
    user_name = url.split("/")[-2]
    repo_name = url.split("/")[-1]
    cmd = f'clipper clip -u "{url}" -o "{user_name}_{repo_name}.md"'
    subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return f"{user_name}_{repo_name}.md"


def remove_consecutive_newlines(text):
    pattern = r"\n{2,}"
    new_text = re.sub(pattern, "\n", text)
    if new_text == text:
        return text
    return remove_consecutive_newlines(new_text)


def normalize_whitespace(text: str):
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r"^ +| +$", "", text, flags=re.MULTILINE)
    text = text.strip()
    text = remove_consecutive_newlines(text)
    return text


def remove_code_blocks(markdown_text):
    # 개선된 정규 표현식 패턴
    pattern = r"(```[^\n]*\n)(?:(?!```).)*?\n```"

    # 코드 블록을 빈 문자열로 대체
    cleaned_text = re.sub(pattern, "", markdown_text, flags=re.DOTALL)

    return cleaned_text


def remove_urls_from_md(filepath: str):
    with open(filepath, mode="r", encoding="utf-8") as f:
        lines = f.readlines()
    content = "\n".join(lines)
    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    md_link_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
    content = remove_code_blocks(content)
    content = re.sub(url_pattern, "", content)
    content = re.sub(md_link_pattern, r"\1", content)
    content = content.replace("()", "")
    content = normalize_whitespace(content)
    return content


class GithubSummaryAgent:
    def __check(self):
        if platform.system() == "Windows":
            cmd = "where clipper"
        else:
            cmd = "which clipper"
        res = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if res.returncode == 1:
            subprocess.run(
                "npm i -g @philschmid/clipper",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

    def run(self, url: str, model: str = "gemini-1.5-flash"):
        self.__check()
        if not url.startswith("https://github.com/"):
            raise "github 링크가 아닙니다."
        llm = ChatGoogleGenerativeAI(model=model)
        filepath = process_url(url)
        while not os.path.exists(filepath):
            print("파일이 존재하지 않아 잠시 멈췄습니다.")
            time.sleep(0.5)
        url = url.replace("https://github.com/", "")
        row = get_repo(url)
        row = get_codes(row)
        row["content"] = remove_urls_from_md(filepath)
        content = json.dumps(row, ensure_ascii=False)
        messages = [
            (
                "system",
                """### 명령어
나는 옵시디언에 데이터를 수집하고 싶어. 내가 만든 스타일대로 markdown 양식으로 변환해줘.
### 요구사항
- summary는 content에 있는 내용을 참고해서 어떤 프로젝트인지를 요약 해서 설명해줘.
- summary는 반드시 한글로 작성해줘.
- tags는 이 깃헙 링크를 분류하기 위한 목적으로 만들어 주세요.
- tgas는 최대 5개까지만 만들어주세요.
- aliases는 내가 해당 프로젝트를 찾기 쉽게 하도록 하기 위한 내용입니다.
### 양식
```
---
Language: {main_code_language}
tags:
 - {tag_name_1}
 - {tag_name_2}
 - ...
aliases:
 - {alias_1}
 - {alias_2}
 - ...
url: {github_url}
---
{summary}
```
""",
            ),
            ("human", f"### 입력 데이터\n{content}\n### 출력\n"),
        ]
        result = llm.invoke(messages)
        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write(result.content[4:-3])


if __name__ == "__main__":
    fire.Fire(GithubSummaryAgent)
