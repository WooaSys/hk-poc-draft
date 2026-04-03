"""
배차 비용 비교 페이지 (cost_comparison.py)

목적:
    현 상태(baseline)와 재할당 시나리오의 VROOM 배차 결과를 비용으로 비교한다.
    baseline은 사전 계산된 파일을 사용하고, 시나리오는 실행 후 저장/재사용.

입력:
    - app/db/vroom_results/baseline.json (사전 계산)
    - stress_test 엔진 + vroom_engine

출력:
    - 비용 비교 차트, RDC별 비교, 차량 경로 상세
"""

import sys
import json

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
DB_DIR = APP_DIR / "db"
RESULTS_DIR = DB_DIR / "vroom_results"

sys.path.insert(0, str(APP_DIR / "01_preproc"))

st.header("배차 비용 비교")

st.caption(
    "※ 3.5T 단일 기준 VROOM 배차 결과입니다. 일평균 추정값이며 실제 운영과 차이가 있을 수 있습니다. "
    "시나리오 간 상대 비교 목적으로 활용하세요."
)

# =============================================================
# baseline 로드
# =============================================================
baseline_path = RESULTS_DIR / "baseline.json"
if not baseline_path.exists():
    st.error("baseline 결과가 없습니다. 먼저 baseline VROOM 배차를 실행해주세요.")
    st.stop()

with open(baseline_path, "r", encoding="utf-8") as f:
    baseline = json.load(f)

# =============================================================
# 시나리오 선택 + 실행
# =============================================================
st.subheader("시나리오 설정")

col_type1, col_type2 = st.columns(2)

with col_type1:
    use_reduce = st.checkbox("평택 축소", value=True, key="cost_use_reduce")
    if use_reduce:
        ratios_input = st.text_input(
            "축소율 리스트 (%)", value="5, 10, 15, 20",
            help="콤마로 구분", key="cost_ratios",
        )
        receiver_buffer = st.number_input(
            "수용 RDC 버퍼 (%)", min_value=100, max_value=200, value=120, step=5,
            key="cost_buffer",
        )

with col_type2:
    use_equal = st.checkbox("균등화", value=False, key="cost_use_equal")
    if use_equal:
        eq_buffers_input = st.text_input(
            "균등 버퍼 리스트 (%)", value="110, 120, 130",
            help="균등 몫 × 버퍼 = 각 RDC capacity", key="cost_eq_buffers",
        )

include_jungbu = st.checkbox("중부RDC 포함", value=False, key="cost_jungbu")

run_button = st.button("시나리오 실행", type="primary", use_container_width=True)

if run_button:
    if not use_reduce and not use_equal:
        st.error("시나리오 유형을 하나 이상 선택하세요.")
        st.stop()

    from stress_test.common import load_problem_data, create_scenarios, Scenario
    from stress_test.runner import run_stress_test
    from vroom_engine.runner import run_vroom_scenario

    with st.spinner("데이터 로드 중..."):
        problem = load_problem_data(include_jungbu=include_jungbu)

    stress_results = []

    # 평택 축소
    if use_reduce:
        try:
            ratios = sorted(set([int(r.strip()) / 100 for r in ratios_input.split(",") if r.strip()]))
        except ValueError:
            st.error("축소율 형식 오류")
            st.stop()

        with st.spinner("평택 축소 재할당 중..."):
            scenarios = create_scenarios(
                problem, target_rdc="평택RDC",
                reduction_ratios=ratios,
                receiver_buffer=receiver_buffer / 100,
            )
            reduce_results = run_stress_test(
                problem, scenarios, solver_type="cpsat", isolation_penalty=1.0,
            )
            stress_results.extend(reduce_results)

    # 균등화
    if use_equal:
        try:
            eq_buffers = sorted(set([int(b.strip()) / 100 for b in eq_buffers_input.split(",") if b.strip()]))
        except ValueError:
            st.error("버퍼 형식 오류")
            st.stop()

        total_demand = sum(problem.demand)
        equal_share = total_demand / problem.n_rdc

        eq_scenarios = []
        for buf in eq_buffers:
            cap = equal_share * buf
            caps = [cap] * problem.n_rdc
            eq_scenarios.append(Scenario(scenario_id=f"EQ_{int(buf*100)}", capacity=caps))

        with st.spinner("균등화 재할당 중..."):
            eq_results = run_stress_test(
                problem, eq_scenarios, solver_type="cpsat", isolation_penalty=1.0,
            )
            stress_results.extend(eq_results)

    # 시나리오별 VROOM 실행
    scenario_vroom_results = {}
    for res in stress_results:
        sid = res.scenario_id
        if sid.startswith("EQ_"):
            file_id = sid
        else:
            file_id = f"{sid}_buf{receiver_buffer if use_reduce else 0}"
        cache_path = RESULTS_DIR / f"{file_id}.json"

        # 캐시 확인
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                scenario_vroom_results[sid] = json.load(f)
            st.write(f"  {sid}: 캐시 사용")
        else:
            with st.spinner(f"{sid} VROOM 배차 중..."):
                # assignment → {sub_region_code: rdc_name} 매핑
                assignment_map = {}
                for i in range(problem.n_sigungu):
                    j = res.assignment[i]
                    assignment_map[problem.sigungu_codes[i]] = problem.rdc_names[j]

                vroom_result = run_vroom_scenario(
                    scenario_id=file_id,
                    assignment_map=assignment_map,
                    include_jungbu=include_jungbu,
                    save=True,
                )
                scenario_vroom_results[sid] = vroom_result

    st.session_state["cost_scenarios"] = scenario_vroom_results
    st.session_state["cost_stress_results"] = stress_results

