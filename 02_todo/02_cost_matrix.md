# OSRM 비용행렬 생성 작업 목록

- **작성시간**: 2026-04-02
- **주제**: RDC ↔ 시군구 OSRM 비용행렬 생성
- **참조 Plan**: `01_plan/02_cost_matrix.md`

## 요약

OSRM 로컬 서버를 이용하여 5개 RDC × 247개 시군구 비용행렬을 생성하고 CSV로 저장한다.

## 작업 목록

- [ ] 1. 비용행렬 생성 모듈 작성 (`app/01_preproc/cost_matrix.py`)
  - RDC/시군구 데이터 로드 (제주 제외)
  - OSRM route API 호출
  - duration/distance 추출 + rank 부여
  - CSV 저장
- [ ] 2. 실행 및 결과 확인
- [ ] 3. 결과 문서 작성 (`03_result/`)
