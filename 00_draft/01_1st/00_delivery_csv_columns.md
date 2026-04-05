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

참고:
- 원본 CSV는 1~3행에 메타/주석이 있고, 4행이 실제 영문 헤더입니다.
- 일부 컬럼 의미는 원본 3행의 한글 주석(`CDC,RDC 구분`, `주문자 코드` 등)을 기준으로 해석했습니다.