# =============================================================
# 결과 표시
# =============================================================
if "cost_scenarios" not in st.session_state:
    # baseline만이라도 표시
    st.subheader("현 상태 (Baseline)")

    bl_total = baseline["total_cost"]
    st.metric("일평균 배송비용 (추정)", f"{bl_total / 10000:,.0f}만원")

    bl_rdc_df = pd.DataFrame([{
        "RDC": r["rdc_name"],
        "시군구": r["sigungu_count"],
        "차량": r["vehicle_count"],
        "경로": len(r["routes"]),
        "비용(만원)": round(r["total_cost"] / 10000),
    } for r in baseline["rdc_results"]])
    st.dataframe(bl_rdc_df, use_container_width=True, hide_index=True)
    st.info("시나리오를 설정하고 실행하면 비교 결과가 표시됩니다.")
    st.stop()

scenario_results = st.session_state["cost_scenarios"]

# --- 비용 비교 요약 ---
st.subheader("비용 비교 요약")

summary_rows = [{
    "시나리오": "현재 운영",
    "총 비용(만원)": round(baseline["total_cost"] / 10000),
    "차량 수": baseline["total_vehicles"],
    "경로 수": baseline["total_routes"],
    "비용 증감(만원)": 0,
    "증감율": "-",
}]

for sid, vr in scenario_results.items():
    diff = vr["total_cost"] - baseline["total_cost"]
    pct = diff / baseline["total_cost"] * 100
    summary_rows.append({
        "시나리오": sid,
        "총 비용(만원)": round(vr["total_cost"] / 10000),
        "차량 수": vr["total_vehicles"],
        "경로 수": vr["total_routes"],
        "비용 증감(만원)": round(diff / 10000),
        "증감율": f"{pct:+.1f}%",
    })

summary_df = pd.DataFrame(summary_rows)
st.dataframe(summary_df, use_container_width=True, hide_index=True)

# --- 비용 비교 차트 ---
fig_total = go.Figure()
fig_total.add_trace(go.Bar(
    x=[r["시나리오"] for r in summary_rows],
    y=[r["총 비용(만원)"] for r in summary_rows],
    text=[
        f"{r['총 비용(만원)']:,}만원" if r["시나리오"] == "현재 운영"
        else f"{r['총 비용(만원)']:,}만원 ({r['증감율']})"
        for r in summary_rows
    ],
    textposition="outside",
    marker_color=["#636EFA"] + ["#FF6B6B"] * len(scenario_results),
))
fig_total.update_layout(
    yaxis_title="일평균 배송비용 (만원)",
    height=400,
    margin=dict(t=30),
)
st.plotly_chart(fig_total, use_container_width=True)

# --- 시나리오 선택 → RDC별 비교 ---
st.divider()
sel_scenarios = st.multiselect(
    "시나리오 선택 (상세 비교, 복수 선택 가능)",
    options=list(scenario_results.keys()),
    default=[list(scenario_results.keys())[-1]],
)

