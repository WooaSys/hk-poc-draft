# 자연권역 생성 및 시각화

- **작성시간**: 2026-04-02
- **주제**: 자연권역(Natural Territory) 생성 — 비용 최소 기준 RDC 배정 기준선

## 요약

각 시군구를 거리/시간 기준으로 가장 가까운 RDC에 배정한 "자연권역"을 생성한다. 자연권역은 최종 배정안이 아니라, 현재 권역 구조의 왜곡을 판단하고 재분배 방향을 설정하기 위한 기준선(reference layer)이다.

---

## 1. 자연권역의 정의

capacity, 운영 정책, 기존 배정 관성 등을 모두 제거하고, **"어느 RDC가 가장 빨리 도달 가능한가"만 기준**으로 만든 reference 권역.

각 시군구 i에 대해, 모든 RDC j 중에서 비용 c_ij가 가장 작은 RDC를 선택:

```
j*(i) = argmin_j c_ij    (c_ij = travel_time)
```

---

## 2. 자연권역을 만드는 이유

### (1) 현재 권역 구조의 왜곡 판단

현재 특정 RDC(평택)가 전체 물량의 40% 이상을 처리 중. 이것이 적정 수준인지 과부하인지는 현재 배정만으로 판단 어려움. 자연권역을 계산하면 "제약이 없다면 어느 RDC가 이 지역을 담당하는 것이 자연스러운가"를 확인 가능.

### (2) 재분배 방향 설정

- 자연권역보다 많이 맡고 있는 RDC → 줄여야 할 대상
- 자연권역보다 적게 맡고 있는 RDC → 늘릴 수 있는 대상

### (3) RDC별 capacity(상한선) 추정 기준

현재 RDC별 처리 상한을 모르는 상태에서, Current Load와 Natural Load를 함께 참고하여 상한선 추정.

### (4) 재할당 결과 평가 기준

최적화 결과를 자연권역 대비로 평가:
- 자연권역 대비 얼마나 개선되었는지
- 불필요하게 먼 RDC 배정이 줄었는지
- 특정 RDC 과부하가 해소되었는지

---

## 3. 자연권역의 역할

- 최종 배정안이 **아니다**
- solver에 강제로 넣는 제약조건이 **아니다**
- 현재 구조의 왜곡을 판단하는 **기준선**이다
- 재분배 방향과 capacity 추정에 사용하는 **reference layer**이다

전체 구조:
```
1. Current (현재 권역)
2. Natural (자연권역) ← 이번 작업
3. Optimized (재할당 결과, OR-Tools 기반) ← 추후
```

---

## 4. 설계

### 입력 데이터

| 데이터 | 파일 | 비고 |
|---|---|---|
| 시군구 수요 | `app/db/sigungu_demand.csv` | demand_3_5t, demand_5t |
| RDC→시군구 비용행렬 | `app/db/cost_matrix.csv` | duration_rank = 1이 자연권역 RDC |
| 현재 RDC 배정 | `app/db/shipto_master.csv` | 시군구별 수요 기준 최다 RDC |
| RDC 위치 | `app/db/rdc_locations.json` | |

### 생성 로직

1. `cost_matrix.csv`에서 `duration_rank = 1`인 행 추출 → 자연권역 RDC
2. `sigungu_demand.csv`에서 수요 병합
3. 현재 RDC 배정: `shipto_master.csv`에서 시군구별 수요 기준 최다 RDC 산출
4. 현재 vs 자연 비교

### 중부RDC 처리

- 중부RDC는 운영 초기(3건)로, 자연권역에 포함 시 9개 시군구가 배정됨
- 현실적으로 이 물량을 처리할 수 있는지는 별개 문제
- **체크박스로 중부RDC 포함/제외 선택 가능하도록 구현**

### 결과 테이블 구조

| 컬럼 | 설명 |
|---|---|
| `sub_region_code` | 시군구 코드 |
| `sigungu_name` | 시군구명 |
| `natural_rdc_code` | 자연권역 RDC 코드 |
| `natural_rdc_name` | 자연권역 RDC 명 |
| `natural_time` | 자연권역 RDC까지 소요시간 (분) |
| `natural_distance` | 자연권역 RDC까지 거리 (km) |
| `demand_3_5t` | 3.5T 환산 수요 |
| `demand_5t` | 5T 환산 수요 |
| `current_rdc_name` | 현재 담당 RDC (시군구 내 수요 최다 RDC) |
| `current_time` | 현재 RDC까지 소요시간 (분) |
| `time_gap` | current_time - natural_time (양수면 현재가 더 먼 배정) |

### Natural Load vs Current Load 비교

RDC별 집계:
- Natural Load = 자연권역 기준 배정 시군구의 수요 합
- Current Load = 현재 배정 기준 수요 합
- 차이 = 해당 RDC의 과부하/여유 정도

---

## 5. 시각화 위치

- 자료 분석 > **수요 분포** 탭 내 "참고사항" 섹션으로 배치
- 자연권역 지도 (시군구 폴리곤, 자연권역 RDC별 색상)
- RDC별 Natural Load vs Current Load 비교 차트
- 중부RDC 포함/제외 체크박스

---

## 6. 주의사항

- OR-Tools를 사용하지 않는다 — argmin 기반 단순 할당
- time 기준 우선 사용 (distance보다 travel_time)
- 현재 RDC는 시군구 내 **수요 기준 최다 RDC**로 결정 (복수 RDC 배정 52개 시군구 대응)
- 제주 제외
