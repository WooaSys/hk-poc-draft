import streamlit as st

st.set_page_config(
    page_title="한국타이어 권역",
    page_icon="🚛",
    layout="wide",
)

# --- 사이드바 스타일 ---
st.markdown(
    """
    <style>
    /* 사이드바 타이틀을 최상단으로 */
    [data-testid="stSidebarHeader"] {
        padding-top: 0rem;
    }
    /* 그룹 타이틀(데이터 확인, 최적화 실행, 결과 비교) 스타일 */
    [data-testid="stSidebarNav"] h2,
    [data-testid="stSidebarNav"] [data-testid="stHeaderActionElements"],
    [data-testid="stSidebarNav"] span[data-testid="stNavigationGroupLabel"] {
        font-size: 1.2em !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 페이지 정의 ---
data_pages = [
    st.Page("pages/current_status.py", title="자료 분석"),
]

opt_pages = [
    st.Page("pages/reassignment.py", title="권역 재할당"),
    st.Page("pages/cost_comparison.py", title="배차 비용 비교"),
]

result_pages = [
    st.Page("pages/report.py", title="보고서"),
]

# --- 사이드바 네비게이션 (그룹별) ---
pg = st.navigation(
    {
        "데이터 확인": data_pages,
        "담당권역 재배치": opt_pages,
        "결과": result_pages,
    }
)

pg.run()
