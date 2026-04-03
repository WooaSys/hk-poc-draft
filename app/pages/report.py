"""
결과 보고서 페이지 (report.py)

목적:
    분석 결과를 보고서 형식으로 한 페이지에 정리하고 PDF 다운로드를 제공한다.
    자료 분석 → 자연권역 → 재할당 → 비용 → 결론 순서로 구성.

입력:
    - app/db/ 데이터 파일들

출력:
    - 보고서 화면 + PDF 다운로드
"""

import json
import sys

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
DB_DIR = APP_DIR / "db"
ASSET_DIR = APP_DIR / "assets"

sys.path.insert(0, str(APP_DIR / "01_preproc"))

st.header("분석 보고서")

st.caption("본 보고서는 3.5T 단일 기준 추정값이며, 시나리오 간 상대 비교 목적으로 작성됨.")

# =============================================================
# 공통 데이터 로드
# =============================================================
with open(DB_DIR / "rdc_locations.json", "r", encoding="utf-8") as f:
    rdc_locs = json.load(f)

demand_df = pd.read_csv(DB_DIR / "sigungu_demand.csv")
demand_df = demand_df[~demand_df["sub_region_code"].str.startswith("JEJ")]

sigungu_master = pd.read_csv(DB_DIR / "sigungu_master.csv")

shipto = pd.read_csv(DB_DIR / "shipto_master_corrected.csv")
shipto["Ship-to party"] = shipto["Ship-to party"].astype(str)

# 시군구별 주담당 RDC
current_rdc = (
    shipto.groupby(["sub_region_code", "담당 RDC 명"])["Ship-to party"]
    .nunique().reset_index()
)
current_rdc.columns = ["sub_region_code", "rdc_name", "count"]
idx = current_rdc.groupby("sub_region_code")["count"].idxmax()
current_main = dict(zip(
    current_rdc.loc[idx, "sub_region_code"],
    current_rdc.loc[idx, "rdc_name"],
))
demand_df["current_rdc"] = demand_df["sub_region_code"].map(current_main)

# RDC별 집계
rdc_summary = demand_df.groupby("current_rdc").agg(
    시군구_수=("sub_region_code", "count"),
    총수요_3_5t=("demand_3_5t", "sum"),
    일평균_3_5t=("daily_demand_3_5t", "sum"),
).reset_index()
rdc_summary.columns = ["RDC", "시군구 수", "총수요(3.5T)", "일평균(3.5T)"]
rdc_summary["비중(%)"] = (rdc_summary["일평균(3.5T)"] / rdc_summary["일평균(3.5T)"].sum() * 100).round(1)
rdc_summary = rdc_summary.sort_values("일평균(3.5T)", ascending=False)
rdc_summary["총수요(3.5T)"] = rdc_summary["총수요(3.5T)"].round(1)
rdc_summary["일평균(3.5T)"] = rdc_summary["일평균(3.5T)"].round(1)

# RDC 색상
rdc_names_list = ["평택RDC", "칠곡RDC", "계룡RDC", "제천RDC", "중부RDC"]
rdc_colors_list = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#19D3F3"]
rdc_color_map = dict(zip(rdc_names_list, rdc_colors_list))

delivery_counts = [1288, 982, 698, 281, 3]
sigungu_counts = [88, 65, 65, 25, 3]

# =============================================================
# 1. 현황 분석
# =============================================================
st.subheader("1. 현황 분석")

# --- 1-1. RDC 개요 ---
st.markdown("#### 1-1. RDC 개요")

rdc_display = pd.DataFrame(rdc_locs)
rdc_display = rdc_display[rdc_display["name"] != "제주RDC"]
rdc_display = rdc_display[["plant_code", "name", "address"]]
rdc_display.columns = ["Plant코드", "물류센터", "주소"]
st.dataframe(rdc_display, use_container_width=True, hide_index=True)

st.caption("※ 제주RDC는 도로 경로 부재로 본 분석에서 제외")

# --- 1-2. RDC별 수요 현황 ---
st.markdown("#### 1-2. RDC별 수요 현황")

col_map, col_pie = st.columns([3, 2])

with col_map:
    st.image(str(ASSET_DIR / "asis-권역map.png"), use_container_width=True)

with col_pie:
    fig_pie = go.Figure(go.Pie(
        labels=rdc_names_list,
        values=delivery_counts,
        marker=dict(colors=rdc_colors_list),
        textinfo="label+percent",
        hole=0,
    ))
    fig_pie.update_layout(height=620, margin=dict(t=30, b=30, l=10, r=10))
    st.plotly_chart(fig_pie, use_container_width=True)

