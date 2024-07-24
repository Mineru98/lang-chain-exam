import os
import subprocess
from collections import defaultdict
from typing import Optional

import cssutils
import fire
import orjson
import requests
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI


def hex_to_decimal(hex_string):
    """
    문자열로 된 16진수를 10진수로 변환하는 함수.

    :param hex_string: 16진수 문자열 (예: '1A3F')
    :return: 10진수 정수 값
    """
    try:
        # int 함수에 두 번째 인수로 16을 전달하여 16진수를 10진수로 변환
        decimal_value = int(hex_string, 16)
        return decimal_value
    except ValueError:
        # 16진수 문자열이 유효하지 않은 경우 예외 처리
        return "Invalid hexadecimal string"


def reconstruct_sort(data):
    # Group data by pages
    pages = defaultdict(list)

    # Group content by page
    for item in data:
        pages[item["page"]].append(item)

    sorted_pages = {}

    for page, content in pages.items():
        # Separate left and right columns
        left_column = [
            item for item in content if item.get("left", 0) < 300
        ]  # Assuming left column items have 'left' value < 300
        right_column = [
            item for item in content if item.get("left", 0) >= 300
        ]  # Assuming right column items have 'left' value >= 300

        if not left_column or not right_column:
            layout_type = "B"  # Single column
        elif len(left_column) == len(right_column):
            layout_type = "A"  # Left and right columns
        else:
            layout_type = "C"  # Mixed layout

        def sort_key(item):
            return item.get(
                "bottom", float("inf")
            )  # Items without 'bottom' will be placed at the end

        if layout_type == "A":
            left_column_sorted = sorted(left_column, key=sort_key, reverse=True)
            right_column_sorted = sorted(right_column, key=sort_key, reverse=True)
            sorted_content = left_column_sorted + right_column_sorted
        elif layout_type == "B":
            sorted_content = sorted(content, key=sort_key, reverse=True)
        elif layout_type == "C":
            left_column_sorted = sorted(left_column, key=sort_key, reverse=True)
            right_column_sorted = sorted(right_column, key=sort_key, reverse=True)
            sorted_content = left_column_sorted + right_column_sorted

        sorted_pages[str(page)] = {
            "layout_type": layout_type,
            "content": sorted_content,
        }

    return sorted_pages


def merge_lines(data):
    if not data:
        return []

    result = []
    i = 0
    while i < len(data):
        if i < len(data) - 1 and data[i].endswith("-\n"):
            # 현재 문자열과 다음 문자열을 합친다
            result.append(
                data[i][:-2] + data[i + 1]
            )  # '-\n'을 제거하고 다음 문자열을 추가
            i += 2  # 두 문자열을 처리했으므로 인덱스를 두 칸 이동
        else:
            result.append(data[i])
            i += 1  # 다음 문자열로 이동

    return result


def extract_left_properties(html_content):
    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html_content, "lxml")

    # 모든 style 태그의 내용을 가져옵니다
    style_tags = soup.find_all("style")
    css_content = " ".join([tag.string for tag in style_tags if tag.string])

    # cssutils를 사용하여 CSS 파싱
    stylesheet = cssutils.parseString(css_content)

    # div 태그와 관련된 클래스 선택자와 해당 left 값을 저장할 딕셔너리
    div_left_properties = {}
    div_bottom_properties = {}

    for rule in stylesheet:
        if rule.type == rule.STYLE_RULE:
            # div 태그와 관련된 클래스 선택자만 처리
            for property in rule.style:
                if property.name == "left":
                    div_left_properties[rule.selectorText] = property.value
                if property.name == "bottom":
                    div_bottom_properties[rule.selectorText] = property.value
    div_left_properties_keys = set(list(div_left_properties.keys()))
    div_bottom_properties_keys = set(list(div_bottom_properties.keys()))
    container = soup.find("div", {"id": "page-container"})
    results = []
    for div in container.find_all("div"):
        parent_element = div.parent
        if parent_element.has_attr("id"):
            page = parent_element["id"].replace("pf", "")
        class_name = div.get("class")
        if class_name:
            class_name = list(map(lambda x: "." + x, class_name))
            class_selector = "".join(class_name)
            item = {"selector": class_selector, "page": page}
            if set(class_name) & div_left_properties_keys:
                common_elements = set(class_name) & div_left_properties_keys
                item["left"] = float(
                    div_left_properties[common_elements.pop()].replace("px", "")
                )
            if set(class_name) & div_bottom_properties_keys:
                common_elements = set(class_name) & div_bottom_properties_keys
                item["bottom"] = float(
                    div_bottom_properties[common_elements.pop()].replace("px", "")
                )
            if len(item.keys()) > 2:
                item["content"] = div.text
                results.append(item)
    results = list(map(lambda x: {**x, "page": hex_to_decimal(x["page"])}, results))
    return results


class Main:
    def run(self, filepath: str, prompt: Optional[str]):
        if not os.path.exists(filepath):
            raise "파일이 존재하지 않습니다."
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
        with open(filepath, mode="r", encoding="utf-8") as f:
            content = f.read()
        if prompt is None:
            messages = [
                (
                    "system",
                    "나는 AI 연구자 입니다. 연구자 입장에서 해당 논문들을 분석한 결과를 한글로 상세히 정리해줘.",
                ),
                ("human", f"### 입력 데이터\n{content}\n### 출력\n"),
            ]
        else:
            messages = [
                ("system", prompt),
                ("human", f"### 입력 데이터\n{content}\n### 출력\n"),
            ]
        result = llm.invoke(messages)
        with open(filepath.replace(".txt", ".md"), mode="w", encoding="utf-8") as f:
            f.write(result.content)

    def load(self, url: str, name: Optional[str]):
        if name is None:
            filename = url.replace("https://", "").replace("http://", "")
        elif name.endswith(".pdf"):
            filename = name
        res = requests.get(url)
        content_type = res.headers.get("Content-Type")
        if content_type == "application/pdf":
            with open(filename, "wb") as f:
                f.write(res.content)
        else:
            raise "해당 링크는 PDF 파일이 아닙니다."
        if os.path.exists(filename):
            subprocess.run(
                f"docker run -ti --rm -v `pwd`:/pdf sergiomtzlosa/pdf2htmlex pdf2htmlEX --zoom 1.3 {filename}",
                shell=True,
            )
            os.remove(filename)
        filename = filename.replace(".pdf", ".html")
        rows = []
        with open(filename, "r") as f:
            rows = extract_left_properties(f)
        os.remove(filename)
        if len(rows) > 0:
            rows = list(filter(lambda x: len(x["content"]) < 1000, rows))
            rows = reconstruct_sort(rows)
            with open(filename.replace(".html", ".json"), "w", encoding="utf-8") as f:
                f.write(orjson.dumps(rows, option=orjson.OPT_INDENT_2).decode("utf-8"))
            os.remove(filename.replace(".html", ".json"))
            lines = []
            count = 1
            for k in rows:
                stack_bottom = None
                stack_left = None
                lines.append(f"\n\n# Page {count}\n")
                for line in rows[k]["content"]:
                    if stack_left is None:
                        stack_left = float(line.get("left", 0))
                    if stack_bottom is None:
                        stack_bottom = float(line.get("bottom", 0))
                    if stack_bottom != float(line.get("bottom", 0)):
                        lines.append(line["content"] + "\n")
                    else:
                        lines.append(line["content"])
                count += 1
            lines = merge_lines(lines)
            lines = "".join(lines).strip()
            with open(filename.replace(".html", ".txt"), "w", encoding="utf-8") as f:
                f.write(lines)


if __name__ == "__main__":
    fire.Fire(Main)
