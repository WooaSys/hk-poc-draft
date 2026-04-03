import json
import sys

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

# shapefile 광역도시 코드 매핑
CITY_CODE_MAP = {
    "11": "서울특별시", "21": "부산광역시", "22": "대구광역시", "23": "인천광역시",
    "24": "광주광역시", "25": "대전광역시", "26": "울산광역시", "29": "세종특별자치시",
    "31": "경기도", "32": "강원도", "33": "충청북도", "34": "충청남도",
    "35": "전라북도", "36": "전라남도", "37": "경상북도", "38": "경상남도", "39": "제주특별자치도",
}


def load_sigungu_gdf():
    """shapefile 로드 + 광역도시 컬럼 추가 + simplify."""
    gdf = gpd.read_file(RAW_DATA_DIR / "map" / "BND_SIGUNGU_PG.shp")
    gdf = gdf.to_crs(epsg=4326)
    gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.001, preserve_topology=True)
    gdf["광역도시"] = gdf["SIGUNGU_CD"].str[:2].map(CITY_CODE_MAP)
    return gdf

st.header("자료 분석")

tab_summary, tab_status, tab_loading, tab_demand = st.tabs(["기본자료", "RDC 현황", "타이어별 적재 기준(예상)", "수요 분포"])

with tab_summary:
    st.subheader("기본 자료")

    # CSV 파일 목록
    csv_files = sorted([f for f in RAW_DATA_DIR.iterdir() if f.suffix == ".csv"])

    if not csv_files:
        st.warning("raw_data 디렉토리에 CSV 파일이 없습니다.")
    else:
        # 파일 목록 + 다운로드
        selected_file = None
        for f in csv_files:
            col_name, col_download = st.columns([4, 1])
            with col_name:
                if st.button(f.name, key=f"btn_{f.name}", use_container_width=True):
                    selected_file = f
            with col_download:
                with open(f, "rb") as fp:
                    st.download_button(
                        "⬇",
                        data=fp.read(),
                        file_name=f.name,
                        key=f"dl_{f.name}",
                    )

        # session_state로 선택 유지
        if selected_file is not None:
            st.session_state["preview_file"] = selected_file

        # Preview 영역
        st.divider()
        st.caption("Preview")
        preview_target = st.session_state.get("preview_file")

        if preview_target and preview_target.exists():
            st.text(f"📄 {preview_target.name}")
            try:
                # 배송 실적은 skiprows=3 필요
                if preview_target.name.startswith("1."):
                    df = pd.read_csv(preview_target, skiprows=3)
                else:
                    df = pd.read_csv(preview_target)
                st.dataframe(df, use_container_width=True, height=400)
            except Exception as e:
                st.error(f"파일을 읽을 수 없습니다: {e}")
        else:
            st.info("파일명을 클릭하면 내용을 미리 볼 수 있습니다.")

    # --- RDC 위치 ---
    st.divider()
    st.subheader("RDC 위치")

    rdc_path = DB_DIR / "rdc_locations.json"
    with open(rdc_path, "r", encoding="utf-8") as f:
        rdc_data = json.load(f)

    rdc_df = pd.DataFrame(rdc_data)
    rdc_df.columns = ["Plant코드", "물류센터", "주소", "위도", "경도"]

    column_config = {
        "Plant코드": st.column_config.TextColumn(disabled=True),
        "물류센터": st.column_config.TextColumn(disabled=True),
    }

    edited_rdc = st.data_editor(
        rdc_df,
        use_container_width=True,
        num_rows="fixed",
        column_config=column_config,
        key="rdc_editor",
    )

    st.caption("※ 중부 RDC 주소 확인 필요 (금산공장과 동일한 주소로 확인됨)")

    if st.button("RDC 위치 저장"):
        save_data = edited_rdc.rename(columns={
            "Plant코드": "plant_code",
            "물류센터": "name",
            "주소": "address",
            "위도": "lat",
            "경도": "lon",
        }).to_dict(orient="records")
        with open(rdc_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        st.success("저장되었습니다.")

with tab_status:
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
        st.plotly_chart(fig3, use_container_width=True)

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
    st.plotly_chart(fig1, use_container_width=True)

    sel_rdc_1 = st.selectbox(
        "RDC 선택 — 담당 배송지 목록",
        options=rdc_names,
        key="sel_delivery",
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
    st.plotly_chart(fig2, use_container_width=True)

    sel_rdc_2 = st.selectbox(
        "RDC 선택 — 담당 시군구 목록",
        options=rdc_names,
        key="sel_sigungu",
    )
    filtered_2 = master_df[master_df["담당 RDC 명"] == sel_rdc_2][
        ["광역도시", "시군구"]
    ].drop_duplicates().sort_values(["광역도시", "시군구"]).reset_index(drop=True)
    st.dataframe(filtered_2, use_container_width=True, height=300, hide_index=True)

with tab_loading:
    # 적재 기준표 CSV 로드
    loading_df = pd.read_csv(DB_DIR / "타이어사이즈별_적재기준표.csv")

    st.markdown(
        "- 타이어 사이즈 × 트럭 톤수별 적재 기준 (1본당 적재율%, 만적 수량)\n"
        "- 구분: PCR(승용차) 222개, LTR/TBR(경트럭/트럭버스) 66개, 총 288개 사이즈\n"
        "- 용도: 혼합 적재 시 적재율 계산, 차량 배차 최적화"
    )

    with st.expander("예상근거"):
        st.markdown(
            "**참조 데이터:** `배송 실적` CSV (raw_data)\n\n"
            "**사용 컬럼:**\n"
            "| 컬럼명 | 설명 |\n"
            "|---|---|\n"
            "| `Size` | 타이어 사이즈 (예: 235/55R19) |\n"
            "| `Inch` | 인치 (예: 190) |\n"
            "| `Group` | 타이어 구분 (PCR, LTR, TBR 등) |\n"
            "| `Q'ty` | 적재 수량 |\n"
            "| `Measurement by Material and Q'ty` | 적재율(%) — 사이즈별 수량 기반 적재 비율 |\n"
            "| `Type of Truck by shipment` | 트럭 톤수 (1T, 3.5T, 5T, 8T, 11T) |\n\n"
            "**산출 방식:**\n"
            "- 동일 사이즈 × 동일 트럭 조합의 `Measurement / Q'ty` = 1본당 적재율(%)\n"
            "- 변동계수(CV) 2.3%로 사이즈×트럭 조합별 고정값으로 확인됨\n"
            "- 만적 수량 = 100% ÷ 1본당%"
        )

    truck_tons = ["1T", "3.5T", "5T", "8T", "11T"]
    ton_colors = ["#FF6B6B", "#45B7D1", "#4ECDC4", "#96CEB4", "#FFEAA7"]
    pct_cols = [f"{t}_1본당%" for t in truck_tons]

    # 1) 트럭 톤수별 대응 사이즈 수
    st.subheader("트럭 톤수별 대응 사이즈 수")
    ton_counts = [int(loading_df[c].notna().sum()) if c in loading_df.columns else 0 for c in pct_cols]

    fig_ton = go.Figure(go.Bar(
        x=truck_tons, y=ton_counts,
        marker_color=ton_colors,
        text=ton_counts, textposition="outside",
    ))
    fig_ton.update_layout(yaxis_title="사이즈 수", height=400, margin=dict(t=30))
    st.plotly_chart(fig_ton, use_container_width=True)

    # 2) 3.5T 기준 1본당 적재율 분포
    st.subheader("3.5T 기준 1본당 적재율 분포")
    col_35 = "3.5T_1본당%"
    if col_35 in loading_df.columns:
        data_35 = loading_df[col_35].dropna()
        fig_hist = go.Figure(go.Histogram(
            x=data_35,
            nbinsx=30,
            marker_color="#45B7D1",
        ))
        fig_hist.update_layout(
            xaxis_title="1본당 적재율 (%)",
            yaxis_title="사이즈 수",
            height=400,
            margin=dict(t=30),
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        st.caption(f"평균: {data_35.mean():.3f}% / 중앙값: {data_35.median():.3f}% / 범위: {data_35.min():.3f}% ~ {data_35.max():.3f}%")

    # 3) 인치별 × 트럭 톤수별 평균 적재율 히트맵
    st.subheader("인치별 × 트럭 톤수별 평균 적재율")
    loading_df["인치_num"] = pd.to_numeric(loading_df["인치"], errors="coerce")
    existing_cols = [c for c in pct_cols if c in loading_df.columns]
    heatmap_data = loading_df.groupby("인치_num")[existing_cols].mean().dropna(how="all")
    heatmap_data.columns = [c.replace("_1본당%", "") for c in heatmap_data.columns]

    fig_heat = go.Figure(go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns.tolist(),
        y=[str(int(i)) for i in heatmap_data.index],
        colorscale="YlOrRd",
        text=heatmap_data.values.round(3),
        texttemplate="%{text}",
        colorbar_title="1본당%",
    ))
    fig_heat.update_layout(
        xaxis_title="트럭 톤수",
        yaxis_title="인치",
        height=600,
        margin=dict(t=30),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # 4) 원본 데이터 테이블
    with st.expander("적재 기준표 전체 데이터"):
        st.dataframe(loading_df.drop(columns=["인치_num"], errors="ignore"), use_container_width=True, height=400, hide_index=True)

with tab_demand:
    # --- 상단: 산출 기준 안내 ---
    with st.expander("산출 기준 안내"):
        st.markdown(
            "**수요 산출 요약**\n"
            "- 247개 시군구(제주 제외)에 대해 배송 실적 기반 차량 환산 수요를 산출\n"
            "- 적재 기준 매칭률: 92.6% (미매칭 7.4%는 극소량 특수 규격, 수량 기준 0.02%)\n\n"
            "**왜 3.5T / 5T 기준인가**\n"
            "- 타이어의 정확한 CBM(부피) 데이터를 보유하고 있지 않음\n"
            "- 배송 실적의 `Measurement by Material and Q'ty` 컬럼으로부터 역산한 "
            "1본당 적재율(%)이 사이즈×트럭 조합별 고정값(CV 2.3%)임을 확인\n"
            "- CBM 없이도 트럭 적재율 기반으로 수요를 환산하는 방식\n"
            "- 3.5T: 전체 자체 차량의 54%, 모든 RDC 공통 주력\n"
            "- 5T: 전체의 32%, 두 번째 주력\n\n"
            "⚠️ **본 수요 데이터는 적재율 역산 기반 추정치이며, 실제 운영과 차이가 있을 수 있습니다.**\n\n"
            "※ 제주(제주RDC + 제주 시군구)는 도로 경로 부재로 본 분석에서 제외"
        )

    # --- 라디오 버튼 ---
    truck_basis = st.radio(
        "환산 기준",
        options=["3.5T 기준", "5T 기준"],
        horizontal=True,
        key="demand_truck_basis",
    )
    demand_col = "demand_3_5t" if truck_basis == "3.5T 기준" else "demand_5t"

    # --- 데이터 로드 ---
    demand_df = pd.read_csv(DB_DIR / "sigungu_demand.csv")
    sigungu_master = pd.read_csv(DB_DIR / "sigungu_master.csv")

    # RDC 위치
    rdc_path = DB_DIR / "rdc_locations.json"
    with open(rdc_path, "r", encoding="utf-8") as f:
        rdc_locs = json.load(f)

    # 시군구별 담당 RDC (수요 기준 최다 RDC)
    cost_df = pd.read_csv(DB_DIR / "cost_matrix.csv")
    # duration_rank=1인 RDC = 가장 가까운 RDC (현재 담당 기준으로 사용)
    # 실제 담당 RDC는 shipto_master 기반이지만, 여기서는 cost_matrix의 rank 1 사용
    # TODO: 실제 담당 RDC 매핑으로 교체 가능

    # shapefile 로드 (광역도시 포함)
    gdf = load_sigungu_gdf()

    # 시군구 마스터와 수요 데이터 병합
    demand_merged = sigungu_master.merge(demand_df[["sub_region_code", demand_col]], on="sub_region_code", how="left")

    # shapefile과 수요 병합 (광역도시+시군구로 매핑)
    gdf = gdf.merge(
        demand_merged[["시군구", "광역도시", demand_col, "sub_region_code"]],
        left_on=["광역도시", "SIGUNGU_NM"],
        right_on=["광역도시", "시군구"],
        how="left",
    )

    # RDC 색상
    rdc_names_map = ["평택RDC", "칠곡RDC", "계룡RDC", "제천RDC", "제주RDC", "중부RDC"]
    rdc_colors_map = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"]
    rdc_color_dict = dict(zip(rdc_names_map, rdc_colors_map))

    # --- folium 지도 ---
    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="CartoDB positron")

    # 수요 choropleth
    demand_valid = gdf[gdf[demand_col].notna() & (gdf[demand_col] > 0)].copy()
    demand_no = gdf[gdf[demand_col].isna() | (gdf[demand_col] == 0)].copy()

    if len(demand_valid) > 0:
        folium.Choropleth(
            geo_data=demand_valid.__geo_interface__,
            data=demand_valid,
            columns=["SIGUNGU_NM", demand_col],
            key_on="feature.properties.SIGUNGU_NM",
            fill_color="YlOrRd",
            fill_opacity=0.7,
            line_opacity=0.3,
            line_weight=0.5,
            legend_name=f"수요 ({truck_basis}, 대수)",
            name="수요 분포",
        ).add_to(m)

    # 수요 없는 시군구 (회색)
    if len(demand_no) > 0:
        folium.GeoJson(
            demand_no,
            style_function=lambda x: {
                "fillColor": "#DDDDDD",
                "color": "#999999",
                "weight": 0.3,
                "fillOpacity": 0.2,
            },
            name="수요 없음",
        ).add_to(m)

    # 시군구 tooltip (수요 + 담당 RDC 표시)
    # 담당 RDC: cost_matrix에서 duration_rank=1
    rank1 = cost_df[cost_df["duration_rank"] == 1][["sub_region_code", "rdc_name"]].copy()
    rank1.columns = ["sub_region_code", "담당RDC"]
    gdf_tooltip = gdf.merge(rank1, on="sub_region_code", how="left")

    folium.GeoJson(
        gdf_tooltip[gdf_tooltip[demand_col].notna()],
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "transparent",
            "weight": 0,
            "fillOpacity": 0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["광역도시", "SIGUNGU_NM", demand_col, "담당RDC"],
            aliases=["광역도시:", "시군구:", f"수요({truck_basis}):", "최근접 RDC:"],
            style="font-size:13px;",
        ),
        name="시군구 정보",
    ).add_to(m)

    # RDC 마커
    for rdc in rdc_locs:
        if rdc["name"] == "제주RDC":
            continue
        folium.Marker(
            location=[rdc["lat"], rdc["lon"]],
            popup=f"<b>{rdc['name']}</b><br>{rdc['address']}",
            tooltip=rdc["name"],
            icon=folium.Icon(color="black", icon="star", prefix="fa"),
        ).add_to(m)

    folium.LayerControl().add_to(m)

    full_html = m.get_root().render()
    st_html(full_html, height=620)

    # --- 참고사항: 자연권역 ---
    st.subheader("참고사항")

    st.markdown(
        "자연권역은 각 시군구를 소요시간 기준 **가장 가까운 RDC에 배정**했을 때의 기준 권역입니다. "
        "capacity, 운영 정책 등을 제거한 reference layer이며, 최종 배정안이 아닙니다."
    )

    include_jungbu = st.checkbox("중부RDC 포함", value=False, key="natural_jungbu")

    # 자연권역 모듈 호출
    sys.path.insert(0, str(APP_DIR / "01_preproc"))
    from natural_territory import generate_natural_territory
    territory_df, load_summary = generate_natural_territory(include_jungbu=include_jungbu)

    # Natural Load vs Current Load 비교 차트
    st.markdown("**RDC별 Natural Load vs Current Load (3.5T 기준)**")

    fig_load = go.Figure()
    fig_load.add_trace(go.Bar(
        name="Current Load",
        x=load_summary["rdc_name"],
        y=load_summary["current_load_3_5t"],
        marker_color="#636EFA",
        text=load_summary["current_load_3_5t"].round(0).astype(int),
        textposition="outside",
    ))
    fig_load.add_trace(go.Bar(
        name="Natural Load",
        x=load_summary["rdc_name"],
        y=load_summary["natural_load_3_5t"],
        marker_color="#FF6B6B",
        text=load_summary["natural_load_3_5t"].round(0).astype(int),
        textposition="outside",
    ))
    fig_load.update_layout(
        barmode="group",
        yaxis_title="수요 (3.5T 환산 대수)",
        height=400,
        margin=dict(t=30),
    )
    st.plotly_chart(fig_load, use_container_width=True)

    # 권역 조정 대상 시군구
    with st.expander("권역 조정 대상 시군구 (time_gap > 0)"):
        st.markdown(
            "재할당을 하지 않고, 자연권역과 비교했을 때 현재 담당 RDC보다 더 가까운 RDC가 있는 시군구 목록.\n\n"
            "`time_gap` = 현재 RDC 소요시간 - 자연권역 RDC 소요시간 (양수 = 현재가 더 먼 배정)"
        )
        gap_df = territory_df[territory_df["time_gap"] > 0].sort_values("time_gap", ascending=False)
        display_gap = gap_df[[
            "sigungu_name", "current_rdc_name", "current_time",
            "natural_rdc_name", "natural_time", "time_gap", "demand_3_5t",
        ]].copy()
        display_gap.columns = ["시군구", "현재 RDC", "현재 시간(분)", "자연 RDC", "자연 시간(분)", "Gap(분)", "수요(3.5T)"]
        st.dataframe(display_gap, use_container_width=True, hide_index=True)
        st.caption(
            f"전체 {len(territory_df)}개 시군구 중 {len(gap_df)}개가 조정 대상 "
            f"/ 수요 기준 주요 대상: 이천시(45.8대, 제천→평택), 광양시(52.1대, 계룡→칠곡)"
        )

    # Load 비교 테이블
    with st.expander("RDC별 상세 비교"):
        display_load = load_summary[[
            "rdc_name", "natural_sigungu_count", "current_sigungu_count",
            "natural_load_3_5t", "current_load_3_5t", "gap_3_5t",
        ]].copy()
        display_load.columns = ["RDC", "자연권역 시군구", "현재 시군구", "Natural Load", "Current Load", "Gap (현재-자연)"]
        st.dataframe(display_load, use_container_width=True, hide_index=True)
        st.caption("Gap 양수 = 현재가 자연권역보다 더 많은 물량 담당 (과부하 가능), 음수 = 여유")

    # 자연권역 지도
    with st.expander("자연권역 지도"):
        # 시군구별 자연권역 RDC 매핑
        gdf_natural = load_sigungu_gdf()

        nat_rdc = territory_df[["sub_region_code", "sigungu_name", "natural_rdc_name"]].copy()
        gdf_natural = gdf_natural.merge(
            sigungu_master[["시군구", "광역도시", "sub_region_code"]],
            left_on=["광역도시", "SIGUNGU_NM"], right_on=["광역도시", "시군구"], how="left",
        )
        gdf_natural = gdf_natural.merge(nat_rdc, on="sub_region_code", how="left")
        gdf_natural["fill_color"] = gdf_natural["natural_rdc_name"].map(rdc_color_dict).fillna("#DDDDDD")

        m_nat = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="CartoDB positron")

        assigned_nat = gdf_natural[gdf_natural["natural_rdc_name"].notna()].copy()
        folium.GeoJson(
            assigned_nat,
            style_function=lambda feature: {
                "fillColor": feature["properties"]["fill_color"],
                "color": "#333333",
                "weight": 0.8,
                "fillOpacity": 0.6,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["광역도시", "SIGUNGU_NM", "natural_rdc_name"],
                aliases=["광역도시:", "시군구:", "자연권역 RDC:"],
                style="font-size:13px;",
            ),
            name="자연권역",
        ).add_to(m_nat)

        for rdc in rdc_locs:
            if rdc["name"] == "제주RDC":
                continue
            if not include_jungbu and rdc["name"] == "중부RDC":
                continue
            folium.Marker(
                location=[rdc["lat"], rdc["lon"]],
                popup=f"<b>{rdc['name']}</b>",
                tooltip=rdc["name"],
                icon=folium.Icon(color="black", icon="star", prefix="fa"),
            ).add_to(m_nat)

        # 범례
        legend_html = """
        <div style="position: fixed; bottom: 30px; left: 30px; z-index: 1000;
             background: white; padding: 12px 16px; border-radius: 8px;
             box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-size: 13px; line-height: 1.6;">
        <b>자연권역 RDC</b><br>
        """
        for name, color in rdc_color_dict.items():
            if name == "제주RDC":
                continue
            if not include_jungbu and name == "중부RDC":
                continue
            legend_html += f'<span style="background:{color};width:14px;height:14px;display:inline-block;margin-right:6px;border-radius:2px;vertical-align:middle;"></span>{name}<br>'
        legend_html += "</div>"

        nat_full_html = m_nat.get_root().render()
        nat_full_html = nat_full_html.replace("</body>", legend_html + "</body>")
        st_html(nat_full_html, height=620)

    # --- 자연권역 분석 결과 해석 ---
    st.divider()
    st.subheader("자연권역 분석 결과 해석")

    st.markdown(
        "#### 현재 권역 구조는 공간적으로 크게 왜곡되어 있지 않다\n\n"
        "- 전체 247개 시군구 중 **231개(94%)가 이미 가장 가까운 RDC에 배정**되어 있음\n"
        "- 더 가까운 RDC가 있는 시군구는 16개(6%), gap > 30분은 1개뿐\n"
        "- 현재 구조는 이미 상당 부분 거리/시간 기반으로 형성된 상태\n\n"
        "#### 문제의 본질은 권역 왜곡이 아니라 수요 편중\n\n"
        "- 현재도 이미 가까운 곳으로 배정되어 있는데, 평택RDC가 40% 가까이 처리 중\n"
        "- 원인은 ~~잘못된 권역 배정~~이 아니라 **수요 자체의 공간 편중** (수도권/경기권 집중)\n"
        "- RDC capacity 불균형, 특정 RDC 주변 고수요 집중이 실제 원인\n\n"
        "#### 재할당만으로 큰 개선이 안 나올 가능성\n\n"
        "- 현재권역 ≈ 자연권역이므로, 단순히 가까운 RDC로 재배정하는 것만으로는 구조가 크게 바뀌지 않음\n"
        "- OR-Tools로 재할당하더라도 **capacity 제약을 강하게 주지 않으면 현재와 거의 비슷한 결과**가 나올 가능성 높음\n\n"
        "#### 결론 및 다음 단계\n\n"
        "1. 현재 권역은 자연권역과 거의 일치 → '비정상적 배정으로 인한 과부하' 가설은 약함\n"
        "2. 자연권역은 기준선 역할을 마침\n"
        "3. **초점을 capacity 추정과 시나리오 재분배로 전환** 필요\n"
        "   - RDC별 처리 상한(capacity) 추정\n"
        "   - capacity 제약 하 시나리오별 재분배 (OR-Tools)\n"
        "   - '가까운 곳으로 보내되, 특정 RDC에 몰리지 않게' 하는 균형 최적화"
    )
