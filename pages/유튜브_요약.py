import locale
import re

import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi

# locale 설정
locale.setlocale(locale.LC_ALL, "")


def format_date(date_obj):
    formatted_date = date_obj.strftime("%Y년 %m월 %d일")

    return formatted_date


# 숫자를 통화 형식으로 변환하는 함수
def format_currency(value: int, currency_symbol=""):
    return locale.currency(value, symbol=currency_symbol, grouping=True)


def format_seconds(seconds: int):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    result = []
    if hours > 0:
        result.append(f"{hours}시간")
    if minutes > 0:
        result.append(f"{minutes}분")
    if secs > 0 or len(result) == 0:  # 초는 항상 표시, 0초도 필요하다면 표시
        result.append(f"{secs}초")

    return " ".join(result)


st.set_page_config(
    page_title="유튜브 영상 요약", layout="centered", initial_sidebar_state="expanded"
)

st.sidebar.page_link(
    "pages/main.py", label="메인", icon="🏠", use_container_width=False
)
st.sidebar.page_link(
    "pages/api_key.py",
    label="Gemini API KEY 발급 방법",
    icon="🔑",
    use_container_width=False,
)
st.sidebar.page_link(
    "pages/유튜브_요약.py", label="유튜브 요약", icon="🎬", use_container_width=False
)
st.sidebar.page_link(
    "pages/링크_요약.py", label="링크 요약", icon="🔗", use_container_width=False
)
st.sidebar.page_link(
    "pages/깃허브_요약.py",
    label="깃허브 레포 요약(준비중)",
    icon="🖥️",
    use_container_width=False,
)
st.sidebar.page_link(
    "pages/논문_요약.py",
    label="논문 요약(준비중)",
    icon="📖",
    use_container_width=False,
)
st.sidebar.divider()

if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""

st.sidebar.text_input(
    "Gemini API Key를 입력하세요.",
    type="password",
    key="gemini_api_key",
    placeholder="API Key 입력",
)
st.sidebar.link_button("Gemini API 가격 확인", "https://ai.google.dev/pricing?hl=ko")


def clean_title(title: str):
    # 특수문자 제거 (알파벳, 숫자, 공백만 남김)
    title = re.sub(r"[^\w\s]", "", title)
    # 공백을 밑줄로 대체
    title = title.replace(" ", "_")
    return title


def get_youtube_info(url: str):
    try:
        yt = YouTube(url)
        view_count = format_currency(yt.views)
        duration = format_seconds(yt.length)
        publish_date = format_date(yt.publish_date)
        return (yt.author, yt.title, publish_date, view_count, duration, yt.channel_url)
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return (None, None, None, None, None)


if "clicked" not in st.session_state:
    st.session_state.clicked = False


def click_button():
    st.session_state.clicked = True


def action(url, content, method: str, model: str, prompt: str = None):
    llm = ChatGoogleGenerativeAI(
        model=model, google_api_key=st.session_state.gemini_api_key
    )
    base_script = ""
    if method == "타임스탬프 생성":
        base_script = """### 명령어
    내가 만든 스타일대로 markdown 양식으로 변환해줘.
    ### 요구사항
    - timestamp_summary는 적절하게 타임스탬프를 큰 내용 단위로 나눠줘.
    - timestamp_summary는 정적인 분위기가 아닌, 얘기를 하듯이 작성해줘.
    - timestamp_summary는 반드시 한글로 작성해줘.
    - 타임라인은 5분 미만의 영상의 경우에는 최소 3개의 타임라인이 나와야 하고 10분 미만의 영상의 경우에는 최소 6개의 타임라인이 나와야 합니다. 30분 이상의 영상의 경우에는 최소 10분당 2개 이상의 타임라인이 만들어져야 합니다.
    - title 들을 적을 땐, 가능하면 title의 앞 부분에 해당 요약 내용에 어울리는 이모티콘을 하나 배정해줘.
    - 타임라인에 타임스탬프는 해당 유튜브 영상의 위치로 클릭 해서 이동할 수 있게 t 파라미터를 추가해서 해당 타임 스탬프의 초 단위 값을 넣어줘.
    ### 양식
    ```
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
    ...
    ```
    """.replace(
            "{youtube_url}", url
        )
    elif method == "3줄 요약":
        base_script = """### 명령어
markdown 양식으로 변환해줘.
### 요구사항
- 3줄로 요약해줘.
- 반드시 한글로 요약해줘."""
    elif method == "심화 요약":
        base_script = """### 명령어
markdown 양식으로 변환해줘.
### 요구사항
- 매우 자세히 요약해줘.
- 반드시 한글로 요약해줘."""
    elif method == "커스터마이징":
        base_script = (
            prompt + "\n반드시 한글로 대답해줘.\n반드시 마크다운 형식으로 대답해줘."
        )
    messages = [
        ("system", base_script),
        ("human", f"### 입력 데이터\n{content}\n### 출력\n"),
    ]
    try:
        with st.spinner("요약 중..."):
            result = llm.invoke(messages)
            st.markdown(result.content, unsafe_allow_html=True)
    except:
        st.error(
            "요약에 실패했습니다. 요청 횟수 제한이 걸렸거나, API KEY 입력이 잘못 되었습니다."
        )


def render(video_id: str):
    url = f"https://youtu.be/{video_id}"
    with st.spinner("링크 분석 중"):
        author, title, publish_date, view_count, duration, channel_url = (
            get_youtube_info(url)
        )
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages=["ko"])
        content = [i for i in srt if i["text"] != "[음악]"]
        st.subheader(title)
        st.video(url)
        with st.expander("영상 정보", expanded=False):
            st.markdown(
                f""" - #### 채널명 : [{author}]({channel_url})
 - #### 조회수 : {view_count} 회
 - #### 영상 길이 : {duration}
 - #### 게시 날짜 : {publish_date}
"""
            )
        model = st.radio(
            "사용할 모델 선택",
            ["gemini-1.5-flash", "gemini-1.5-pro"],
            captions=[
                "1분에 15번 요청 가능, 빨라요!",
                "1분에 2번 요청 가능, 똑똑해요!",
            ],
        )
        method = st.radio(
            "**영상 분석 방식을 선택하세요**",
            ["3줄 요약", "심화 요약", "타임스탬프 생성", "커스터마이징"],
        )
        if method == "커스터마이징":
            prompt = st.text_area("프롬프트를 직접 입력해주세요.")
            st.button("요약", on_click=click_button)
            if st.session_state.clicked:
                action(url, content, method, model, prompt)
        else:
            st.button("요약", on_click=click_button)
            if st.session_state.clicked:
                action(url, content, method, model)


st.title("YouTube 영상 🎬 요약")
if not st.session_state.gemini_api_key:
    st.warning("API KEY를 입력하세요.")
else:
    youtube_url = st.text_input("YouTube 영상 URL을 입력해주세요")
    if youtube_url.startswith("https://youtu.be/"):
        video_id = youtube_url.split("/")[-1]
        render(video_id)
    elif youtube_url.startswith("https://www.youtube.com/watch?"):
        video_id = youtube_url.split("v=")[-1].split("&")[0]
        render(video_id)
    elif youtube_url != "":
        st.warning("유효한 YouTube URL을 입력하세요.")
