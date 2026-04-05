# 제목: 배송 CSV 36개 컬럼 정의
- 작성시간: 2026-04-03 19:15:16 KST
- 주제: `배송 실적` 원본 CSV의 36개 컬럼명과 의미 정리

기준 파일: `raw_data/1.업체 공유용_배송 실적_2025년 2월 11월_20260317.csv`

| No | 컬럼명 | 의미(한글) | 비고 |
|---:|---|---|---|
| 1 | Shipment Making Date | 출하(Shipment) 생성일 |  |
| 2 | Actual G/I Date | 실제 G/I 일자 | G/I = Goods Issue |
| 3 | G/I Plant | G/I 기준 플랜트 코드 | 예: 11RC, 1120 |
| 4 | G/I Plant Name | G/I 기준 플랜트명 | 예: 계룡RDC, 대전공장 |
| 5 | Actual Plant | 실제 처리 플랜트 코드 |  |
| 6 | Actual Plant Name | 실제 처리 플랜트명 |  |
| 7 | DC | DC 구분 | CDC / RDC 구분 |
| 8 | Shipment Type | 출하 유형 코드 | 예: Z002 |
| 9 | Shipment Type Description | 출하 유형 설명 | 예: Delivery by truck |
| 10 | Shipment No. | 출하 번호 | Shipment 식별자 |
| 11 | Delivery No. | 딜리버리 번호 | Delivery 식별자 |
| 12 | Sold to party | 주문자 코드 | 원본 한글 주석 반영 |
| 13 | Ship-to party | 납품처(배송지) 코드 |  |
| 14 | Shipment Route | 권역 번호(루트) | 원본 한글 주석 반영 |
| 15 | Region Code by Ship to | 배송지 기준 리전 코드 | 원본 한글 주석 반영 |
| 16 | 광역도시 | 배송지 광역시/도 |  |
| 17 | 시군구 | 배송지 시군구 |  |
| 18 | Material | 자재(Material) 코드 | 제품 코드 |
| 19 | Line_1 | 라인 구분 1 | 예: PC/LT |
| 20 | Line_2 | 라인 구분 2 | PCR / LTR 구분 |
| 21 | Group | 제품 그룹 | 원본 한글 주석: 그룹 |
| 22 | Size | 타이어 규격 사이즈 | 원본 한글 주석: 사이즈 |
| 23 | Inch | 타이어 인치 | 원본 한글 주석: 인치 |
| 24 | Q'ty | 수량 | Quantity |
| 25 | Measurement by Material and Q'ty | 규격·수량 기반 메저 값(비중) | 원본 한글 주석: 쉽먼트 내 규격 수량의 메저(%) |
| 26 | Cost of Shipment | 운반비 | 원본 한글 주석: 기준 운반비 |
| 27 | Distance by Shipment | 운송 거리 | 원본 한글 주석: 기준 운반비 거리 |
| 28 | Type of Truck by shipment | 트럭 톤수/차종 | 원본 한글 주석: 트럭 톤 수 |
| 29 | Picking Start | 피킹 시작 일시 | 원본 한글 주석 반영 |
| 30 | Picking Ending | 피킹 종료 일시 | 원본 한글 주석 반영 |
| 31 | Loading Start | 상차 시작 일시 | 원본 한글 주석 반영 |
| 32 | Loading Ending | 상차 종료 일시 | 원본 한글 주석 반영 |
| 33 | Truck Gate In | 트럭 입차 일시 | 원본 한글 주석 반영 |
| 34 | Truck Gate Out | 트럭 출차 일시 | 원본 한글 주석 반영 |
| 35 | Real G/I | 기사 배송 시작 일시 | 원본 한글 주석 반영 |
| 36 | Arrival by Delivery | 딜리버리별 도착 일시 | 원본 한글 주석 반영 |

---

## 데이터 구조 (키 관계)

이 CSV의 1행은 **Shipment × Delivery × Material** 단위이다.

| 키 | 고유값 수 | 단위 | 의미 |
|---|---:|---|---|
| Shipment No. | 17,631 | 트럭 1대 | 같은 Shipment가 여러 행으로 반복 |
| Delivery No. | 98,043 | 배송지 1곳 | 같은 Delivery가 여러 행으로 반복 |
| Shipment + Delivery | 98,043 | 위와 동일 | Delivery는 Shipment에 종속 |
| Shipment + Delivery + Material | 329,219 | 거의 행 단위 | 일부 중복(20,786건) 존재 |

- **1 Shipment = 트럭 1대 출발** (여러 배송지를 순회할 수 있음)
- **1 Delivery = 배송지 1곳** (한 배송지에서 여러 SKU를 하차)
- **1 행 = 배송지 1곳 × 제품 1종**

→ Shipment 1건에 Delivery가 여러 개면 그 트럭이 여러 곳을 돌았다는 뜻이다.

---

## Sold to party / Ship-to party 관계

- **Ship-to → Sold to**: 항상 1:1 (Ship-to 하나는 반드시 Sold to 하나에만 속함)
- **Sold to → Ship-to**: 1:N (대부분 1:1이지만, 일부는 여러 Ship-to를 가짐)
- **Sold to = Ship-to 인 비율**: 57.6% (204,563 / 354,960행)

| Sold to 1개당 Ship-to 수 | 업체 수 |
|---|---:|
| 1개 (동일) | 2,316 (93.1%) |
| 2~5개 | 153 |
| 6~50개 | 19 |
| 428개 | 1 (코드 2516) |

→ **Sold to = 주문 법인(대리점 본사)**, **Ship-to = 실제 배송 장소**
- 대부분(93%)은 주문자 = 배송지가 같은 단일 매장
- 일부 대리점은 본사가 주문하고 여러 지점으로 배송받는 구조

---

참고:
- 원본 CSV는 1~3행에 메타/주석이 있고, 4행이 실제 영문 헤더입니다.
- 일부 컬럼 의미는 원본 3행의 한글 주석(`CDC,RDC 구분`, `주문자 코드` 등)을 기준으로 해석했습니다.