st.dataframe(rdc_summary, use_container_width=True, hide_index=True)

st.caption("※ 수요는 3.5T 트럭 환산 기준으로 산출. 산출 근거 및 방법은 1-5. 수요 측정 기준 참고.")

st.markdown(
    "> **중부RDC 참고사항**\n>\n"
    "> - 보유한 데이터 상 총 배송지 **3건**에 불과함.\n"
    "> - 배송지: 대전 대덕구(1), 경기 광명시(1), 강원 춘천시(1)\n"
    "> - 주소가 금산공장과 동일한 것으로 확인되어 주소 검증 필요\n"
    "> - 운영 규모와 향후 활용 방향이 불확실하여 **권역 재할당 분석에서는 기본적으로 제외** (옵션으로 포함 가능)"
)

# --- 1-3. RDC별 배송지/시군구 ---
st.markdown("#### 1-3. RDC별 담당 현황")

fig_bars = go.Figure()
fig_bars.add_trace(go.Bar(
    name="배송지 수 (Ship-to party)",
    x=rdc_names_list, y=delivery_counts,
    text=delivery_counts, textposition="outside",
    marker_color="#636EFA",
))
fig_bars.add_trace(go.Bar(
    name="시군구 수",
    x=rdc_names_list, y=sigungu_counts,
    text=sigungu_counts, textposition="outside",
    marker_color="#EF553B",
))
fig_bars.update_layout(barmode="group", yaxis_title="수", height=400, margin=dict(t=30))
st.plotly_chart(fig_bars, use_container_width=True)

# --- 1-4. 데이터 특이사항 ---
st.markdown("#### 1-4. 데이터 특이사항")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**RDC간 중복 권역 (12개 지역)**")
    st.markdown(
        "같은 Region Code 안에서 복수 RDC가 배송하는 경우. "
        "개별 배송지는 1:1이지만, 권역 레벨에서 복수 RDC 혼재. "
        "대부분 주 담당 RDC가 있고 그 외 RDC는 1~3건 수준의 소량이므로, "
        "재할당 분석에서는 주 담당 RDC 기준으로 보정하여 사용."
    )

with col_right:
    st.markdown("**Region Code 데이터 이상 (18건)**")
    st.markdown(
        "배송지의 시군구가 Region Code의 주 지역과 다른 광역도시에 해당.\n"
        "전체 3,320개 중 22건(0.7%) — 보정 데이터 사용."
    )

# --- 1-5. 적재 기준 ---
st.markdown("#### 1-5. 수요 측정 기준")

st.markdown(
    "##### 배경: 배송지별 물량을 어떻게 측정할 것인가?\n\n"
    "권역 재배정을 수행하기 위해서는 각 배송지의 물량을 정량적으로 산정할 필요가 있음.\n\n"
    "배송지(시군구)별 수요량을 정량화하기 위해 "
    "\"이 지역에 하루에 타이어가 얼마나 필요한가\"를 트럭 단위로 환산하여 권역 재할당에 사용함.\n\n"
    "타이어의 정확한 **부피(CBM) 데이터가 없음.**"
)

st.markdown(
    "##### 해결: 배송 실적에서 적재율 역산\n\n"
    "배송 실적 데이터의 `Measurement by Material and Q'ty` 컬럼은 "
    "**해당 배송에서 타이어가 트럭 적재 공간의 몇 %를 차지했는지**를 나타냄.\n\n"
    "이 값을 수량으로 나누면 **타이어 1본당 적재율(%)**을 산출할 수 있음:"
)

st.code("1본당 적재율(%) = Measurement ÷ 수량", language=None)

st.markdown(
    "분석 결과, 같은 사이즈 × 같은 트럭 조합에서 이 값이 **거의 일정** (변동계수 2.3%). "
    "타이어 사이즈와 트럭이 정해지면 1본이 차지하는 비율은 고정값.\n\n"
    "이를 기반으로 **288개 타이어 사이즈 × 5개 트럭 톤수**에 대한 적재율 기준표를 구축함."
)

st.markdown(
    "##### 적재율 예시 (3.5T 트럭 기준)\n\n"
    "| 타이어 | 1본당 적재율 | 만적 수량 |\n"
    "|---|---:|---:|\n"
    "| 155/70R13 (소형) | 0.267% | 375본 |\n"
    "| 225/45R18 (중형) | 0.400% | 250본 |\n"
    "| 265/60R18 (대형) | 0.875% | 114본 |\n\n"
    "타이어가 클수록 1본당 적재율이 높아 트럭에 적게 적재됨."
)

