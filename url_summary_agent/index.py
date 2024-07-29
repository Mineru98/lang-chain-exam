import getpass
import os
import platform
import subprocess
import time
from urllib.parse import unquote, urlparse

import fire
from langchain_google_genai import ChatGoogleGenerativeAI

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Provide your Google API Key")


def decode_url_encoded_string(encoded_string):
    # URL 인코딩된 문자열을 디코딩하여 원래 문자열로 변환
    decoded_string = unquote(encoded_string)
    return decoded_string


def extract_path(url: str):
    parsed_url = urlparse(url)
    return parsed_url.path.strip("/")


def process_url(url: str):
    output = extract_path(url)
    if output == "":
        raise ValueError("URL path is empty.")
    output = output.split("/")[-1]
    output = decode_url_encoded_string(output)
    cmd = f'clipper clip -u "{url}" -o "{output}.tmp.md"'
    subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return f"{output}.tmp.md"


def remove_urls_from_md(filepath: str):
    with open(filepath, mode="r", encoding="utf-8") as f:
        lines = f.readlines()
    content = "\n".join(lines)
    return content


def get_unique_filepath(filepath):
    # 파일이 존재하는지 확인
    if not os.path.exists(filepath):
        return filepath

    # 파일명과 확장자를 분리
    base, ext = os.path.splitext(filepath)

    # 숫자를 붙일 수를 저장할 변수
    counter = 1

    # 새로운 파일명을 찾을 때까지 반복
    while True:
        # 새로운 파일명 생성
        new_filepath = f"{base}_{counter}{ext}"

        # 새로운 파일명이 존재하지 않으면 반환
        if not os.path.exists(new_filepath):
            return new_filepath

        # 숫자를 증가시키고 반복
        counter += 1


class UrlSummaryAgent:
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

    def run(self, url: str, prompt: str = "", model: str = "gemini-1.5-flash"):
        self.__check()
        llm = ChatGoogleGenerativeAI(model=model)
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
        tmp_filepath = filepath
        filepath = tmp_filepath.replace(".tmp", "")
        filepath = get_unique_filepath(filepath)
        with open(filepath, mode="w", encoding="utf-8") as f:
            f.write(result.content)
        os.remove(tmp_filepath)


if __name__ == "__main__":
    fire.Fire(UrlSummaryAgent)
