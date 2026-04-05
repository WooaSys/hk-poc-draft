# 제목: Shipment Route / Region Code by Ship to 정리
- 작성시간: 2026-04-06
- 주제: 광역도시/시군구 기준으로 Shipment Route, Region Code, 담당 RDC 매핑 정리

기준 파일: `raw_data/1.업체 공유용_배송 실적_2025년 2월 11월_20260317.csv`

> 참고: 일부 Route에서 2~3개 RDC가 겹치는 경우가 있으나(10건), 모두 서브 RDC 비율이 극소량(대부분 1% 미만)이며 단발적/일시적 건으로 판단하여 **메인 RDC 1개만 할당**하였다.

### RDC 중복 배송 상세 (무시 근거)

| 시군구 | Route | 메인 RDC | 서브 RDC | 비고 |
|---|---|---|---|---|
| 충북 음성군 | KRDA50 | 평택 90% | 계룡 9%, 제천 2% | 유일한 3개 RDC |
| 강원 강릉시 | KRD900, KRD940 | 제천 94% | 평택 6% | Route 2개에 걸침 |
| 대전 대덕구 | KRD500, KRDA91 | 계룡 98% | 중부 2% | Route 2개에 걸침 |
| 강원 원주시 | KRD980 | 제천 99% | 평택 1% | |
| 충북 진천군 | KRDA80 | 평택 97% | 계룡 3% | |
| 경기 광명시 | KRD830 | 평택 99% | 중부 1% | |
| 충남 아산시 | KRDB90 | 평택 99.9% | 계룡 0.1% | |
| 충남 홍성군 | KRDBE0 | 평택 99.9% | 계룡 0.1% | |
| 강원 춘천시 | KRD9C0 | 제천 100% | 중부 0.0% | |
| 경북 봉화군 | KRDE70 | 제천 98% | 칠곡 2% | |

→ 음성군(9%)을 제외하면 서브 RDC 비율이 모두 3% 이하. 재고 부족 시 타 RDC 보충 등 예외 건으로 판단하여 분석에서 제외한다.

---

## 1) RDC별 담당 현황 요약

| RDC | 담당 Route 수 | 담당 시군구 수 | 행 수 |
|---|---:|---:|---:|
| 평택RDC | 88 | 86 | 141,446 |
| 칠곡RDC | 74 | 64 | 108,736 |
| 계룡RDC | 63 | 61 | 72,193 |
| 제천RDC | 24 | 24 | 24,701 |
| 제주RDC | 2 | 2 | 7,883 |

---

## 2) 광역도시 단위 요약

| 광역도시 | 시군구 수 | Route 수 | Region 수 | 담당 RDC | 행 수 |
|---|---:|---:|---:|---|---:|
| 경기도 | 44 | 45 | 38 | 평택RDC | 78,386 |
| 경상남도 | 22 | 22 | 28 | 칠곡RDC | 33,473 |
| 서울특별시 | 25 | 25 | 25 | 평택RDC | 32,790 |
| 경상북도 | 23 | 23 | 31 | 칠곡RDC | 27,645 |
| 대구광역시 | 9 | 10 | 17 | 칠곡RDC | 21,936 |
| 충청남도 | 16 | 17 | 18 | 평택RDC | 20,931 |
| 부산광역시 | 16 | 16 | 21 | 칠곡RDC | 19,039 |
| 충청북도 | 14 | 14 | 14 | 계룡RDC | 17,019 |
| 강원도 | 18 | 18 | 19 | 제천RDC | 16,612 |
| 인천광역시 | 9 | 10 | 11 | 평택RDC | 15,663 |
| 전라북도 | 15 | 15 | 17 | 계룡RDC | 14,844 |
| 대전광역시 | 5 | 6 | 12 | 계룡RDC | 14,443 |
| 전라남도 | 20 | 20 | 28 | 계룡RDC | 13,627 |
| 광주광역시 | 5 | 5 | 6 | 계룡RDC | 10,128 |
| 울산광역시 | 5 | 5 | 7 | 칠곡RDC | 8,172 |
| 제주특별자치도 | 2 | 2 | 8 | 제주RDC | 7,883 |
| 세종특별자치시 | 1 | 1 | 1 | 계룡RDC | 2,368 |

