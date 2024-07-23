import streamlit as st


def main():
    st.set_page_config(
        page_title="AI 에이전트", layout="centered", initial_sidebar_state="expanded"
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
        "pages/유튜브_요약.py",
        label="유튜브 요약",
        icon="🎬",
        use_container_width=False,
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

    st.title("AI 에이전트 도구 모음")
    st.write("이곳에서 AI를 활용하여 생산성을 높여보세요!")


if __name__ == "__main__":
    main()
