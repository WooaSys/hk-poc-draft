"""
backup.py - 이전 작업 백업 페이지
이전 버전의 탭/화면을 보존하기 위한 용도.
"""
import json
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import folium
from streamlit.components.v1 import html as st_html
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = APP_DIR.parent
RAW_DATA_DIR = PROJECT_DIR / "raw_data"
DB_DIR = APP_DIR / "db"

CITY_CODE_MAP = {
    "11": "서울특별시", "21": "부산광역시", "22": "대구광역시", "23": "인천광역시",
    "24": "광주광역시", "25": "대전광역시", "26": "울산광역시", "29": "세종특별자치시",
    "31": "경기도", "32": "강원도", "33": "충청북도", "34": "충청남도",
    "35": "전라북도", "36": "전라남도", "37": "경상북도", "38": "경상남도", "39": "제주특별자치도",
}


def load_sigungu_gdf():
    gdf = gpd.read_file(RAW_DATA_DIR / "map" / "BND_SIGUNGU_PG.shp")
    gdf = gdf.to_crs(epsg=4326)
    gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.001, preserve_topology=True)
    gdf["광역도시"] = gdf["SIGUNGU_CD"].str[:2].map(CITY_CODE_MAP)
    return gdf


st.header("Backup")

tab_status_old = st.tabs(["RDC 현황_v0.0.1"])[0]

