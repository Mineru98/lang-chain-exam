import streamlit as st

st.set_page_config(
    page_title="논문 요약", layout="centered", initial_sidebar_state="expanded"
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


def render(video_id: str):
    url = f"https://youtu.be/{video_id}"
    st.video(url)
    with st.expander("영상 정보", expanded=False):
        st.write("test")
    method = st.radio(
        "영상 분석 방식을 선택하세요",
        ["3줄 요약", "심화 요약", "타임스탬프 생성", "커스터마이징"],
    )
    print(method)


st.title("📖 논문 요약")
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