st.markdown(
    "##### 수요 환산 방법\n\n"
    "적재율을 이용하여 배송지별 물량을 **\"3.5T 트럭 몇 대분\"**으로 환산:"
)

st.code(
    "예) 어떤 배송지의 하루 배송:\n"
    "  225/45R18  80본 × 0.400% = 32.0%\n"
    "  245/45R18  60본 × 0.600% = 36.0%\n"
    "  합계: 68.0% → 3.5T 트럭 0.68대분",
    language=None,
)

st.markdown(
    "이 값이 본 분석에서 사용하는 **`daily_demand_3_5t`** (일평균 3.5T 환산 수요)임."
)

st.markdown(
    "##### 3.5T를 기준으로 선택한 이유\n\n"
    "| 트럭 | 사용 비중 | 비고 |\n"
    "|---|---:|---|\n"
    "| **3.5T** | **54.2%** | 모든 RDC 공통 주력, 기준표 288개 사이즈 완비 |\n"
    "| 5T | 31.7% | 2순위, 참고용으로 병행 산출 |\n"
    "| 1T | 12.5% | 소량 배송용 |\n"
    "| 8T/11T | 1.6% | 대형 타이어 전용, 일부 사이즈만 적재 가능 |\n\n"
    "3.5T는 가장 높은 사용 비중(54.2%)을 차지하며, 모든 RDC에서 공통으로 운용됨. "
    "288개 사이즈 전부 적재율이 확보되어 있어 **비교 기준으로 가장 일관적**."
)

st.markdown(
    "##### 한계\n\n"
    "- 대형 타이어(1100-20 등) 9개 사이즈는 8T/11T 전용으로 3.5T 환산 불가 → 전체의 0.02%로 영향 미미\n"
    "- 실제 운영에서는 1T, 5T 등 혼합 톤수 사용 → 3.5T 단일 기준은 추정값\n"
    "- **시나리오 간 상대 비교에는 동일 기준 적용으로 유효**"
)

