import getpass
import json
import os
import re
import subprocess
import time
from typing import Dict
from urllib.parse import urlparse

import fire
import requests
from langchain_google_genai import ChatGoogleGenerativeAI

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Provide your Google API Key")


def extract_path(url: str):
    parsed_url = urlparse(url)
    return parsed_url.path.strip("/")


def process_url(url: str):
    output = extract_path(url)
    if output == "":
        raise ValueError("URL path is empty.")
    output = output.split("/")[-1]
    cmd = f"clipper clip -u {url} -o {output}.md"
    subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return f"{output}.md"


def remove_urls_from_md(filepath: str):
    with open(filepath, mode="r", encoding="utf-8") as f:
        lines = f.readlines()
    content = "\n".join(lines)
    return content


class Main:
    def __check(self):
        res = subprocess.run(
            "which clipper", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if res.returncode == 1:
            subprocess.run("npm i -g @philschmid/clipper", shell=True)

    def run(self, url: str, prompt: str = ""):
        self.__check()
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
        filepath = process_url(url)
        while not os.path.exists(filepath):
            print("파일이 존재하지 않아 잠시 멈췄습니다.")
            time.sleep(0.5)
        content = remove_urls_from_md(filepath)
        messages = [
            (
                "system",
                "한글로 다음 내용들을 요약해줘." + prompt,
            ),
            ("human", f"### 입력 데이터\n{content}\n### 출력\n"),
        ]
        result = llm.invoke(messages)
        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write(result.content)


if __name__ == "__main__":
    fire.Fire(Main)