with tab_status_old:
    # --- RDC별 담당 현황 (하드코딩) ---
    rdc_names = ["평택RDC", "칠곡RDC", "계룡RDC", "제천RDC", "제주RDC", "중부RDC"]
    delivery_counts = [1288, 982, 698, 281, 68, 3]  # Ship-to party 수
    sigungu_counts = [88, 65, 65, 25, 2, 3]          # 시군구 수
    colors = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"]

    # 배송지 마스터 로드
    master_df = pd.read_csv(DB_DIR / "배송지_마스터.csv")
    master_df = master_df.dropna(subset=["Region Code"])

    # --- 지도: RDC + 배송지 분포 ---
    st.subheader("RDC 및 권역 분포 지도")

    # RDC 위치
    rdc_path = DB_DIR / "rdc_locations.json"
    with open(rdc_path, "r", encoding="utf-8") as f:
        rdc_data = json.load(f)

    # 배송지 좌표
    region_df = pd.read_csv(DB_DIR / "배송지코드_지역매핑_완성.csv")

    # 배송지별 주 담당 RDC (최다 건수 기준)
    main_rdc = (
        master_df.groupby("Region Code")["담당 RDC 명"]
        .agg(lambda x: x.value_counts().index[0])
        .reset_index()
    )
    main_rdc.columns = ["Region Code", "주담당RDC"]

    # 좌표 병합
    region_with_rdc = region_df.merge(
        main_rdc, left_on="region_code", right_on="Region Code", how="inner"
    )

    rdc_color_map = dict(zip(rdc_names, colors))
    OVERLAP_COLOR = "#FFD700"

    # 시군구 shapefile 로드 (광역도시 포함)
    gdf = load_sigungu_gdf()

    # 시군구별 RDC 수 + 주담당 RDC (광역도시+시군구 기준)
    sigungu_rdc_count = master_df.groupby(["광역도시", "시군구"])["담당 RDC 명"].nunique().reset_index()
    sigungu_rdc_count.columns = ["광역도시_m", "시군구_m", "RDC수"]
    sigungu_rdc_main = (
        master_df.groupby(["광역도시", "시군구"])["담당 RDC 명"]
        .agg(lambda x: x.value_counts().index[0])
        .reset_index()
    )
    sigungu_rdc_main.columns = ["광역도시_m", "시군구_m", "담당RDC"]
    sigungu_rdc_all = (
        master_df.groupby(["광역도시", "시군구"])["담당 RDC 명"]
        .agg(lambda x: ", ".join(sorted(x.unique())))
        .reset_index()
    )
    sigungu_rdc_all.columns = ["광역도시_m", "시군구_m", "담당RDC_전체"]

    gdf = gdf.merge(sigungu_rdc_count, left_on=["광역도시", "SIGUNGU_NM"], right_on=["광역도시_m", "시군구_m"], how="left")
    gdf = gdf.merge(sigungu_rdc_main, left_on=["광역도시", "SIGUNGU_NM"], right_on=["광역도시_m", "시군구_m"], how="left", suffixes=("", "_main"))
    gdf = gdf.merge(sigungu_rdc_all, left_on=["광역도시", "SIGUNGU_NM"], right_on=["광역도시_m", "시군구_m"], how="left", suffixes=("", "_all"))

    # 색상 매핑
    gdf["fill_color"] = gdf.apply(
        lambda r: OVERLAP_COLOR if r["RDC수"] > 1
        else rdc_color_map.get(r["담당RDC"], "#DDDDDD") if pd.notna(r["담당RDC"])
        else "#DDDDDD",
        axis=1,
    )

    # Folium 지도
    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="CartoDB positron")

    assigned = gdf[gdf["RDC수"] > 0].copy()
    folium.GeoJson(
        assigned,
        style_function=lambda feature: {
            "fillColor": feature["properties"]["fill_color"],
            "color": "#333333",
            "weight": 0.8,
            "fillOpacity": 0.6,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["광역도시", "SIGUNGU_NM", "담당RDC_전체", "RDC수"],
            aliases=["광역도시:", "시군구:", "담당 RDC:", "RDC 수:"],
            style="font-size:13px;",
        ),
        name="RDC 담당 구역",
    ).add_to(m)

    # RDC 위치 마커
    for rdc in rdc_data:
        folium.Marker(
            location=[rdc["lat"], rdc["lon"]],
            popup=f"<b>{rdc['name']}</b><br>{rdc['address']}",
            tooltip=rdc["name"],
            icon=folium.Icon(color="black", icon="star", prefix="fa"),
        ).add_to(m)

    folium.LayerControl().add_to(m)

    # 범례를 포함한 전체 HTML 생성
    legend_html = """
    <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
         background: white; padding: 12px 16px; border-radius: 8px;
         box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-size: 13px; line-height: 1.6;">
    <b>RDC 담당 구역</b><br>
    """
    for name, color in rdc_color_map.items():
        legend_html += f'<span style="background:{color};width:14px;height:14px;display:inline-block;margin-right:6px;border-radius:2px;vertical-align:middle;"></span>{name}<br>'
    legend_html += f'<span style="background:{OVERLAP_COLOR};width:14px;height:14px;display:inline-block;margin-right:6px;border-radius:2px;vertical-align:middle;"></span>복수 RDC 겹침<br>'
    legend_html += "</div>"

    # 지도(좌) + 원형그래프(우) 배치
    col_map, col_pie = st.columns([3, 2])

    with col_map:
        full_html = m.get_root().render()
        full_html = full_html.replace("</body>", legend_html + "</body>")
        st_html(full_html, height=620)

    with col_pie:
        fig3 = go.Figure(go.Pie(
            labels=rdc_names, values=delivery_counts,
            marker=dict(colors=colors),
            textinfo="label+percent",
            hole=0,
        ))
        fig3.update_layout(height=620, margin=dict(t=30, b=30, l=10, r=10))
        st.plotly_chart(fig3, use_container_width=True, key="pie_backup")

    # --- 중복 권역 ---
    with st.expander("RDC간 중복 권역 (12개 지역)"):
        st.markdown("※ 같은 Region Code 안에서 **복수 RDC가 배송**하는 경우 (예: 춘천시를 제천RDC + 중부RDC가 담당)")
        overlap_data = [
            {"지역코드": "CAA", "지역": "강원도 춘천시", "배송지 수": 17, "배정 현황": "제천RDC(16) / 중부RDC(1)"},
            {"지역코드": "CCA", "지역": "강원도 강릉시", "배송지 수": 29, "배정 현황": "제천RDC(28) / 평택RDC(1)"},
            {"지역코드": "CIA", "지역": "강원도 원주시", "배송지 수": 31, "배정 현황": "제천RDC(30) / 평택RDC(1)"},
            {"지역코드": "DOA", "지역": "충청남도 아산시", "배송지 수": 34, "배정 현황": "평택RDC(33) / 계룡RDC(1)"},
            {"지역코드": "DSA", "지역": "충청남도 당진시", "배송지 수": 22, "배정 현황": "평택RDC(19) / 칠곡RDC(2) / 계룡RDC(1)"},
            {"지역코드": "EAA", "지역": "충청남도 홍성군", "배송지 수": 14, "배정 현황": "평택RDC(13) / 계룡RDC(1)"},
            {"지역코드": "EJA", "지역": "충청북도 진천군", "배송지 수": 12, "배정 현황": "평택RDC(11) / 계룡RDC(1)"},
            {"지역코드": "ELA", "지역": "충청북도 음성군", "배송지 수": 19, "배정 현황": "평택RDC(14) / 계룡RDC(3) / 제천RDC(2)"},
            {"지역코드": "FSA", "지역": "경기도 광명시", "배송지 수": 13, "배정 현황": "평택RDC(12) / 중부RDC(1)"},
            {"지역코드": "MNA", "지역": "경상남도 진주시", "배송지 수": 54, "배정 현황": "칠곡RDC(53) / 계룡RDC(1)"},
            {"지역코드": "PBA", "지역": "경상북도 봉화군", "배송지 수": 5, "배정 현황": "제천RDC(4) / 칠곡RDC(1)"},
            {"지역코드": "PCA", "지역": "경상북도 안동시", "배송지 수": 8, "배정 현황": "칠곡RDC(7) / 제천RDC(1)"},
        ]
        st.dataframe(
            pd.DataFrame(overlap_data),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("※ 괄호 안 숫자는 해당 RDC에서 담당하는 배송지(Ship-to party) 수")
        st.info("개별 배송지(Ship-to party)는 1:1로 RDC에 배정되어 있으나, 권역(Region Code) 레벨에서 복수 RDC가 섞여 있음")

    with st.expander("Region Code 데이터 이상 (18건)"):
        st.markdown("※ 배송지의 시군구 정보가 Region Code의 주 지역과 **다른 광역도시**에 해당하는 경우 (예: 대덕구 코드에 광산구 배송지)")
        st.markdown(
            "다른 광역도시에 걸친 Region Code **15개**에서 이탈 배송지 **18건** 발견.\n\n"
            "**판단 기준**: 이탈 시군구에 자체 Region Code가 이미 있으면 오류 의심.\n\n"
            "**결과**: 전 건 오류 의심 — 이탈 시군구 모두 자체 Region Code를 이미 보유."
        )
        error_data = [
            {"RC": "ALA", "주 지역": "서울 강남구(12)", "이탈 시군구": "경기 성남시 분당구", "이탈 수": 1, "Ship-to": "2516", "자체 RC": "GRA(19)"},
            {"RC": "BBA", "주 지역": "서울 양천구(15)", "이탈 시군구": "경기 시흥시", "이탈 수": 1, "Ship-to": "477", "자체 RC": "FVA(39)"},
            {"RC": "DEA", "주 지역": "대전 대덕구(23)", "이탈 시군구": "광주 광산구", "이탈 수": 1, "Ship-to": "KH11059", "자체 RC": "IEA(40), IDA(1)"},
            {"RC": "DSA", "주 지역": "충남 당진시(19)", "이탈 시군구": "경북 경산시", "이탈 수": 2, "Ship-to": "KH11342, KH11343", "자체 RC": "OIA(19)"},
            {"RC": "DSA", "주 지역": "충남 당진시(19)", "이탈 시군구": "전남 목포시", "이탈 수": 1, "Ship-to": "KH01796", "자체 RC": "IQA(17)"},
            {"RC": "EHA", "주 지역": "충북 청주시 흥덕구(22)", "이탈 시군구": "대전 대덕구", "이탈 수": 1, "Ship-to": "KH11103", "자체 RC": "DEA(23)"},
            {"RC": "EJA", "주 지역": "충북 진천군(11)", "이탈 시군구": "경기 안성시", "이탈 수": 1, "Ship-to": "7840", "자체 RC": "GNA(16)"},
            {"RC": "FNA", "주 지역": "경기 김포시(28)", "이탈 시군구": "인천 중구", "이탈 수": 3, "Ship-to": "562, KH00702, KH09917", "자체 RC": "FAA(11)"},
            {"RC": "GIA", "주 지역": "경기 화성시(91)", "이탈 시군구": "인천 서구", "이탈 수": 1, "Ship-to": "KP13408", "자체 RC": "FEA(20)"},
            {"RC": "LKA", "주 지역": "부산 수영구(10)", "이탈 시군구": "경남 양산시", "이탈 수": 1, "Ship-to": "KP11447", "자체 RC": "LSA(34)"},
            {"RC": "LKA", "주 지역": "부산 수영구(10)", "이탈 시군구": "경남 창원시 진해구", "이탈 수": 1, "Ship-to": "9580", "자체 RC": "MIA(15)"},
            {"RC": "MNA", "주 지역": "경남 진주시(50)", "이탈 시군구": "전북 정읍시", "이탈 수": 1, "Ship-to": "KH02651", "자체 RC": "KAA(10)"},
            {"RC": "MUA", "주 지역": "경남 함양군(4)", "이탈 시군구": "경북 포항시 남구", "이탈 수": 1, "Ship-to": "KP11861", "자체 RC": "PNA(29)"},
            {"RC": "NEA", "주 지역": "울산 울주군(17)", "이탈 시군구": "경북 포항시 남구", "이탈 수": 1, "Ship-to": "KP11029", "자체 RC": "PNA(29)"},
            {"RC": "OLA", "주 지역": "경북 고령군(5)", "이탈 시군구": "대구 수성구", "이탈 수": 1, "Ship-to": "KP11704", "자체 RC": "OGA(9)"},
            {"RC": "PHA", "주 지역": "경북 영덕군(4)", "이탈 시군구": "울산 동구", "이탈 수": 2, "Ship-to": "1307, KH10354", "자체 RC": "NCA(6)"},
            {"RC": "PHA", "주 지역": "경북 영덕군(4)", "이탈 시군구": "울산 울주군", "이탈 수": 2, "Ship-to": "5505, KH10017", "자체 RC": "NEA(17)"},
            {"RC": "PIA", "주 지역": "경북 울진군(9)", "이탈 시군구": "경남 거제시", "이탈 수": 3, "Ship-to": "10552, 5399, 9277", "자체 RC": "MLA(23)"},
        ]
        st.dataframe(
            pd.DataFrame(error_data),
            use_container_width=True,
            hide_index=True,
        )
        st.caption("※ 전체 3,320개 배송지 중 22건(0.7%) — 권역 재배치 시 처리 방안 결정 필요")

    # 1) RDC별 담당 배송지 수
    st.subheader("RDC별 담당 배송지 수")
    fig1 = go.Figure(go.Bar(
        x=rdc_names, y=delivery_counts,
        marker_color=colors,
        text=delivery_counts, textposition="outside",
    ))
    fig1.update_layout(yaxis_title="배송지 수", height=400, margin=dict(t=30))
    st.plotly_chart(fig1, use_container_width=True, key="bar_delivery_backup")

    sel_rdc_1 = st.selectbox(
        "RDC 선택 — 담당 배송지 목록",
        options=rdc_names,
        key="sel_delivery_backup",
    )
    filtered_1 = master_df[master_df["담당 RDC 명"] == sel_rdc_1][
        ["Ship-to party", "Region Code", "광역도시", "시군구"]
    ].drop_duplicates().sort_values(["광역도시", "시군구", "Ship-to party"]).reset_index(drop=True)
    st.dataframe(filtered_1, use_container_width=True, height=300, hide_index=True)

    # 2) RDC별 담당 시군구 수
    st.subheader("RDC별 담당 시군구 수")
    fig2 = go.Figure(go.Bar(
        x=rdc_names, y=sigungu_counts,
        marker_color=colors,
        text=sigungu_counts, textposition="outside",
    ))
    fig2.update_layout(yaxis_title="시군구 수", height=400, margin=dict(t=30))
    st.plotly_chart(fig2, use_container_width=True, key="bar_sigungu_backup")

    sel_rdc_2 = st.selectbox(
        "RDC 선택 — 담당 시군구 목록",
        options=rdc_names,
        key="sel_sigungu_backup",
    )
    filtered_2 = master_df[master_df["담당 RDC 명"] == sel_rdc_2][
        ["광역도시", "시군구"]
    ].drop_duplicates().sort_values(["광역도시", "시군구"]).reset_index(drop=True)
    st.dataframe(filtered_2, use_container_width=True, height=300, hide_index=True)
