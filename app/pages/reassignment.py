"""
권역 재할당 페이지 (reassignment.py)

목적:
    Capacity Stress Test 엔진을 활용하여 평택RDC 물량 축소 시나리오를 실행하고,
    비용 증가 곡선, RDC별 물량 변화, 이동 시군구 지도 등을 시각화한다.

입력:
    - stress_test 엔진 (app/01_preproc/stress_test/)
    - app/db/ 데이터 파일들

출력:
    - 비용 증가 곡선, RDC별 물량 차트, 이동 지도, 상세 테이블
"""

import sys
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

# stress_test 모듈 경로 추가
sys.path.insert(0, str(APP_DIR / "01_preproc"))

st.header("권역 재할당")

st.caption(
    "※ 본 분석은 보정된 배송지 데이터(`shipto_master_corrected.csv`)를 사용합니다. "
    "원본 데이터에서 확인된 18건의 Region Code 이상(다른 광역도시에 배정된 배송지)을 "
    "해당 시군구의 자체 Region Code로 재배정한 데이터입니다."
)

st.caption(
    "📌 수요: `daily_demand_3_5t` (시군구별 3.5T 환산 일평균 수요) / "
    "비용: `duration_min` (RDC→시군구 OSRM 이동시간) / "
    "목적함수: Σ(수요 × 이동시간) 최소화 — 수요가 많은 곳일수록 가까운 RDC에 배정"
)

tab_reduce, tab_equal = st.tabs(["평택 축소 재할당", "균등화 재할당"])

