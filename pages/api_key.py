import streamlit as st

st.set_page_config(
    page_title="API KEY 발급 방법", layout="centered", initial_sidebar_state="expanded"
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

st.header("무료 사용 API KEY 발급 by Google Gemini")
st.video(data="https://youtu.be/6aj5a7qGcb4")

st.markdown(
    """### 영상 요약
```
- 영상은 Google Gemini API 키를 얻는 방법을 안내함.
- 먼저 ai.google.dev 웹페이지에 접속함.
- 'Google AI for Developers' 페이지에서 'Get API Key in Google AI Studio' 버튼을 클릭함.
- 이용 약관에 동의함.
- 'Get API Key'를 클릭 후 'Create API key in new project' 버튼을 클릭하여 새로운 프로젝트를 생성함.
- API 키가 생성되면 복사하여 Gemini를 애플리케이션에 통합하는 데 사용 가능함.
```"""
)
