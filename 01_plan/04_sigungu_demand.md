# 시군구별 차량 환산 수요 산출

- **작성시간**: 2026-04-02
- **주제**: 시군구(sub_region_code) 단위 3.5T / 5T 차량 환산 물량 산출

## 요약

배송 실적 데이터에서 시군구별로 3.5T, 5T 기준 차량 환산 수요를 산출한다. 각 배송처가 데이터 기간 동안 몇 대 분량의 차량 부담을 만드는지 파악하는 것이 목적.

## 왜 3.5T와 5T 기준인가

- 타이어의 정확한 CBM(부피) 데이터를 보유하고 있지 않음
- 대신 배송 실적의 `Measurement by Material and Q'ty` 컬럼이 트럭별 적재율(%)을 제공
- 이 값과 수량으로부터 역산한 `1본당 적재율(%)`이 사이즈 × 트럭 조합별 고정값(CV 2.3%)임을 확인
- 따라서 CBM 없이도 "이 사이즈 타이어 N본이 트럭 한 대의 몇 %를 차지하는가"를 알 수 있음
- 3.5T: 전체 자체 차량의 54%, 모든 RDC 공통 주력 → 비교 기준으로 가장 적합
- 5T: 전체의 32%, 두 번째 주력 → 3.5T와 병행하면 실제 운영에 더 가까운 수요 파악 가능
- 즉, CBM을 모르지만 **트럭 적재율 기반 환산**으로 수요를 측정하는 방식

## 산출 방식

1. 배송 실적의 각 row에서 Size, Q'ty 확인
2. 적재 기준표에서 해당 Size의 3.5T_1본당%, 5T_1본당% 조회
3. `수량 × 1본당% ÷ 100` = 해당 row의 트럭 환산 대수
4. Ship-to party → sub_region_code 매핑 (shipto_master.csv)
5. sub_region_code별 합산

## 입력 데이터

| 데이터 | 파일 | 비고 |
|---|---|---|
| 배송 실적 | `raw_data/1.업체 공유용_배송 실적_*.csv` | Size, Q'ty, Region Code 등 |
| 적재 기준표 | `00_draft/타이어사이즈별_적재기준표.csv` | 사이즈별 3.5T_1본당%, 5T_1본당% |
| Ship-to 매핑 | `doc/wemeet/shipto_master.csv` | Ship-to party → sub_region_code |
| 시군구 마스터 | `doc/wemeet/sigungu_master.csv` | sub_region_code, 광역도시, 시군구 |

## 출력

파일: `doc/wemeet/sigungu_demand.csv`

| 컬럼 | 설명 |
|---|---|
| `sub_region_code` | 시군구 코드 |
| `sigungu_name` | 광역도시 + 시군구 |
| `total_qty` | 총 수량 (본) |
| `shipment_count` | 총 shipment 수 |
| `demand_3_5t` | 3.5T 환산 대수 (기간 합계) |
| `demand_5t` | 5T 환산 대수 (기간 합계) |
| `daily_demand_3_5t` | 3.5T 일평균 환산 대수 |
| `daily_demand_5t` | 5T 일평균 환산 대수 |
| `delivery_days` | 배송 발생 일수 |

## 주의사항

- 적재 기준표에 없는 사이즈는 환산 불가 → 해당 건수/비율 확인 필요
- 제주 제외
- 3PL 물량 포함 — 배송된 것이므로 배송처의 물량으로 집계