if sel_scenarios:
    st.subheader(f"RDC별 비용 비교")

    bl_rdc = {r["rdc_name"]: r for r in baseline["rdc_results"]}
    all_rdcs = list(bl_rdc.keys())

    bar_colors = ["#636EFA", "#FF6B6B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3", "#FF97FF", "#FECB52"]

    fig_rdc = go.Figure()
    fig_rdc.add_trace(go.Bar(
        name="현재 운영",
        x=all_rdcs,
        y=[round(bl_rdc[r]["total_cost"] / 10000) for r in all_rdcs],
        text=[f"{round(bl_rdc[r]['total_cost'] / 10000):,}" for r in all_rdcs],
        textposition="outside",
        marker_color=bar_colors[0],
    ))
    for idx, sid in enumerate(sel_scenarios):
        sel_vroom = scenario_results[sid]
        sel_rdc = {r["rdc_name"]: r for r in sel_vroom["rdc_results"]}
        color = bar_colors[(idx + 1) % len(bar_colors)]
        fig_rdc.add_trace(go.Bar(
            name=sid,
            x=all_rdcs,
            y=[round(sel_rdc.get(r, {"total_cost": 0})["total_cost"] / 10000) for r in all_rdcs],
            text=[f"{round(sel_rdc.get(r, {'total_cost': 0})['total_cost'] / 10000):,}" for r in all_rdcs],
            textposition="outside",
            marker_color=color,
        ))
    fig_rdc.update_layout(
        barmode="group",
        yaxis_title="일평균 배송비용 (만원)",
        height=400,
        margin=dict(t=30),
    )
    st.plotly_chart(fig_rdc, use_container_width=True)

# --- 차량 경로 상세 ---
if sel_scenarios:
    st.subheader("차량 경로 상세")

    col_sc, col_rdc = st.columns(2)
    with col_sc:
        detail_scenario = st.selectbox("시나리오", options=sel_scenarios, key="cost_detail_sc")
    with col_rdc:
        detail_vroom = scenario_results[detail_scenario]
        detail_rdc = st.selectbox("RDC", options=[r["rdc_name"] for r in detail_vroom["rdc_results"]], key="cost_detail_rdc")

    sel_rdc_data = next(r for r in detail_vroom["rdc_results"] if r["rdc_name"] == detail_rdc)

    route_rows = []
    for route in sel_rdc_data["routes"]:
        route_rows.append({
            "차량": route["vehicle_id"],
            "방문 시군구": " → ".join(route["stops"]),
            "방문 수": route["stop_count"],
            "거리(km)": route["osrm_km"],
            "보정거리(km)": route["corrected_km"],
            "소요시간(분)": route["duration_min"],
            "적재율": f"{route['utilization']:.1%}",
            "비용(원)": f"{route['cost']:,}",
        })

    st.dataframe(pd.DataFrame(route_rows), use_container_width=True, hide_index=True)
    st.caption(f"unassigned: {sel_rdc_data['unassigned_count']}건")

# --- 실제 비용 vs 추정 비용 참고 ---
st.divider()
with st.expander("실제 비용 vs 추정 비용 비교 (참고)"):
    st.markdown(
        "#### 11월 실적 × 11월 단가표 기준 vs 3.5T 추정\n\n"
        "| 기준 | 일평균 | 비고 |\n"
        "|---|---:|---|\n"
        "| 실제 (전체 톤수) | 3,969만원 | 3PL 제외(단가표에 해당 톤수 없음), 11월 단가 적용 |\n"
        "| 추정 (3.5T only) | 4,590만원 | VROOM + 거리 보정 |\n"
        "| **차이** | **+621만원 (+16%)** | |\n\n"
        "#### 거리 보정\n\n"
        "VROOM은 시군구 대표좌표(시청) 간 거리만 계산하므로, 시군구 내부 배송지 순회 거리가 빠짐. "
        "실제 배송 실적의 `Distance by Shipment`와 비교하여 OSRM 거리 구간별 보정계수(1.22~1.82)를 적용.\n\n"
        "#### 차이 원인\n\n"
        "1. **톤수 혼합 효과**: 실제는 1T(저렴) + 5T(비쌈) 혼합, 3.5T는 중간 단가\n"
        "2. **거리 보정계수**: 구간별 보정계수가 과대 추정 가능\n"
        "3. **3PL 미포함**: 실제 비용에서 3PL 3,453건 비용 빠져 있음 (포함 시 실제가 더 높음)\n"
        "4. **배차 최적화 차이**: VROOM 경로와 실제 배차 경로가 다름\n\n"
        "#### 결론\n\n"
        "- 3.5T 추정값은 실제 대비 약 +16% 수준\n"
        "- 3PL 비용 미포함 고려 시 실제 차이는 더 작을 수 있음\n"
        "- **시나리오 간 상대 비교 목적으로는 충분한 정확도**"
    )
