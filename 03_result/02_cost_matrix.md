# OSRM 비용행렬 생성 결과

- **작성시간**: 2026-04-02
- **주제**: RDC ↔ 시군구 OSRM 비용행렬 생성 완료
- **참조 Plan**: `01_plan/02_cost_matrix.md`
- **참조 Todo**: `02_todo/02_cost_matrix.md`

## 요약

OSRM 로컬 서버를 이용하여 5개 RDC × 247개 시군구 = 1,235건의 비용행렬을 생성 완료.

## 결과 파일

- `doc/wemeet/cost_matrix.csv` (1,235행)
- NULL 건: 0

## 시간 기준 최적 RDC 분포 (duration_rank = 1)

| RDC | 최적 시군구 수 |
|---|---:|
| 평택RDC | 90 |
| 칠곡RDC | 69 |
| 계룡RDC | 53 |
| 제천RDC | 26 |
| 중부RDC | 9 |

## 모듈

- `app/01_preproc/cost_matrix.py` — 재사용 가능한 모듈
- 파라미터: OSRM 서버 주소, RDC 필터, 시군구 제외 등 지원