---

## 3) 전체 매핑표 (광역도시 > 시군구 > Route > Region Code > RDC)

### 강원도

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 강릉시 | KRD900 | CCA | 제천RDC |
| 강릉시 | KRD940 | CCA | 제천RDC |
| 고성군 | KRD910 | CGB | 제천RDC |
| 동해시 | KRD920 | CPA | 제천RDC |
| 삼척시 | KRD930 | CQA | 제천RDC |
| 속초시 | KRD940 | CFA, CMA | 제천RDC |
| 양구군 | KRD950 | CUA | 제천RDC |
| 양양군 | KRD960 | CEA | 제천RDC |
| 영월군 | KRD970 | CLA | 제천RDC |
| 원주시 | KRD980 | CIA | 제천RDC |
| 인제군 | KRD990 | CTA | 제천RDC |
| 정선군 | KRD9A0 | CNA | 제천RDC |
| 철원군 | KRD9B0 | CVA | 평택RDC |
| 춘천시 | KRD9C0 | CAA | 제천RDC |
| 태백시 | KRD9D0 | COA | 제천RDC |
| 평창군 | KRD9E0 | CFA, CMA, CMB | 제천RDC |
| 홍천군 | KRD9F0 | CSA | 제천RDC |
| 화천군 | KRD9G0 | CBA | 제천RDC |
| 횡성군 | KRD9H0 | CKA | 제천RDC |

### 경기도

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 가평군 | KRD800 | HEA | 평택RDC |
| 고양시 덕양구 | KRD810 | FJA, FKA | 평택RDC |
| 고양시 일산동구 | KRD811 | FJA | 평택RDC |
| 고양시 일산서구 | KRD812 | FJA | 평택RDC |
| 과천시 | KRD820 | FUA | 평택RDC |
| 광명시 | KRD830 | FSA | 평택RDC |
| 광주시 | KRD840 | GSA | 평택RDC |
| 구리시 | KRD850 | HAA | 평택RDC |
| 군포시 | KRD860 | GDA | 평택RDC |
| 김포시 | KRD870 | FNA | 평택RDC |
| 남양주시 | KRD880 | HBA | 평택RDC |
| 동두천시 | KRD890 | HHA | 평택RDC |
| 부천시 소사구 | KRD8A0 | FPA | 평택RDC |
| 부천시 오정구 | KRD8A0 | FPA | 평택RDC |
| 부천시 원미구 | KRD305 | FPA | 평택RDC |
| 부천시 원미구 | KRD8A0 | FPA | 평택RDC |
| 성남시 분당구 | KRD8B0 | ALA, GRA | 평택RDC |
| 성남시 수정구 | KRD8B1 | GPA, GRA | 평택RDC |
| 성남시 중원구 | KRD8B2 | GRA | 평택RDC |
| 수원시 권선구 | KRD8C0 | GFA, GGA, GIA | 평택RDC |
| 수원시 영통구 | KRD8C1 | GFA | 평택RDC |
| 수원시 장안구 | KRD8C2 | GFA | 평택RDC |
| 수원시 장안구 | KRD8D0 | GFA | 평택RDC |
| 수원시 팔달구 | KRD8C3 | GFA | 평택RDC |
| 시흥시 | KRD8D0 | BBA, FVA | 평택RDC |
| 안산시 단원구 | KRD8E0 | FTA | 평택RDC |
| 안산시 상록구 | KRD8E1 | FTA | 평택RDC |
| 안성시 | KKR143 | GNA | 평택RDC |
| 안성시 | KRD8F0 | EJA, GNA | 평택RDC |
| 안양시 동안구 | KRD8G0 | GBA | 평택RDC |
| 안양시 만안구 | KRD8G1 | GBA | 평택RDC |
| 양주시 | KRD8H0 | HGA | 평택RDC |
| 양평군 | KRD8I0 | HDA | 평택RDC |
| 여주시 | KRD8J0 | GVA | 제천RDC |
| 연천군 | KRD8K0 | HHA, HJA | 평택RDC |
| 오산시 | KRD8L0 | GJA | 평택RDC |
| 용인시 기흥구 | KRD8M0 | GFA, GIA, GJA, GKA | 평택RDC |
| 용인시 수지구 | KRD8M1 | GKA | 평택RDC |
| 용인시 처인구 | KRD8M0 | GKA | 평택RDC |
| 용인시 처인구 | KRD8M2 | GIA, GKA | 평택RDC |
| 의왕시 | KRD8N0 | GEA | 평택RDC |
| 의정부시 | KRD8O0 | HFA | 평택RDC |
| 이천시 | KRD8P0 | GUA | 제천RDC |
| 파주시 | KRD8Q0 | FLA | 평택RDC |
| 평택시 | KRD8R0 | GLA, GMA | 평택RDC |
| 포천시 | KRD8S0 | HKA | 평택RDC |
| 하남시 | KRD8T0 | GTA | 평택RDC |
| 화성시 | KKR151 | GIA | 평택RDC |
| 화성시 | KRD8U0 | GFA, GIA | 평택RDC |

