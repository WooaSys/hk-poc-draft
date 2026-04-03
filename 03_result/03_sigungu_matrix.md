# 시군구 간 비용행렬 생성 결과

- **작성시간**: 2026-04-02
- **주제**: 시군구 × 시군구 OSRM 비용행렬 생성 완료
- **참조 Plan**: `01_plan/03_sigungu_matrix.md`
- **참조 Todo**: `02_todo/03_sigungu_matrix.md`

## 요약

OSRM 로컬 서버를 이용하여 247개 시군구 간 60,762쌍의 비용행렬을 생성 완료.

## 결과 파일

- `doc/wemeet/sigungu_matrix.csv` (60,762행)
- NULL 건: 0

## 거리 통계

| 항목 | 값 |
|---|---|
| 평균 | 216.3 km |
| 중앙값 | 216.9 km |
| 최소 | 1.6 km |
| 최대 | 640.3 km |

## 모듈

- `app/01_preproc/sigungu_matrix.py` — 재사용 가능한 모듈
