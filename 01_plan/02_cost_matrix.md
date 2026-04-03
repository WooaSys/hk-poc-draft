# OSRM 비용행렬 생성

- **작성시간**: 2026-04-02
- **주제**: RDC ↔ 시군구 간 OSRM 기반 거리/시간 비용행렬 생성

## 요약

로컬 OSRM 서버(port 5002)를 이용하여 육지 4개 RDC × 육지 247개 시군구 간 실제 도로 거리/시간을 산출하고, 시군구 기준 RDC 순위를 매긴 비용행렬을 생성한다. 제주(제주RDC + 제주 시군구)는 이번 범위에서 제외.

## 배경

- 기존 거리 계산: Haversine × 1.45 (직선 보정) → ±20% 오차
- OSRM: 실제 도로 네트워크 기반 → 정확한 거리/시간
- 용도: 권역 재배치 최적화 시 RDC-배송지 간 비용 기준

## 입력 데이터

| 데이터 | 파일 | 비고 |
|---|---|---|
| RDC 위치 (5개) | `app/db/rdc_locations.json` | 제주RDC 제외 (평택, 계룡, 제천, 칠곡, 중부) |
| 시군구 위치 (247개) | `doc/wemeet/sigungu_master.csv` | 제주 시군구 제외 |

## 출력

파일: `doc/wemeet/cost_matrix.csv`

| 컬럼 | 설명 |
|---|---|
| `rdc_code` | RDC Plant 코드 (예: 11R2) |
| `rdc_name` | RDC 명 (예: 평택RDC) |
| `sub_region_code` | 시군구 코드 (예: GWO_GR) |
| `sigungu_name` | 광역도시 + 시군구 (예: 강원도 강릉시) |
| `duration_min` | 소요시간 (분) |
| `distance_km` | 거리 (km) |
| `duration_rank` | 시군구 기준 시간 순위 (1=가장 가까운 RDC) |
| `distance_rank` | 시군구 기준 거리 순위 (1=가장 가까운 RDC) |

- 총 행 수: 247 × 5 = 1,235행
- rank는 동일 sub_region_code 내에서 오름차순 정렬

## 구현 방식

1. RDC 5개(제주RDC 제외), 시군구 247개(제주 시군구 제외) 좌표 로드
2. 각 RDC × 시군구 조합에 대해 OSRM route API 호출 (`http://localhost:5002/route/v1/driving/{lon1},{lat1};{lon2},{lat2}`)
3. response에서 `duration`(초→분), `distance`(m→km) 추출
4. sub_region_code 기준 그룹별 duration/distance 순위 부여
5. CSV 저장

## 기술 스택

- Python (requests, pandas)
- OSRM 로컬 서버 (localhost:5002)

## 주의사항

- OSRM 좌표 형식: `lon,lat` (경도,위도 순서)
- 제주 제외 (제주RDC + 제주 시군구 2개) — 제주는 제주RDC 고정, 도로 경로 없음
- 중부RDC 포함 (운영 초기이지만 비용행렬에는 포함)
- 1,235건 API 호출, 로컬 서버이므로 수 분 내 완료 예상