### 경상남도

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 거제시 | KRDF00 | 3, MLA, MLC, PIA | 칠곡RDC |
| 거창군 | KRDF10 | MTA | 칠곡RDC |
| 고성군 | KRDF20 | MGA | 칠곡RDC |
| 김해시 | KRDF30 | LQA, LQG, LQH | 칠곡RDC |
| 김해시 | KRDF80 | LQA | 칠곡RDC |
| 남해군 | KRDF40 | MSA | 칠곡RDC |
| 밀양시 | KRDF50 | LTA | 칠곡RDC |
| 사천시 | KRDF60 | MNA, MPA | 칠곡RDC |
| 산청군 | KRDF70 | MGA, MQA | 칠곡RDC |
| 양산시 | KRDF80 | LKA, LSA, LSC | 칠곡RDC |
| 의령군 | KRDF90 | MEA | 칠곡RDC |
| 진주시 | KRDFA0 | MNA | 칠곡RDC |
| 창녕군 | KRDFB0 | MDA | 칠곡RDC |
| 창원시 마산합포구 | KRDFC0 | MBA, MHA | 칠곡RDC |
| 창원시 마산회원구 | KRDFC1 | MAA, MHA | 칠곡RDC |
| 창원시 성산구 | KRDFC2 | MHA | 칠곡RDC |
| 창원시 성산구 | KRDFC3 | MHA | 칠곡RDC |
| 창원시 의창구 | KRDFC3 | MAA, MBA, MHA | 칠곡RDC |
| 창원시 진해구 | KRDFC4 | LKA, MHA, MIA | 칠곡RDC |
| 통영시 | KRDFD0 | MJA | 칠곡RDC |
| 하동군 | KRDFE0 | MRA | 칠곡RDC |
| 함안군 | KRDFF0 | MFA | 칠곡RDC |
| 함양군 | KRDFG0 | MUA | 칠곡RDC |
| 합천군 | KRDFH0 | MVA | 칠곡RDC |

### 경상북도

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 경산시 | KRDE00 | C55, DSA, OIA | 칠곡RDC |
| 경주시 | KRDE10 | PCA, PLA, PLB | 칠곡RDC |
| 고령군 | KRDE20 | OLA | 칠곡RDC |
| 구미시 | KRDE30 | OOA, OOB | 칠곡RDC |
| 김천시 | KRDE50 | OPA | 칠곡RDC |
| 문경시 | KRDE60 | OTA | 칠곡RDC |
| 봉화군 | KRDE70 | PBA, PCA | 제천RDC |
| 상주시 | KRDE80 | OOA, OQA | 칠곡RDC |
| 성주군 | KRDE90 | ONA | 칠곡RDC |
| 안동시 | KRDEA0 | PCA, PDA, POA | 칠곡RDC |
| 영덕군 | KRDEB0 | PHA | 칠곡RDC |
| 영양군 | KRDEC0 | PGA | 칠곡RDC |
| 영주시 | KRDED0 | PAA | 제천RDC |
| 영천시 | KRDEE0 | PJA | 칠곡RDC |
| 예천군 | KRDEF0 | PCA, PCB | 칠곡RDC |
| 울릉군 | KRDEG0 | C84 | 칠곡RDC |
| 울진군 | KRDEH0 | PIA | 칠곡RDC |
| 의성군 | KRDEI0 | PIK | 칠곡RDC |
| 청도군 | KRDEJ0 | OKA | 칠곡RDC |
| 청송군 | KRDEK0 | PFA | 칠곡RDC |
| 칠곡군 | KRDEL0 | OMA, OMC | 칠곡RDC |
| 포항시 남구 | KRDEM0 | C84, MUA, NEA, PNA | 칠곡RDC |
| 포항시 북구 | KRDEM1 | PNA, POA | 칠곡RDC |

