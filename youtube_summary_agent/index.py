import getpass
import os
import re
from urllib.parse import parse_qs, urlparse

import fire
import requests
from langchain_google_genai import ChatGoogleGenerativeAI
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Provide your Google API Key")


def clean_title(title: str):
    # 특수문자 제거 (알파벳, 숫자, 공백만 남김)
    title = re.sub(r"[^\w\s]", "", title)
    # 공백을 밑줄로 대체
    title = title.replace(" ", "_")
    return title


def get_youtube_info(url: str):
    try:
        yt = YouTube(url)
        title = yt.title
        title = title.replace("/", "")
        thumbnail_url = yt.thumbnail_url
        thumbnail_path = "{}.jpg".format(title[:100])
        res = requests.get(thumbnail_url)
        with open(thumbnail_path, "wb") as f:
            f.write(res.content)
        return title, thumbnail_path
    except Exception as e:
        print(f"오류 발생: {str(e)}")


def get_youtube_video_id(url: str):
    if url.startswith("https://youtu.be/"):
        video_id = url.split("/")[-1]
    elif url.startswith("https://www.youtube.com/watch?"):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get("v", [None])[0]
    return video_id


class Main:
    def run(self, url: str, script: bool = False):
        title, thumbnail_path = get_youtube_info(url)
        video_id = get_youtube_video_id(url)
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko"])
        content = [i for i in srt if i["text"] != "[음악]"]
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
        base_script = """### 명령어
나는 옵시디언에 데이터를 수집하고 싶어. 내가 만든 스타일대로 markdown 양식으로 변환해줘.
### 요구사항
- timestamp_summary는 적절하게 타임스탬프를 큰 내용 단위로 나눠줘.
- timestamp_summary는 정적인 분위기가 아닌, 얘기를 하듯이 작성해줘.
- timestamp_summary는 반드시 한글로 작성해줘.
- tags는 이 영상을 분류하기 위한 목적으로 만들어줘,
- tgas는 최대 5개까지만 만들어줘,
- 타임라인은 5분 미만의 영상의 경우에는 최소 3개의 타임라인이 나와야 하고 10분 미만의 영상의 경우에는 최소 6개의 타임라인이 나와야 합니다. 30분 이상의 영상의 경우에는 최소 10분당 2개 이상의 타임라인이 만들어져야 합니다.
- title 들을 적을 땐, 가능하면 title의 앞 부분에 해당 요약 내용에 어울리는 이모티콘을 하나 배정해줘.
- 타임라인에 타임스탬프는 해당 유튜브 영상의 위치로 클릭 해서 이동할 수 있게 t 파라미터를 추가해서 해당 타임 스탬프의 초 단위 값을 넣어줘.
### 양식
---
tags:
 - {tag_name_1}
 - {tag_name_2}
 - ...
url: {youtube_url}
---
# 핵심주제
<details open>
  <summary>{timeline_summary_title_1}</summary>
  <ul>
    <li>...</li>
    ...
  </ul>
</details>

<details open>
  <summary>{timeline_summary_title_2}</summary>
  <ul>
    <li>...</li>
    ...
  </ul>
</details>
...

# 타임라인
[[{hh:mm:ss}]]({youtube_url}&t={second}) {timestamp_summary_title_1}
- {timestamp_summary_1_content}
- ...
{more}
...
""".replace(
            "{youtube_url}", url
        )
        if script:
            base_script = base_script.replace(
                "{more}",
                """<details open>
  <summary>원문 스크립트 보기</summary>
  {original_script}
</details>""",
            )
        else:
            base_script = base_script.replace("{more}\n", "")
        messages = [
            ("system", base_script),
            ("human", f"### 입력 데이터\n{content}\n### 출력\n"),
        ]
        result = llm.invoke(messages)
        if result.content != "":
            with open("{}.md".format(title), mode="w", encoding="utf-8") as f:
                f.write(result.content)
        else:
            print("무언가 문제가 발생했습니다.")


if __name__ == "__main__":
    fire.Fire(Main)