# =============================================================
# Tab 1: 평택 축소 재할당 (기존)
# =============================================================
with tab_reduce:

    # =============================================================
    # 파라미터 설정
    # =============================================================
    st.subheader("파라미터 설정")

    col1, col2 = st.columns(2)

    with col1:
        ratios_input = st.text_input(
            "축소율 리스트 (%)",
            value="5, 10, 15, 20",
            help="콤마로 구분. 0%(baseline)은 자동 포함됩니다.",
        )
        include_jungbu = st.checkbox("중부RDC 포함", value=False, key="reassign_jungbu")
        use_penalty = st.checkbox("공간 연속성 제약 (고립 방지)", value=True, key="reassign_penalty")

    with col2:
        receiver_buffer = st.number_input(
            "수용 RDC 버퍼 (%)",
            min_value=100,
            max_value=200,
            value=120,
            step=5,
            help="전체 수요 균등 분배 기준 × 버퍼. 나머지 RDC의 수용 상한",
        )

    run_button = st.button("실행", type="primary", use_container_width=True)

    # =============================================================
    # 실행
    # =============================================================
    if run_button:
        # 축소율 파싱
        try:
            ratios = [int(r.strip()) / 100 for r in ratios_input.split(",")]
            ratios = [0.0] + [r for r in ratios if r > 0]  # 0% 자동 포함
            ratios = sorted(set(ratios))
        except ValueError:
            st.error("축소율 형식이 잘못되었습니다. 예: 5, 10, 15, 20")
            st.stop()

        from stress_test.common import load_problem_data, create_scenarios
        from stress_test.runner import run_stress_test

        with st.spinner("데이터 로드 중..."):
            problem = load_problem_data(include_jungbu=include_jungbu)

        with st.spinner(f"시나리오 {len(ratios)}개 실행 중..."):
            scenarios = create_scenarios(
                problem,
                target_rdc="평택RDC",
                reduction_ratios=ratios,
                receiver_buffer=receiver_buffer / 100,
            )
            results = run_stress_test(
                problem=problem,
                scenarios=scenarios,
                solver_type="cpsat",
                isolation_penalty=10.0 if use_penalty else 0.0,
            )

        # infeasible 시나리오 경고
        infeasible_list = [r.scenario_id for r in results if r.status == "infeasible"]
        if infeasible_list:
            st.warning(
                f"⚠️ {', '.join(infeasible_list)}: 해 없음(infeasible) — "
                f"수용 RDC의 여유 용량이 부족합니다. 수용 RDC 버퍼를 높여보세요."
            )

        # session_state에 결과 저장
        st.session_state["reassign_results"] = results
        st.session_state["reassign_problem"] = problem
        st.session_state["reassign_ratios"] = ratios

    # =============================================================
    # 결과 표시
    # =============================================================
    if "reassign_results" not in st.session_state:
        st.info("파라미터를 설정하고 실행 버튼을 눌러주세요.")

    if "reassign_results" in st.session_state:
        results = st.session_state["reassign_results"]
        problem = st.session_state["reassign_problem"]
        ratios = st.session_state["reassign_ratios"]

        # --- 1) 이동시간/거리 증가 곡선 ---
        st.subheader("이동시간 / 거리 증가 곡선")

        x_vals = [int(r * 100) for r in ratios]
        y_time = [res.cost_increase_pct for res in results]
        y_dist = [res.distance_increase_pct for res in results]

        fig_curve = go.Figure()
        fig_curve.add_trace(go.Scatter(
        x=x_vals, y=y_time,
        mode="lines+markers+text",
        name="이동시간 증가율",
        text=[f"+{v}%" for v in y_time],
        textposition="top center",
        marker=dict(size=10),
        line=dict(width=3, color="#636EFA"),
        ))
        fig_curve.add_trace(go.Scatter(
        x=x_vals, y=y_dist,
        mode="lines+markers+text",
        name="이동거리 증가율",
        text=[f"+{v}%" for v in y_dist],
        textposition="bottom center",
        marker=dict(size=10),
        line=dict(width=3, color="#EF553B", dash="dash"),
        ))
        fig_curve.update_layout(
        xaxis_title="평택RDC 축소율 (%)",
        yaxis_title="증가율 (%)",
        height=400,
        margin=dict(t=30),
        )
        st.plotly_chart(fig_curve, use_container_width=True)

        # --- 5) 시나리오 요약 테이블 ---
        st.subheader("시나리오 요약")

        summary_rows = []

        # Baseline (실제 운영) 행 추가
        baseline_time = sum(
        problem.demand[i] * problem.cost[i][problem.current_rdc_idx[i]]
        for i in range(problem.n_sigungu)
        )
        baseline_dist = sum(
        problem.demand[i] * problem.distance[i][problem.current_rdc_idx[i]]
        for i in range(problem.n_sigungu)
        )
        summary_rows.append({
        "시나리오": "현재 운영",
        "축소율": "-",
        "총 이동시간": round(baseline_time, 1),
        "시간 증가율": "-",
        "총 이동거리": round(baseline_dist, 1),
        "거리 증가율": "-",
        "이동 시군구": 0,
        "이동 수요": 0,
        "상태": "baseline",
        })

        for res in results:
            summary_rows.append({
            "시나리오": res.scenario_id,
            "축소율": f"{int(res.scenario_id[1:])}%",
            "총 이동시간": res.total_cost,
            "시간 증가율": f"+{res.cost_increase_pct}%",
            "총 이동거리": res.total_distance,
            "거리 증가율": f"+{res.distance_increase_pct}%",
            "이동 시군구": len(res.moved_detail),
            "이동 수요": round(res.moved_detail["demand"].sum(), 1) if len(res.moved_detail) > 0 else 0,
            "상태": res.status,
            })
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

            # --- 시나리오 선택 (2~4번 결과에 사용) ---
            st.divider()
            scenario_options = [res.scenario_id for res in results]
            if not scenario_options:
                st.stop()

                selected_scenario = st.selectbox(
                "시나리오 선택 (상세 결과)",
                options=scenario_options,
                index=len(scenario_options) - 1,
                )

                sel_result = next(r for r in results if r.scenario_id == selected_scenario)

                # Baseline = 실제 운영 상태 (optimizer 결과가 아닌 current_rdc 기준)
                baseline_rows = []
                for i in range(problem.n_sigungu):
                    j = problem.current_rdc_idx[i]
                    baseline_rows.append({
                    "sub_region_code": problem.sigungu_codes[i],
                    "sigungu_name": problem.sigungu_names[i],
                    "assigned_rdc": problem.rdc_names[j],
                    "moved": False,
                    })
                    baseline_detail = pd.DataFrame(baseline_rows)

                    # --- 2) RDC별 물량 변화 ---
                    st.subheader(f"RDC별 물량 변화 ({selected_scenario})")

                    # 실제 운영 기준 RDC별 load
                    current_load_list = [0.0] * problem.n_rdc
                    for i in range(problem.n_sigungu):
                        current_load_list[problem.current_rdc_idx[i]] += problem.demand[i]
                        current_load_list = [round(v, 1) for v in current_load_list]
                        current_total = sum(current_load_list)
                        current_pct = [round(v / current_total * 100, 1) for v in current_load_list]

                        sel_total = sel_result.rdc_summary["assigned_load"].sum()
                        sel_pct = (sel_result.rdc_summary["assigned_load"] / sel_total * 100).round(1)

                        fig_rdc = go.Figure()
                        fig_rdc.add_trace(go.Bar(
                        name="현재 운영",
                        x=problem.rdc_names,
                        y=current_load_list,
                        marker_color="#636EFA",
                        text=[f"{v} ({p}%)" for v, p in zip(current_load_list, current_pct)],
                        textposition="outside",
                        ))
                        fig_rdc.add_trace(go.Bar(
                        name=f"{selected_scenario} (재할당)",
                        x=sel_result.rdc_summary["rdc_name"],
                        y=sel_result.rdc_summary["assigned_load"],
                        marker_color="#FF6B6B",
                        text=[f"{v} ({p}%)" for v, p in zip(sel_result.rdc_summary["assigned_load"], sel_pct)],
                        textposition="outside",
                        ))
                        fig_rdc.update_layout(
                        barmode="group",
                        yaxis_title="배정 수요 (3.5T 일평균)",
                        height=400,
                        margin=dict(t=30),
                        )
                        st.plotly_chart(fig_rdc, use_container_width=True)

                        # RDC별 비중 비교 테이블
                        with st.expander("RDC별 상세"):
                            detail_df = sel_result.rdc_summary.copy()
                            detail_df["baseline_load"] = current_load_list
                            detail_df["baseline_pct"] = current_pct
                            detail_df["assigned_pct"] = sel_pct.values
                            detail_df["load_change"] = (detail_df["assigned_load"] - detail_df["baseline_load"]).round(1)
                            detail_df["pct_change"] = (detail_df["assigned_pct"] - detail_df["baseline_pct"]).round(1)
                            display_detail = detail_df[[
                            "rdc_name", "capacity", "baseline_load", "baseline_pct",
                            "assigned_load", "assigned_pct", "load_change", "pct_change", "utilization_pct",
                            ]].copy()
                            display_detail.columns = [
                            "RDC", "Capacity", "현재 물량", "현재 비중(%)",
                            "재할당 물량", "재할당 비중(%)", "물량 변화", "비중 변화(%p)", "Utilization(%)",
                            ]
                            st.dataframe(display_detail, use_container_width=True, hide_index=True)

                            # --- 3) 권역 비교 지도 (Baseline vs 시나리오) ---
                            st.subheader(f"권역 비교 지도 (Baseline vs {selected_scenario})")

                            # 공통 데이터 로드
                            rdc_names_map = ["평택RDC", "칠곡RDC", "계룡RDC", "제천RDC", "제주RDC", "중부RDC"]
                            rdc_colors_map = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"]
                            rdc_color_dict = dict(zip(rdc_names_map, rdc_colors_map))

                            sigungu_master = pd.read_csv(DB_DIR / "sigungu_master.csv")

                            # shapefile 광역도시 코드 매핑
                            CITY_CODE_MAP = {
                            "11": "서울특별시", "21": "부산광역시", "22": "대구광역시", "23": "인천광역시",
                            "24": "광주광역시", "25": "대전광역시", "26": "울산광역시", "29": "세종특별자치시",
                            "31": "경기도", "32": "강원도", "33": "충청북도", "34": "충청남도",
                            "35": "전라북도", "36": "전라남도", "37": "경상북도", "38": "경상남도", "39": "제주특별자치도",
                            }

                            gdf = gpd.read_file(RAW_DATA_DIR / "map" / "BND_SIGUNGU_PG.shp")
                            gdf = gdf.to_crs(epsg=4326)
                            gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.001, preserve_topology=True)
                            gdf["광역도시"] = gdf["SIGUNGU_CD"].str[:2].map(CITY_CODE_MAP)

                            gdf_base = gdf.merge(
                            sigungu_master[["시군구", "광역도시", "sub_region_code"]],
                            left_on=["광역도시", "SIGUNGU_NM"], right_on=["광역도시", "시군구"], how="left",
                            )

                            with open(DB_DIR / "rdc_locations.json", "r", encoding="utf-8") as f:
                                rdc_locs = json.load(f)

                                def _build_map(detail_df, title, show_moved_border=False):
                                    """배정 결과를 folium 지도로 생성."""
                                    gdf_map = gdf_base.copy()
                                    gdf_map = gdf_map.merge(
                                    detail_df[["sub_region_code", "assigned_rdc", "moved"]],
                                    on="sub_region_code", how="left",
                                    )
                                    gdf_map["fill_color"] = gdf_map["assigned_rdc"].map(rdc_color_dict).fillna("#DDDDDD")
                                    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="CartoDB positron")
                                    assigned = gdf_map[gdf_map["assigned_rdc"].notna()].copy()
                                    folium.GeoJson(
                                    assigned,
                                    style_function=lambda feature: {
                                    "fillColor": feature["properties"]["fill_color"],
                                    "color": "#FF0000" if show_moved_border and feature["properties"].get("moved") else "#333333",
                                    "weight": 3 if show_moved_border and feature["properties"].get("moved") else 0.5,
                                    "fillOpacity": 0.6,
                                    },
                                    tooltip=folium.GeoJsonTooltip(
                                    fields=["광역도시", "SIGUNGU_NM", "assigned_rdc"],
                                    aliases=["광역도시:", "시군구:", "배정 RDC:"],
                                    style="font-size:13px;",
                                    ),
                                    name=title,
                                    ).add_to(m)
                                    for rdc in rdc_locs:
                                        if rdc["name"] == "제주RDC":
                                            continue
                                            if not st.session_state.get("reassign_jungbu", False) and rdc["name"] == "중부RDC":
                                                continue
                                                folium.Marker(
                                                location=[rdc["lat"], rdc["lon"]],
                                                popup=f"<b>{rdc['name']}</b>",
                                                tooltip=rdc["name"],
                                                icon=folium.Icon(color="black", icon="star", prefix="fa"),
                                                ).add_to(m)
                                                legend_html = '<div style="position: fixed; bottom: 30px; left: 10px; z-index: 1000; background: white; padding: 8px 12px; border-radius: 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-size: 11px; line-height: 1.6;">'
                                                for name, color in rdc_color_dict.items():
                                                    if name == "제주RDC":
                                                        continue
                                                        if not st.session_state.get("reassign_jungbu", False) and name == "중부RDC":
                                                            continue
                                                            legend_html += f'<span style="background:{color};width:12px;height:12px;display:inline-block;margin-right:4px;border-radius:2px;vertical-align:middle;"></span>{name}<br>'
                                                            legend_html += "</div>"
                                                            full_html = m.get_root().render()
                                                            full_html = full_html.replace("</body>", legend_html + "</body>")
                                                            return full_html

                                                            # 좌우 배치
                                                            col_left, col_right = st.columns(2)

                                                            with col_left:
                                                                st.caption("현재 운영 (실제 배정)")
                                                                baseline_html = _build_map(baseline_detail, "현재 운영", show_moved_border=False)
                                                                st_html(baseline_html, height=500)

                                                                with col_right:
                                                                    st.caption(f"{selected_scenario} (재할당)")
                                                                    scenario_html = _build_map(sel_result.sigungu_detail, selected_scenario, show_moved_border=True)
                                                                    st_html(scenario_html, height=500)

                                                                    if len(sel_result.moved_detail) > 0:
                                                                        st.caption("※ 오른쪽 지도: 빨간 테두리 = 이동된 시군구")

                                                                        # --- 4) 이동 상세 테이블 ---
                                                                        st.subheader(f"이동 상세 ({selected_scenario})")

                                                                        if len(sel_result.moved_detail) > 0:
                                                                            display_moved = sel_result.moved_detail[[
                                                                            "sigungu_name", "demand", "current_rdc", "assigned_rdc",
                                                                            "current_time", "assigned_time", "delta_time",
                                                                            "current_distance", "assigned_distance", "delta_distance",
                                                                            ]].copy()
                                                                            display_moved.columns = [
                                                                            "시군구", "수요(3.5T)", "이전 RDC", "변경 RDC",
                                                                            "이전 시간(분)", "변경 시간(분)", "시간 증가(분)",
                                                                            "이전 거리(km)", "변경 거리(km)", "거리 증가(km)",
                                                                            ]
                                                                            display_moved = display_moved.sort_values("시간 증가(분)", ascending=False)
                                                                            st.dataframe(display_moved, use_container_width=True, hide_index=True)
                                                                            else:
                                                                            st.info("이동된 시군구가 없습니다.")

                                                                            # --- 6) 배송 비용 비교 ---
                                                                            st.divider()
                                                                            st.subheader("배송 비용 비교 (3.5T 기준, 2025년 11월 단가)")

                                                                            with st.expander("산출 기준 안내"):
                                                                            st.markdown(
                                                                            "**비용 산출 흐름**\n\n"
                                                                            "1. 배송 실적의 타이어 사이즈/수량에서 `Measurement / Q\'ty`로 1본당 적재율(%) 역산\n"
                                                                            "2. 적재율 기준으로 전체 배송 물량을 3.5T 환산 대수(`daily_demand_3_5t`)로 변환\n"
                                                                            "3. 각 시군구의 환산 대수 × RDC-시군구 거리구간 단가 = 배송 비용\n\n"
                                                                            "**일평균 추정값입니다**\n\n"
                                                                            "- `daily_demand_3_5t`는 데이터 기간(2025년 2월+11월, 약 52일) 총 수요를 배송 발생 일수로 나눈 일평균\n"
                                                                            "- 따라서 표시되는 비용도 일평균 배송비용(추정)\n\n"
                                                                            "**거리 보정**\n\n"
                                                                            "VROOM은 시군구 대표좌표(시청) 간 거리만 계산하므로, 시군구 내부 배송지 순회 거리가 빠짐. "
                                                                            "실제 배송 실적의 `Distance by Shipment`와 비교하여 OSRM 거리 구간별 보정계수(1.22~1.82)를 적용.\n\n"
                                                                            "**차이 원인**\n\n"
                                                                            "- 실제로는 1T, 5T 등 혼합 톤수 사용 → 톤수별 단가가 다름\n"
                                                                            "- 실제로는 여러 시군구를 순회 배송 → 거리 계산이 다름\n"
                                                                            "- 시나리오 간 상대 비교 목적으로는 같은 기준이므로 유효"
                                                                            )

                                                                            import importlib
                                                                            import stress_test.common as _stc
                                                                            importlib.reload(_stc)
                                                                            calculate_delivery_cost = _stc.calculate_delivery_cost

                                                                            # 현재 운영 비용
                                                                            baseline_cost_df = calculate_delivery_cost(
                                                                            problem, list(problem.current_rdc_idx), truck_type="3.5T"
                                                                            )

                                                                            # 시나리오별 비용
                                                                            scenario_cost_rows = []
                                                                            scenario_cost_rows.append({
                                                                            "시나리오": "현재 운영",
                                                                            "총 배송비용": baseline_cost_df["total_cost"].sum(),
                                                                            })
                                                                            for res in results:
                                                                            cost_df = calculate_delivery_cost(problem, res.assignment, truck_type="3.5T")
                                                                            scenario_cost_rows.append({
                                                                            "시나리오": res.scenario_id,
                                                                            "총 배송비용": cost_df["total_cost"].sum(),
                                                                            })

                                                                            cost_summary = pd.DataFrame(scenario_cost_rows)
                                                                            cost_summary["비용 증감"] = cost_summary["총 배송비용"] - cost_summary["총 배송비용"].iloc[0]
                                                                            cost_summary["증감율"] = (cost_summary["비용 증감"] / cost_summary["총 배송비용"].iloc[0] * 100).round(2)
                                                                            cost_summary["총 배송비용(만원)"] = (cost_summary["총 배송비용"] / 10000).round(0).astype(int)
                                                                            cost_summary["비용 증감(만원)"] = (cost_summary["비용 증감"] / 10000).round(0).astype(int)

                                                                            fig_cost = go.Figure()
                                                                            fig_cost.add_trace(go.Bar(
                                                                            x=cost_summary["시나리오"],
                                                                            y=cost_summary["총 배송비용(만원)"],
                                                                            text=cost_summary.apply(
                                                                            lambda r: f"{r['총 배송비용(만원)']:,}만원" if r['시나리오'] == '현재 운영'
                                                                            else f"{r['총 배송비용(만원)']:,}만원 ({'+' if r['증감율']>=0 else ''}{r['증감율']}%)",
                                                                            axis=1
                                                                            ),
                                                                            textposition="outside",
                                                                            marker_color=["#636EFA"] + ["#FF6B6B"] * (len(cost_summary) - 1),
                                                                            ))
                                                                            fig_cost.update_layout(yaxis_title="일평균 배송비용 (만원)", height=400, margin=dict(t=30))
                                                                            st.plotly_chart(fig_cost, use_container_width=True)

                                                                            # 선택된 시나리오의 RDC별 비용 비교
                                                                            st.markdown(f"**RDC별 배송비용 비교 ({selected_scenario})**")

                                                                            sel_cost_df = calculate_delivery_cost(problem, sel_result.assignment, truck_type="3.5T")

                                                                            fig_rdc_cost = go.Figure()
                                                                            fig_rdc_cost.add_trace(go.Bar(
                                                                            name="현재 운영", x=baseline_cost_df["rdc_name"],
                                                                            y=(baseline_cost_df["total_cost"] / 10000).round(0),
                                                                            marker_color="#636EFA",
                                                                            text=(baseline_cost_df["total_cost"] / 10000).round(0).astype(int).apply(lambda x: f"{x:,}만원"),
                                                                            textposition="outside",
                                                                            ))
                                                                            fig_rdc_cost.add_trace(go.Bar(
                                                                            name=f"{selected_scenario}", x=sel_cost_df["rdc_name"],
                                                                            y=(sel_cost_df["total_cost"] / 10000).round(0),
                                                                            marker_color="#FF6B6B",
                                                                            text=(sel_cost_df["total_cost"] / 10000).round(0).astype(int).apply(lambda x: f"{x:,}만원"),
                                                                            textposition="outside",
                                                                            ))
                                                                            fig_rdc_cost.update_layout(barmode="group", yaxis_title="일평균 배송비용 (만원)", height=400, margin=dict(t=30))
                                                                            st.plotly_chart(fig_rdc_cost, use_container_width=True)

                                                                            with st.expander("RDC별 비용 상세"):
                                                                            detail_cost = sel_cost_df.copy()
                                                                            detail_cost = detail_cost.merge(
                                                                            baseline_cost_df[["rdc_name", "total_cost", "avg_cost_per_trip"]],
                                                                            on="rdc_name", suffixes=("_scenario", "_baseline"),
                                                                            )
                                                                            detail_cost["비용 증감"] = detail_cost["total_cost_scenario"] - detail_cost["total_cost_baseline"]
                                                                            display_cost = pd.DataFrame({
                                                                            "RDC": detail_cost["rdc_name"],
                                                                            "현재 비용": detail_cost["total_cost_baseline"].apply(lambda x: f"{x:,.0f}원"),
                                                                            "현재 건당": detail_cost["avg_cost_per_trip_baseline"].apply(lambda x: f"{x:,.0f}원"),
                                                                            f"{selected_scenario} 비용": detail_cost["total_cost_scenario"].apply(lambda x: f"{x:,.0f}원"),
                                                                            f"{selected_scenario} 건당": detail_cost["avg_cost_per_trip_scenario"].apply(lambda x: f"{x:,.0f}원"),
                                                                            "비용 증감": detail_cost["비용 증감"].apply(lambda x: f"{x:+,.0f}원"),
                                                                            })
                                                                            st.dataframe(display_cost, use_container_width=True, hide_index=True)

                                                                            st.caption("※ 배송비용 = 시군구별 수요(3.5T 대수) × RDC-시군구 거리구간 단가 (2025년 11월 기준). 추정값이며 실제 운영 비용과 차이가 있을 수 있음.")