### 광주광역시

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 광산구 | KRD400 | DEA, IDA, IEA | 계룡RDC |
| 남구 | KRD401 | IDA | 계룡RDC |
| 동구 | KRD402 | IBA | 계룡RDC |
| 동구 | KRD403 | IBA | 계룡RDC |
| 북구 | KRD403 | IAA, IEA | 계룡RDC |
| 서구 | KRD404 | ICA | 계룡RDC |

### 대구광역시

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 군위군 | KRD208 | OKD | 칠곡RDC |
| 남구 | KRD200 | OFA | 칠곡RDC |
| 달서구 | KRD201 | OEA, OEH | 칠곡RDC |
| 달성군 | KRD202 | OHA, OHD | 칠곡RDC |
| 동구 | KRD203 | AOM, OBA, OBC | 칠곡RDC |
| 북구 | KKR065 | ODA | 칠곡RDC |
| 북구 | KRD204 | C75, C83, OCA | 칠곡RDC |
| 북구 | KRD205 | OCA | 칠곡RDC |
| 서구 | KKR065 | ODA | 칠곡RDC |
| 서구 | KRD205 | ODA, OEA | 칠곡RDC |
| 수성구 | KRD206 | OGA, OGC, OLA | 칠곡RDC |
| 중구 | KRD207 | OAA | 칠곡RDC |

### 대전광역시

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 대덕구 | KRD500 | C61, DEA, DEF, DP | 계룡RDC |
| 대덕구 | KRDA91 | EHA | 계룡RDC |
| 동구 | KRD501 | DAA | 계룡RDC |
| 서구 | KRD502 | DCA, DCG | 계룡RDC |
| 유성구 | KRD503 | DAA, DDA, DDB, DDC | 계룡RDC |
| 중구 | KRD502 | DCA | 계룡RDC |
| 중구 | KRD504 | DBA | 계룡RDC |

### 부산광역시

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 강서구 | KRD100 | LKA, LOA, LOD | 칠곡RDC |
| 강서구 | KRD108 | LOA | 칠곡RDC |
| 금정구 | KRD101 | LHA, LHC | 칠곡RDC |
| 기장군 | KRD102 | 8, LPA | 칠곡RDC |
| 남구 | KRD103 | LGA, LKA | 칠곡RDC |
| 동구 | KRD104 | LBA | 칠곡RDC |
| 동래구 | KRD105 | LFA | 칠곡RDC |
| 부산진구 | KRD106 | LLA | 칠곡RDC |
| 북구 | KRD107 | LMA | 칠곡RDC |
| 사상구 | KRD108 | LCA, LNA | 칠곡RDC |
| 사하구 | KRD109 | LDA, LDB | 칠곡RDC |
| 서구 | KRD10A | LCA | 칠곡RDC |
| 수영구 | KRD10B | LKA | 칠곡RDC |
| 연제구 | KRD10C | LIA, LLA | 칠곡RDC |
| 영도구 | KRD10D | LEA, LKA | 칠곡RDC |
| 중구 | KRD10E | LAA | 칠곡RDC |
| 해운대구 | KRD10F | LJA, LJD | 칠곡RDC |

