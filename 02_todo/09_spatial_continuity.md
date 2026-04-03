# 공간 연속성 제약 추가 작업 목록

- **작성시간**: 2026-04-03
- **주제**: 고립 방지 패널티 추가
- **참조 Plan**: `01_plan/09_spatial_continuity.md`

## 요약

sigungu_matrix에서 인접 리스트를 생성하고, 엔진에 고립 패널티를 추가한다.

## 작업 목록

- [ ] 1. common.py — 인접 리스트 생성 함수 + ProblemData에 추가
- [ ] 2. engine_cpsat.py — 패널티 항 추가
- [ ] 3. engine_scip.py — 패널티 항 추가
- [ ] 4. 화면에 패널티 on/off 옵션 추가
- [ ] 5. 검증 (철원군 고립 해소 확인)
