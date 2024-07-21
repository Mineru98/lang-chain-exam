import getpass
import json
import os
import re
import time

import orjson
from langchain_google_genai import ChatGoogleGenerativeAI
from tqdm import tqdm

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Provide your Google API Key")


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


with open("my_repo.json", mode="r", encoding="utf-8") as f:
    rows = orjson.loads(f.read())
with open("save.json", mode="r", encoding="utf-8") as f:
    rows = orjson.loads(f.read())

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

try:
    for i, row in tqdm(enumerate(rows), total=len(rows)):
        if "result" in row.keys():
            continue
        url = row["url"]
        user_name = url.split("/")[-2]
        repo_name = url.split("/")[-1]
        row["content"] = remove_urls_from_md(f"output/{user_name}_{repo_name}.md")
        content = json.dumps(row, ensure_ascii=False)

        messages = [
            (
                "system",
                """### 명령어
나는 옵시디언에 데이터를 수집하고 싶어. 내가 만든 스타일대로 markdown 양식으로 변환해줘.
### 요구사항
- summary는 content에 있는 내용을 참고해서 어떤 프로젝트인지를 요약 해서 설명해줘.
- summary는 반드시 한글로 작성해줘.
- tags는 이 깃헙 링크를 분류하기 위한 목적으로 만들어 주세요. 반드시 #을 붙여주세요.
- aliases는 내가 해당 프로젝트를 찾기 쉽게 하도록 하기 위한 내용입니다.
### 양식
```
---
Language: {main_code_language}
tags:
- #{tag_name_1}
- #{tag_name_2}
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
        if i != 0 and i % 15 == 0:
            time.sleep(60)
        result = llm.invoke(messages)
        rows[i]["result"] = result.content
        if i != 0 and i % 10 == 0:
            with open("save.json", "w", encoding="utf-8") as f:
                f.write(orjson.dumps(rows, option=orjson.OPT_INDENT_2).decode("utf-8"))
except Exception as e:
    print(e)
finally:
    with open("save.json", "w", encoding="utf-8") as f:
        f.write(orjson.dumps(rows, option=orjson.OPT_INDENT_2).decode("utf-8"))