### 서울특별시

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 강남구 | KRD000 | ALA, AOA | 평택RDC |
| 강동구 | KRD001 | AKA | 평택RDC |
| 강북구 | KRD002 | ARA | 평택RDC |
| 강서구 | KRD003 | BAA | 평택RDC |
| 관악구 | KRD004 | AUA | 평택RDC |
| 광진구 | KRD005 | ASA | 평택RDC |
| 구로구 | KRD006 | AVA | 평택RDC |
| 금천구 | KRD007 | AWA | 평택RDC |
| 노원구 | KRD008 | APA | 평택RDC |
| 도봉구 | KRD009 | AIA | 평택RDC |
| 동대문구 | KRD00A | AGA | 평택RDC |
| 동작구 | KRD00B | AUA, AXA | 평택RDC |
| 마포구 | KRD00C | AEA | 평택RDC |
| 서대문구 | KRD00D | ADA | 평택RDC |
| 서초구 | KRD00E | ANA | 평택RDC |
| 성동구 | KRD00F | AJA | 평택RDC |
| 성북구 | KRD00G | AMA | 평택RDC |
| 송파구 | KRD00H | AOA | 평택RDC |
| 양천구 | KRD00I | BBA | 평택RDC |
| 영등포구 | KRD00J | ATA | 평택RDC |
| 용산구 | KRD00K | AQA | 평택RDC |
| 은평구 | KRD009 | AFA | 평택RDC |
| 은평구 | KRD00L | AFA | 평택RDC |
| 종로구 | KRD00M | ABA | 평택RDC |
| 중구 | KRD00N | AAA | 평택RDC |
| 중랑구 | KRD00G | AHA | 평택RDC |
| 중랑구 | KRD00O | AHA | 평택RDC |

### 세종특별자치시

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 세종특별자치시 | KRD700 | DQA | 계룡RDC |

### 울산광역시

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 남구 | KRD600 | NAA | 칠곡RDC |
| 동구 | KRD601 | NCA, PHA | 칠곡RDC |
| 북구 | KRD602 | NDA | 칠곡RDC |
| 울주군 | KRD603 | NEA, NED, PHA | 칠곡RDC |
| 중구 | KRD604 | NBA | 칠곡RDC |

### 인천광역시

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 강화군 | KRD300 | FOA | 평택RDC |
| 계양구 | KRD301 | FHA | 평택RDC |
| 남동구 | KRD302 | FFA | 평택RDC |
| 동구 | KRD303 | FBA | 평택RDC |
| 동구 | KRD309 | FAA | 평택RDC |
| 미추홀구 | KRD304 | FCA, FFA | 평택RDC |
| 부평구 | KRD305 | FDA | 평택RDC |
| 서구 | KRD306 | FEA, GIA | 평택RDC |
| 연수구 | KRD307 | FGA | 평택RDC |
| 중구 | KKR079 | FNA | 평택RDC |
| 중구 | KRD309 | FAA, FNA | 평택RDC |

### 전라남도

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 강진군 | KRDD00 | ABD | 계룡RDC |
| 고흥군 | KRDD10 | JHA | 계룡RDC |
| 광양시 | KRDD30 | JFA | 계룡RDC |
| 구례군 | KRDD40 | ADC, JBA | 계룡RDC |
| 나주시 | KRDD50 | ILA | 계룡RDC |
| 담양군 | KRDD60 | IIA | 계룡RDC |
| 목포시 | KRDD70 | DSA, IQA, IQH | 계룡RDC |
| 무안군 | KRDD80 | IRA | 계룡RDC |
| 보성군 | KRDD90 | JGA | 계룡RDC |
| 순천시 | KRDDA0 | C86, JAA, JAF | 계룡RDC |
| 여수시 | KRDDC0 | JIA, JJA | 계룡RDC |
| 영광군 | KRDDD0 | IFA | 계룡RDC |
| 영암군 | KRDDE0 | INB | 계룡RDC |
| 완도군 | KRDDF0 | IUA, IUB | 계룡RDC |
| 장성군 | KRDDG0 | C51, IGA | 계룡RDC |
| 장흥군 | KRDDH0 | IPA | 계룡RDC |
| 진도군 | KRDDI0 | IVA | 계룡RDC |
| 함평군 | KRDDJ0 | INA | 계룡RDC |
| 해남군 | KRDDK0 | ITA | 계룡RDC |
| 화순군 | KRDDL0 | IKA | 계룡RDC |

