# VROOM 배차 비용 비교 작업 목록

- **작성시간**: 2026-04-03
- **주제**: VROOM 배차 엔진 + 현 상태 결과 저장 + 비교 페이지
- **참조 Plan**: `01_plan/11_vroom_cost_comparison.md`

## 요약

VROOM 엔진 구축 → 현 상태 배차 결과 저장 → 비교 페이지 구현.

## 작업 목록

- [ ] 1. `vroom_engine/vroom_client.py` — VROOM API 호출
- [ ] 2. `vroom_engine/cost_calculator.py` — 거리 보정 + 단가 적용
- [ ] 3. `vroom_engine/runner.py` — RDC별 배차 실행 + 결과 집계 + 파일 저장
- [ ] 4. 현 상태 baseline 배차 결과 생성 + 저장
- [ ] 5. 새 페이지 (`pages/cost_comparison.py`) + main.py 등록
- [ ] 6. 동작 확인
