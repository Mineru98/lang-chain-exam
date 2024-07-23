import re

import requests
import streamlit as st
from html2text import html2text
from langchain_google_genai import ChatGoogleGenerativeAI
from readabilipy import simple_json_from_html_string


def is_valid_url(url):
    # URL의 기본 형식 검사 정규 표현식
    pattern = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # 도메인 이름
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # IP 주소 (v4)
        r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"  # IP 주소 (v6)
        r"(?::\d+)?"  # 포트
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )  # 경로

    return re.match(pattern, url) is not None


st.set_page_config(
    page_title="메인", layout="centered", initial_sidebar_state="expanded"
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
st.sidebar.text_input(
    "Gemini API Key를 입력하세요.",
    type="password",
    key="gemini_api_key",
    placeholder="API Key 입력",
)
st.sidebar.link_button("Gemini API 가격 확인", "https://ai.google.dev/pricing?hl=ko")


if "clicked" not in st.session_state:
    st.session_state.clicked = False


def click_button():
    st.session_state.clicked = True


def action(url: str, method: str, model: str):
    res = requests.get(url)
    if res.status_code == 200:
        article = simple_json_from_html_string(res.text, use_readability=True)
        content = html2text(article["content"])
        with st.expander("내용 추출 원본", expanded=False):
            st.markdown(content, unsafe_allow_html=True)
        llm = ChatGoogleGenerativeAI(
            model=model, google_api_key=st.session_state.gemini_api_key
        )
        messages = [
            (
                "system",
                "### 요구사항\n1. 한글로 다음 내용들을 요약해줘.\n마크다운 형식으로 출력해줘.\n3."
                + method,
            ),
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
    else:
        return None
    st.session_state.clicked = False


def render(url: str):
    method = st.radio(
        "요약 방식을 선택하세요",
        ["3줄 요약", "심화 요약"],
    )
    model = st.radio(
        "사용할 모델 선택",
        ["gemini-1.5-flash", "gemini-1.5-pro"],
        captions=["1분에 15번 요청 가능, 빨라요!", "1분에 2번 요청 가능, 똑똑해요!"],
    )
    st.button("요약", on_click=click_button)
    if st.session_state.clicked:
        action(url, method, model)


st.title("링크 요약")
if not st.session_state.gemini_api_key:
    st.warning("API KEY를 입력하세요.")
else:
    url = st.text_input("요약 하고자 하는 URL을 입력해주세요")
    if is_valid_url(url):
        render(url)
    elif url != "":
        st.warning("유효한 URL을 입력하세요.")