### 전라북도

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 고창군 | KRDC00 | KCA | 계룡RDC |
| 군산시 | KRDC10 | JTA, JTC | 계룡RDC |
| 김제시 | KRDC20 | JVA | 계룡RDC |
| 남원시 | KRDC30 | KDA | 계룡RDC |
| 무주군 | KRDC40 | JQA | 계룡RDC |
| 부안군 | KRDC50 | JXA | 계룡RDC |
| 순창군 | KRDC60 | KFA | 계룡RDC |
| 완주군 | KRDC70 | JNA | 계룡RDC |
| 익산시 | KRDC80 | JRA | 계룡RDC |
| 임실군 | KRDC90 | JOA | 계룡RDC |
| 장수군 | KRDCA0 | KGA | 계룡RDC |
| 전주시 덕진구 | KRDCB0 | JMA | 계룡RDC |
| 전주시 완산구 | KRDCB1 | JLA, JMA | 계룡RDC |
| 정읍시 | KRDCC0 | KAA, MNA | 계룡RDC |
| 진안군 | KRDCD0 | JPA | 계룡RDC |

### 제주특별자치도

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 서귀포시 | KRDG00 | NFE, NFF, NFG | 제주RDC |
| 제주시 | KRDG10 | C73, NFA, NFB, NFC, NFD | 제주RDC |

### 충청남도

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 계룡시 | KRDB00 | ABB | 계룡RDC |
| 공주시 | KRD700 | DGA | 계룡RDC |
| 공주시 | KRDB10 | DGA | 계룡RDC |
| 금산군 | KRDB20 | DFA, DFE | 계룡RDC |
| 논산시 | KRDB30 | DIA, DIB | 계룡RDC |
| 당진시 | KRDB40 | DSA | 평택RDC |
| 보령시 | KRDB50 | EDA | 계룡RDC |
| 부여군 | KRDB60 | DJA | 계룡RDC |
| 서산시 | KRDB70 | EEA | 평택RDC |
| 서천군 | KRDB80 | DKA | 계룡RDC |
| 아산시 | KRDB90 | DOA | 평택RDC |
| 예산군 | KRDBA0 | DRA | 평택RDC |
| 천안시 동남구 | KRDBB0 | DLA | 평택RDC |
| 천안시 서북구 | KRDBB1 | DLA | 평택RDC |
| 청양군 | KRDBC0 | DTA, DTB | 계룡RDC |
| 태안군 | KRDBD0 | EFA | 평택RDC |
| 홍성군 | KRDBE0 | EAA | 평택RDC |

### 충청북도

| 시군구 | Route | Region Code | RDC |
|---|---|---|---|
| 괴산군 | KRDA00 | EKA, EKE | 계룡RDC |
| 단양군 | KRDA10 | ETA | 제천RDC |
| 보은군 | KRDA20 | EOA | 계룡RDC |
| 영동군 | KRDA30 | EMA | 계룡RDC |
| 옥천군 | KRDA40 | ENA | 계룡RDC |
| 음성군 | KRDA50 | ELA | 평택RDC |
| 제천시 | KRDA60 | ERA | 제천RDC |
| 증평군 | KRDA70 | ABF, ELA | 계룡RDC |
| 진천군 | KRDA80 | EJA | 평택RDC |
| 청주시 상당구 | KRDA90 | EGA, EHA, EIA | 계룡RDC |
| 청주시 서원구 | KRDA91 | EHA, EIA | 계룡RDC |
| 청주시 청원구 | KRDA90 | EGA | 계룡RDC |
| 청주시 청원구 | KRDA92 | EGA, EHA, EIA, ELA | 계룡RDC |
| 청주시 청원구 | KRDA93 | EHA | 계룡RDC |
| 청주시 흥덕구 | KRDA93 | EHA, EIA | 계룡RDC |
| 충주시 | KRDAA0 | EPA | 제천RDC |