# 적재율 분포 차트
loading_df = pd.read_csv(DB_DIR / "타이어사이즈별_적재기준표.csv")
col_35 = "3.5T_1본당%"
if col_35 in loading_df.columns:
    data_35 = loading_df[col_35].dropna()
    fig_hist = go.Figure(go.Histogram(
        x=data_35, nbinsx=30, marker_color="#45B7D1",
    ))
    fig_hist.update_layout(
        xaxis_title="1본당 적재율 (%)", yaxis_title="사이즈 수",
        height=300, margin=dict(t=10),
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    st.caption(f"3.5T 기준 1본당 적재율 분포 — 평균: {data_35.mean():.3f}% / 중앙값: {data_35.median():.3f}% / 288개 사이즈")

# =============================================================
# 2. 수요 분포 분석
# =============================================================
st.divider()
st.subheader("2. 수요 분포 분석")

st.markdown("#### 2-1. 시군구별 수요 분포 (3.5T 일평균)")

# 상위/하위 수요 시군구
demand_ranked = demand_df.sort_values("daily_demand_3_5t", ascending=False)
top10 = demand_ranked.head(10)[["sub_region_code", "sigungu_name", "current_rdc", "daily_demand_3_5t"]].copy()
top10.columns = ["코드", "시군구", "현재 RDC", "일평균(3.5T)"]

st.markdown("**수요 상위 10개 시군구**")
st.dataframe(top10, use_container_width=True, hide_index=True)

# 수요 분포 히스토그램
fig_demand_hist = go.Figure(go.Histogram(
    x=demand_df["daily_demand_3_5t"], nbinsx=30, marker_color="#636EFA",
))
fig_demand_hist.update_layout(
    xaxis_title="일평균 수요 (3.5T 대수)", yaxis_title="시군구 수",
    height=300, margin=dict(t=10),
)
st.plotly_chart(fig_demand_hist, use_container_width=True)
st.caption(f"247개 시군구 — 평균: {demand_df['daily_demand_3_5t'].mean():.2f} / 중앙값: {demand_df['daily_demand_3_5t'].median():.2f} / 최대: {demand_df['daily_demand_3_5t'].max():.1f}")

# =============================================================
# 3. 자연권역 분석
# =============================================================
st.divider()
st.subheader("3. 자연권역 분석")

st.markdown(
    "자연권역 = 각 시군구를 소요시간 기준 **가장 가까운 RDC에 배정**했을 때의 기준 권역. "
    "capacity, 운영 정책 등을 제거한 reference layer. "
    "RDC↔시군구 간 소요시간은 **OSRM(실제 도로 네트워크 기반)**으로 산출."
)

# 자연권역 생성
from natural_territory import generate_natural_territory
territory_df, load_summary = generate_natural_territory(include_jungbu=False)

# Natural Load vs Current Load
st.markdown("#### 3-1. Natural Load vs Current Load")

fig_load = go.Figure()
fig_load.add_trace(go.Bar(
    name="Current Load (현재)", x=load_summary["rdc_name"],
    y=load_summary["current_load_3_5t"].round(1),
    marker_color="#636EFA",
    text=load_summary["current_load_3_5t"].round(1), textposition="outside",
))
fig_load.add_trace(go.Bar(
    name="Natural Load (자연권역)", x=load_summary["rdc_name"],
    y=load_summary["natural_load_3_5t"].round(1),
    marker_color="#FF6B6B",
    text=load_summary["natural_load_3_5t"].round(1), textposition="outside",
))
fig_load.update_layout(barmode="group", yaxis_title="수요 (3.5T 일평균)", height=400, margin=dict(t=30))
st.plotly_chart(fig_load, use_container_width=True)

# 비교 테이블
display_load = load_summary[[
    "rdc_name", "natural_sigungu_count", "current_sigungu_count",
    "natural_load_3_5t", "current_load_3_5t", "gap_3_5t",
]].copy()
display_load.columns = ["RDC", "자연 시군구", "현재 시군구", "Natural Load", "Current Load", "Gap"]
st.dataframe(display_load, use_container_width=True, hide_index=True)

# 핵심 결론
st.markdown("#### 3-2. 핵심 결론")

gap_positive = territory_df[territory_df["time_gap"] > 0]

st.markdown(
    f"- 전체 247개 시군구 중 **{len(territory_df) - len(gap_positive)}개(94%)가 이미 가장 가까운 RDC에 배정**\n"
    f"- 더 가까운 RDC가 있는 시군구: **{len(gap_positive)}개(6%)**, gap > 30분은 1개뿐\n"
    "- **현재 권역 구조는 공간적으로 크게 왜곡되어 있지 않음**\n"
    "- 문제의 본질은 권역 왜곡이 아니라 **수요 자체의 공간 편중** (수도권/경기권 집중)\n"
    "- 단순 재할당만으로 큰 개선이 안 나올 가능성 → **capacity 제약 기반 시나리오 분석으로 전환**"
)

# =============================================================
# (추후 섹션 추가 위치)
# =============================================================
st.divider()
st.info("📋 권역 재할당 결과, 배차 비용 비교, 결론 섹션은 추후 추가 예정.")

# =============================================================
# PDF 다운로드
# =============================================================
st.divider()

def generate_pdf():
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_font("Korean", "", "/System/Library/Fonts/AppleSDGothicNeo.ttc")
    pdf.add_font("Korean", "B", "/System/Library/Fonts/AppleSDGothicNeo.ttc")
    pdf.set_auto_page_break(auto=True, margin=15)

    def heading(text, size=18):
        pdf.set_font("Korean", "B", size)
        pdf.cell(0, 12, text=text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    def subheading(text, size=14):
        pdf.set_font("Korean", "B", size)
        pdf.cell(0, 10, text=text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    def body(text):
        pdf.set_font("Korean", "", 10)
        pdf.multi_cell(0, 7, text=text)
        pdf.ln(2)

    def table(headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [180 // len(headers)] * len(headers)
        pdf.set_font("Korean", "B", 9)
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 8, text=h, border=1, align="C")
        pdf.ln()
        pdf.set_font("Korean", "", 9)
        for row in rows:
            for w, val in zip(col_widths, row):
                pdf.cell(w, 8, text=str(val), border=1, align="C")
            pdf.ln()
        pdf.ln(3)

    # --- 표지 ---
    pdf.add_page()
    pdf.set_font("Korean", "B", 24)
    pdf.cell(0, 60, text="", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 15, text="한국타이어 RDC 권역 분석 보고서", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Korean", "", 12)
    pdf.cell(0, 10, text="3.5T 기준 추정값 | 시나리오 간 상대 비교 목적", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 8, text="데이터 기준: 2025년 2월, 11월 배송 실적", new_x="LMARGIN", new_y="NEXT", align="C")

    # --- 1. 현황 분석 ---
    pdf.add_page()
    heading("1. 현황 분석")

    subheading("1-1. RDC 개요")
    for rdc in rdc_locs:
        if rdc["name"] == "제주RDC":
            continue
        body(f"  {rdc['name']} ({rdc['plant_code']}): {rdc['address']}")

    subheading("1-2. RDC별 수요 현황 (3.5T 기준, 일평균)")
    table(
        ["RDC", "시군구 수", "총수요", "일평균", "비중(%)"],
        [[r["RDC"], int(r["시군구 수"]), r["총수요(3.5T)"], r["일평균(3.5T)"], r["비중(%)"]] for _, r in rdc_summary.iterrows()],
        [35, 25, 30, 30, 25],
    )

    body(
        "[중부RDC] 2025년 11월 운영 시작, 총 배송 3건의 초기 단계.\n"
        "운영 규모와 향후 활용 방향이 불확실하여 권역 재할당에서는 기본적으로 제외."
    )

    subheading("1-3. 데이터 특이사항")
    body(
        "- RDC간 중복 권역 12개 지역: 같은 Region Code에서 복수 RDC가 배송\n"
        "  대부분 주 담당 RDC가 있고 그 외는 1~3건 소량, 재할당에서는 주 담당 기준으로 보정\n"
        "- Region Code 데이터 이상 18건: 보정 데이터(shipto_master_corrected) 사용\n"
        "- 개별 배송지(Ship-to party)는 1:1로 RDC에 배정"
    )

    subheading("1-4. 수요 측정 기준")
    body(
        "- CBM 데이터 미보유 -> 적재율 역산 기반 3.5T 환산\n"
        "- 배송 실적의 Measurement / Q'ty = 1본당 적재율(%)\n"
        "- 288개 사이즈 x 5개 트럭 조합별 고정값 (CV 2.3%)\n"
        "- 3.5T 선택: 전체 자체 차량의 54%, 모든 RDC 공통 주력"
    )

    # --- 2. 수요 분포 ---
    pdf.add_page()
    heading("2. 수요 분포 분석")

    subheading("수요 상위 10개 시군구 (3.5T 일평균)")
    top_rows = []
    for _, r in top10.iterrows():
        top_rows.append([r["시군구"], r["현재 RDC"], f"{r['일평균(3.5T)']:.1f}"])
    table(["시군구", "현재 RDC", "일평균(3.5T)"], top_rows, [70, 40, 35])

    body(
        f"247개 시군구 평균: {demand_df['daily_demand_3_5t'].mean():.2f}대/일\n"
        f"중앙값: {demand_df['daily_demand_3_5t'].median():.2f}대/일\n"
        f"최대: {demand_df['daily_demand_3_5t'].max():.1f}대/일"
    )

    # --- 3. 자연권역 ---
    pdf.add_page()
    heading("3. 자연권역 분석")

    body("자연권역 = 각 시군구를 소요시간 기준 가장 가까운 RDC에 배정한 기준 권역")

    subheading("Natural Load vs Current Load")
    load_rows = []
    for _, r in display_load.iterrows():
        load_rows.append([r["RDC"], int(r["자연 시군구"]), int(r["현재 시군구"]),
                         f"{r['Natural Load']:.1f}", f"{r['Current Load']:.1f}", f"{r['Gap']:.1f}"])
    table(["RDC", "자연 시군구", "현재 시군구", "Natural", "Current", "Gap"], load_rows, [30, 25, 25, 25, 25, 25])

    subheading("핵심 결론")
    body(
        f"- 247개 중 {len(territory_df) - len(gap_positive)}개(94%)가 이미 최근접 RDC에 배정\n"
        f"- 조정 대상: {len(gap_positive)}개(6%), gap > 30분은 1개뿐\n"
        "- 현재 권역 구조는 공간적으로 크게 왜곡되어 있지 않음\n"
        "- 문제의 본질: 수요 자체의 공간 편중 (수도권/경기권 집중)\n"
        "- -> capacity 제약 기반 시나리오 분석으로 전환"
    )

    return bytes(pdf.output())

if st.button("PDF 다운로드", type="secondary"):
    with st.spinner("PDF 생성 중..."):
        pdf_bytes = generate_pdf()
    st.download_button(
        label="📥 보고서 PDF 저장",
        data=pdf_bytes,
        file_name="hk_rdc_report.pdf",
        mime="application/pdf",
    )