with tab_equal:
    st.markdown(
        "모든 RDC가 비슷한 물량을 처리하도록 균등 분배하는 방식. "
        "균등 몫(총 수요 ÷ RDC 수) × 버퍼를 각 RDC의 capacity로 설정."
    )

    st.subheader("파라미터 설정")

    col_eq1, col_eq2 = st.columns(2)

    with col_eq1:
        eq_buffers_input = st.text_input(
            "균등 버퍼 리스트 (%)",
            value="110, 120, 130",
            help="콤마로 구분. 균등 몫 × 버퍼 = 각 RDC capacity",
            key="eq_buffers",
        )
        eq_jungbu = st.checkbox("중부RDC 포함", value=False, key="eq_jungbu")

    with col_eq2:
        eq_penalty = st.checkbox("공간 연속성 제약 (고립 방지)", value=True, key="eq_penalty")

    eq_run = st.button("균등화 실행", type="primary", use_container_width=True)

    if eq_run:
        try:
            eq_buffers = sorted(set([int(b.strip()) / 100 for b in eq_buffers_input.split(",") if b.strip()]))
        except ValueError:
            st.error("버퍼 형식 오류")
            st.stop()

        from stress_test.common import load_problem_data, Scenario
        from stress_test.runner import run_stress_test

        with st.spinner("데이터 로드 중..."):
            eq_problem = load_problem_data(include_jungbu=eq_jungbu)

        total_demand = sum(eq_problem.demand)
        equal_share = total_demand / eq_problem.n_rdc

        # 현재 RDC별 load
        eq_current_load = [0.0] * eq_problem.n_rdc
        for i in range(eq_problem.n_sigungu):
            j = eq_problem.current_rdc_idx[i]
            eq_current_load[j] += eq_problem.demand[i]

        # 시나리오 생성
        eq_scenarios = []
        for buf in eq_buffers:
            cap = equal_share * buf
            caps = [cap] * eq_problem.n_rdc
            eq_scenarios.append(Scenario(scenario_id=f"EQ_{int(buf*100)}", capacity=caps))

        with st.spinner(f"균등화 시나리오 {len(eq_scenarios)}개 실행 중..."):
            eq_results = run_stress_test(
                eq_problem, eq_scenarios, solver_type="cpsat",
                isolation_penalty=1.0 if eq_penalty else 0.0,
            )

        st.session_state["eq_results"] = eq_results
        st.session_state["eq_problem"] = eq_problem
        st.session_state["eq_current_load"] = eq_current_load
        st.session_state["eq_equal_share"] = equal_share

    # --- 결과 표시 ---
    if "eq_results" not in st.session_state:
        st.info("파라미터를 설정하고 실행하세요.")
    else:
        eq_results = st.session_state["eq_results"]
        eq_problem = st.session_state["eq_problem"]
        eq_current_load = st.session_state["eq_current_load"]
        equal_share = st.session_state["eq_equal_share"]
        total_demand = sum(eq_problem.demand)

        st.caption(f"총 수요: {total_demand:.1f} / RDC {eq_problem.n_rdc}개 / 균등 몫: {equal_share:.1f}")

        # --- 이동시간/거리 증가 곡선 ---
        st.subheader("이동시간 / 거리 증가 곡선")

        # 현 상태(0%) + 시나리오 — 균등이 강할수록 비용 증가
        eq_x = ["현 상태"] + [f"균등 {int(r.scenario_id.split('_')[1])}%" for r in eq_results]
        eq_y_time = [0.0] + [r.cost_increase_pct for r in eq_results]
        eq_y_dist = [0.0] + [r.distance_increase_pct for r in eq_results]

        fig_eq_curve = go.Figure()
        fig_eq_curve.add_trace(go.Scatter(
            x=eq_x, y=eq_y_time, mode="lines+markers+text",
            name="이동시간 증가율",
            text=[f"+{v}%" for v in eq_y_time], textposition="top center",
            marker=dict(size=10), line=dict(width=3, color="#636EFA"),
        ))
        fig_eq_curve.add_trace(go.Scatter(
            x=eq_x, y=eq_y_dist, mode="lines+markers+text",
            name="이동거리 증가율",
            text=[f"+{v}%" for v in eq_y_dist], textposition="bottom center",
            marker=dict(size=10), line=dict(width=3, color="#EF553B", dash="dash"),
        ))
        fig_eq_curve.update_layout(
            xaxis_title="← 현 상태 ─────── 균등 강도 ───────→",
            yaxis_title="증가율 (%)",
            height=400, margin=dict(t=30),
        )
        st.plotly_chart(fig_eq_curve, use_container_width=True)

        # 시나리오 요약 테이블
        st.subheader("시나리오 요약")

        eq_summary_rows = [{
            "시나리오": "현재 운영", "cap/RDC": "-",
            "시간 증가": "-", "거리 증가": "-", "이동 수": 0,
        }]
        for j, rn in enumerate(eq_problem.rdc_names):
            eq_summary_rows[0][rn] = f"{eq_current_load[j]:.1f} ({eq_current_load[j]/total_demand*100:.1f}%)"

        for res in eq_results:
            row = {"시나리오": res.scenario_id, "cap/RDC": f"{res.rdc_summary['capacity'].iloc[0]:.1f}"}
            rdc_load_new = [0.0] * eq_problem.n_rdc
            for i in range(eq_problem.n_sigungu):
                rdc_load_new[res.assignment[i]] += eq_problem.demand[i]
            for j, rn in enumerate(eq_problem.rdc_names):
                row[rn] = f"{rdc_load_new[j]:.1f} ({rdc_load_new[j]/total_demand*100:.1f}%)"
            row["시간 증가"] = f"+{res.cost_increase_pct}%"
            row["거리 증가"] = f"+{res.distance_increase_pct}%"
            row["이동 수"] = len(res.moved_detail)
            eq_summary_rows.append(row)

        st.dataframe(pd.DataFrame(eq_summary_rows), use_container_width=True, hide_index=True)

        # --- 시나리오 선택 ---
        st.divider()
        eq_sel = st.selectbox("시나리오 선택 (상세)", [r.scenario_id for r in eq_results], key="eq_sel")
        eq_sel_res = next(r for r in eq_results if r.scenario_id == eq_sel)

        # --- RDC별 물량 변화 ---
        st.subheader(f"RDC별 물량 변화 ({eq_sel})")

        eq_load_new = [0.0] * eq_problem.n_rdc
        for i in range(eq_problem.n_sigungu):
            eq_load_new[eq_sel_res.assignment[i]] += eq_problem.demand[i]

        fig_eq = go.Figure()
        fig_eq.add_trace(go.Bar(
            name="현재 운영", x=eq_problem.rdc_names,
            y=[round(v, 1) for v in eq_current_load],
            text=[f"{v:.1f} ({v/total_demand*100:.1f}%)" for v in eq_current_load],
            textposition="outside", marker_color="#636EFA",
        ))
        fig_eq.add_trace(go.Bar(
            name=eq_sel, x=eq_problem.rdc_names,
            y=[round(v, 1) for v in eq_load_new],
            text=[f"{v:.1f} ({v/total_demand*100:.1f}%)" for v in eq_load_new],
            textposition="outside", marker_color="#FF6B6B",
        ))
        fig_eq.update_layout(barmode="group", yaxis_title="수요 (3.5T 일평균)", height=400, margin=dict(t=30))
        st.plotly_chart(fig_eq, use_container_width=True)

        # --- 비교 지도 ---
        st.subheader(f"권역 비교 지도 (현재 vs {eq_sel})")

        eq_sigungu_master = pd.read_csv(DB_DIR / "sigungu_master.csv")

        CITY_CODE_MAP = {
            "11": "서울특별시", "21": "부산광역시", "22": "대구광역시", "23": "인천광역시",
            "24": "광주광역시", "25": "대전광역시", "26": "울산광역시", "29": "세종특별자치시",
            "31": "경기도", "32": "강원도", "33": "충청북도", "34": "충청남도",
            "35": "전라북도", "36": "전라남도", "37": "경상북도", "38": "경상남도", "39": "제주특별자치도",
        }
        rdc_color_dict_eq = {"평택RDC": "#636EFA", "칠곡RDC": "#EF553B", "계룡RDC": "#00CC96", "제천RDC": "#AB63FA", "중부RDC": "#19D3F3"}

        eq_gdf = gpd.read_file(RAW_DATA_DIR / "map" / "BND_SIGUNGU_PG.shp")
        eq_gdf = eq_gdf.to_crs(epsg=4326)
        eq_gdf["geometry"] = eq_gdf["geometry"].simplify(tolerance=0.001, preserve_topology=True)
        eq_gdf["광역도시"] = eq_gdf["SIGUNGU_CD"].str[:2].map(CITY_CODE_MAP)
        eq_gdf = eq_gdf.merge(
            eq_sigungu_master[["시군구", "광역도시", "sub_region_code"]],
            left_on=["광역도시", "SIGUNGU_NM"], right_on=["광역도시", "시군구"], how="left",
        )

        with open(DB_DIR / "rdc_locations.json", "r", encoding="utf-8") as f:
            eq_rdc_locs = json.load(f)

        def _eq_build_map(assignment_list, title, show_moved=False):
            detail_rows = []
            for i in range(eq_problem.n_sigungu):
                j = assignment_list[i]
                cur_j = eq_problem.current_rdc_idx[i]
                detail_rows.append({
                    "sub_region_code": eq_problem.sigungu_codes[i],
                    "assigned_rdc": eq_problem.rdc_names[j],
                    "moved": j != cur_j,
                })
            detail_df = pd.DataFrame(detail_rows)
            gdf_map = eq_gdf.copy()
            gdf_map = gdf_map.merge(detail_df, on="sub_region_code", how="left")
            gdf_map["fill_color"] = gdf_map["assigned_rdc"].map(rdc_color_dict_eq).fillna("#DDDDDD")
            m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="CartoDB positron")
            assigned = gdf_map[gdf_map["assigned_rdc"].notna()].copy()
            folium.GeoJson(
                assigned,
                style_function=lambda feature: {
                    "fillColor": feature["properties"]["fill_color"],
                    "color": "#FF0000" if show_moved and feature["properties"].get("moved") else "#333333",
                    "weight": 3 if show_moved and feature["properties"].get("moved") else 0.5,
                    "fillOpacity": 0.6,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["광역도시", "SIGUNGU_NM", "assigned_rdc"],
                    aliases=["광역도시:", "시군구:", "배정 RDC:"],
                    style="font-size:13px;",
                ),
                name=title,
            ).add_to(m)
            for rdc in eq_rdc_locs:
                if rdc["name"] == "제주RDC":
                    continue
                if not eq_jungbu and rdc["name"] == "중부RDC":
                    continue
                folium.Marker(
                    location=[rdc["lat"], rdc["lon"]],
                    tooltip=rdc["name"],
                    icon=folium.Icon(color="black", icon="star", prefix="fa"),
                ).add_to(m)
            return m.get_root().render()

        eq_col_l, eq_col_r = st.columns(2)
        with eq_col_l:
            st.caption("현재 운영")
            st_html(_eq_build_map(list(eq_problem.current_rdc_idx), "현재"), height=500)
        with eq_col_r:
            st.caption(f"{eq_sel} (균등화)")
            st_html(_eq_build_map(eq_sel_res.assignment, eq_sel, show_moved=True), height=500)

        if len(eq_sel_res.moved_detail) > 0:
            st.caption("※ 오른쪽 지도: 빨간 테두리 = 이동된 시군구")

        # --- 이동 상세 ---
        st.subheader(f"이동 상세 ({eq_sel})")

        if len(eq_sel_res.moved_detail) > 0:
            eq_moved = eq_sel_res.moved_detail[[
                "sigungu_name", "demand", "current_rdc", "assigned_rdc",
                "current_time", "assigned_time", "delta_time",
                "current_distance", "assigned_distance", "delta_distance",
            ]].copy()
            eq_moved.columns = [
                "시군구", "수요(3.5T)", "이전 RDC", "변경 RDC",
                "이전 시간(분)", "변경 시간(분)", "시간 증가(분)",
                "이전 거리(km)", "변경 거리(km)", "거리 증가(km)",
            ]
            eq_moved = eq_moved.sort_values("시간 증가(분)", ascending=False)
            st.dataframe(eq_moved, use_container_width=True, hide_index=True)
        else:
            st.info("이동 없음")

        # 핵심 분석
        st.divider()
        st.markdown(
            "#### 분석\n\n"
            "- **제천RDC**: 주변 시군구 수요가 적어 균등 분배 시에도 먼 곳에서 끌어와야 함 → 비용 급증\n"
            "- **평택 축소 방식이 더 효율적**: 같은 수준의 분산이면 이동시간 증가가 더 적음\n"
            "- **균등화의 가치**: '왜 완전 균등이 안 되는가'를 보여주는 근거로 활용"
        )
