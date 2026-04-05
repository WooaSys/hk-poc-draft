# 제목: RDC별 담당 권역 매핑
- 작성시간: 2026-04-06
- 주제: RDC 기준으로 담당 광역도시/시군구/Route/Region Code 정리 (지도 표시용)

기준 파일: `raw_data/1.업체 공유용_배송 실적_2025년 2월 11월_20260317.csv`

> 참고: 일부 Route에서 RDC가 겹치는 경우(10건)는 단발적 건으로 판단하여 메인 RDC 1개만 할당하였다. 상세는 `08_route_region_mapping.md` 참조.

---

## RDC별 담당 현황 요약

| RDC | 담당 광역도시 수 | 담당 시군구 수 | 담당 Route 수 | 행 수 |
|---|---:|---:|---:|---:|
| 평택RDC | 6 | 86 | 88 | 141,446 |
| 칠곡RDC | 5 | 64 | 74 | 108,736 |
| 계룡RDC | 7 | 61 | 63 | 72,193 |
| 제천RDC | 4 | 24 | 24 | 24,701 |
| 제주RDC | 1 | 2 | 2 | 7,883 |

---

## 평택RDC

### 강원도 (285건)

| 시군구 | Route | Region Code |
|---|---|---|
| 철원군 | KRD9B0 | CVA |

### 경기도 (74,995건)

| 시군구 | Route | Region Code |
|---|---|---|
| 가평군 | KRD800 | HEA |
| 고양시 덕양구 | KRD810 | FJA, FKA |
| 고양시 일산동구 | KRD811 | FJA |
| 고양시 일산서구 | KRD812 | FJA |
| 과천시 | KRD820 | FUA |
| 광명시 | KRD830 | FSA |
| 광주시 | KRD840 | GSA |
| 구리시 | KRD850 | HAA |
| 군포시 | KRD860 | GDA |
| 김포시 | KRD870 | FNA |
| 남양주시 | KRD880 | HBA |
| 동두천시 | KRD890 | HHA |
| 부천시 소사구 | KRD8A0 | FPA |
| 부천시 오정구 | KRD8A0 | FPA |
| 부천시 원미구 | KRD305 | FPA |
| 부천시 원미구 | KRD8A0 | FPA |
| 성남시 분당구 | KRD8B0 | ALA, GRA |
| 성남시 수정구 | KRD8B1 | GPA, GRA |
| 성남시 중원구 | KRD8B2 | GRA |
| 수원시 권선구 | KRD8C0 | GFA, GGA, GIA |
| 수원시 영통구 | KRD8C1 | GFA |
| 수원시 장안구 | KRD8C2 | GFA |
| 수원시 장안구 | KRD8D0 | GFA |
| 수원시 팔달구 | KRD8C3 | GFA |
| 시흥시 | KRD8D0 | BBA, FVA |
| 안산시 단원구 | KRD8E0 | FTA |
| 안산시 상록구 | KRD8E1 | FTA |
| 안성시 | KKR143 | GNA |
| 안성시 | KRD8F0 | EJA, GNA |
| 안양시 동안구 | KRD8G0 | GBA |
| 안양시 만안구 | KRD8G1 | GBA |
| 양주시 | KRD8H0 | HGA |
| 양평군 | KRD8I0 | HDA |
| 연천군 | KRD8K0 | HHA, HJA |
| 오산시 | KRD8L0 | GJA |
| 용인시 기흥구 | KRD8M0 | GFA, GIA, GJA, GKA |
| 용인시 수지구 | KRD8M1 | GKA |
| 용인시 처인구 | KRD8M0 | GKA |
| 용인시 처인구 | KRD8M2 | GIA, GKA |
| 의왕시 | KRD8N0 | GEA |
| 의정부시 | KRD8O0 | HFA |
| 파주시 | KRD8Q0 | FLA |
| 평택시 | KRD8R0 | GLA, GMA |
| 포천시 | KRD8S0 | HKA |
| 하남시 | KRD8T0 | GTA |
| 화성시 | KKR151 | GIA |
| 화성시 | KRD8U0 | GFA, GIA |

### 서울특별시 (32,790건)

| 시군구 | Route | Region Code |
|---|---|---|
| 강남구 | KRD000 | ALA, AOA |
| 강동구 | KRD001 | AKA |
| 강북구 | KRD002 | ARA |
| 강서구 | KRD003 | BAA |
| 관악구 | KRD004 | AUA |
| 광진구 | KRD005 | ASA |
| 구로구 | KRD006 | AVA |
| 금천구 | KRD007 | AWA |
| 노원구 | KRD008 | APA |
| 도봉구 | KRD009 | AIA |
| 동대문구 | KRD00A | AGA |
| 동작구 | KRD00B | AUA, AXA |
| 마포구 | KRD00C | AEA |
| 서대문구 | KRD00D | ADA |
| 서초구 | KRD00E | ANA |
| 성동구 | KRD00F | AJA |
| 성북구 | KRD00G | AMA |
| 송파구 | KRD00H | AOA |
| 양천구 | KRD00I | BBA |
| 영등포구 | KRD00J | ATA |
| 용산구 | KRD00K | AQA |
| 은평구 | KRD009 | AFA |
| 은평구 | KRD00L | AFA |
| 종로구 | KRD00M | ABA |
| 중구 | KRD00N | AAA |
| 중랑구 | KRD00G | AHA |
| 중랑구 | KRD00O | AHA |

### 인천광역시 (15,663건)

| 시군구 | Route | Region Code |
|---|---|---|
| 강화군 | KRD300 | FOA |
| 계양구 | KRD301 | FHA |
| 남동구 | KRD302 | FFA |
| 동구 | KRD303 | FBA |
| 동구 | KRD309 | FAA |
| 미추홀구 | KRD304 | FCA, FFA |
| 부평구 | KRD305 | FDA |
| 서구 | KRD306 | FEA, GIA |
| 연수구 | KRD307 | FGA |
| 중구 | KKR079 | FNA |
| 중구 | KRD309 | FAA, FNA |

### 충청남도 (14,748건)

| 시군구 | Route | Region Code |
|---|---|---|
| 당진시 | KRDB40 | DSA |
| 서산시 | KRDB70 | EEA |
| 아산시 | KRDB90 | DOA |
| 예산군 | KRDBA0 | DRA |
| 천안시 동남구 | KRDBB0 | DLA |
| 천안시 서북구 | KRDBB1 | DLA |
| 태안군 | KRDBD0 | EFA |
| 홍성군 | KRDBE0 | EAA |

### 충청북도 (2,965건)

| 시군구 | Route | Region Code |
|---|---|---|
| 음성군 | KRDA50 | ELA |
| 진천군 | KRDA80 | EJA |


## 칠곡RDC

### 경상남도 (33,473건)

| 시군구 | Route | Region Code |
|---|---|---|
| 거제시 | KRDF00 | 3, MLA, MLC, PIA |
| 거창군 | KRDF10 | MTA |
| 고성군 | KRDF20 | MGA |
| 김해시 | KRDF30 | LQA, LQG, LQH |
| 김해시 | KRDF80 | LQA |
| 남해군 | KRDF40 | MSA |
| 밀양시 | KRDF50 | LTA |
| 사천시 | KRDF60 | MNA, MPA |
| 산청군 | KRDF70 | MGA, MQA |
| 양산시 | KRDF80 | LKA, LSA, LSC |
| 의령군 | KRDF90 | MEA |
| 진주시 | KRDFA0 | MNA |
| 창녕군 | KRDFB0 | MDA |
| 창원시 마산합포구 | KRDFC0 | MBA, MHA |
| 창원시 마산회원구 | KRDFC1 | MAA, MHA |
| 창원시 성산구 | KRDFC2 | MHA |
| 창원시 성산구 | KRDFC3 | MHA |
| 창원시 의창구 | KRDFC3 | MAA, MBA, MHA |
| 창원시 진해구 | KRDFC4 | LKA, MHA, MIA |
| 통영시 | KRDFD0 | MJA |
| 하동군 | KRDFE0 | MRA |
| 함안군 | KRDFF0 | MFA |
| 함양군 | KRDFG0 | MUA |
| 합천군 | KRDFH0 | MVA |

### 경상북도 (26,116건)

| 시군구 | Route | Region Code |
|---|---|---|
| 경산시 | KRDE00 | C55, DSA, OIA |
| 경주시 | KRDE10 | PCA, PLA, PLB |
| 고령군 | KRDE20 | OLA |
| 구미시 | KRDE30 | OOA, OOB |
| 김천시 | KRDE50 | OPA |
| 문경시 | KRDE60 | OTA |
| 상주시 | KRDE80 | OOA, OQA |
| 성주군 | KRDE90 | ONA |
| 안동시 | KRDEA0 | PCA, PDA, POA |
| 영덕군 | KRDEB0 | PHA |
| 영양군 | KRDEC0 | PGA |
| 영천시 | KRDEE0 | PJA |
| 예천군 | KRDEF0 | PCA, PCB |
| 울릉군 | KRDEG0 | C84 |
| 울진군 | KRDEH0 | PIA |
| 의성군 | KRDEI0 | PIK |
| 청도군 | KRDEJ0 | OKA |
| 청송군 | KRDEK0 | PFA |
| 칠곡군 | KRDEL0 | OMA, OMC |
| 포항시 남구 | KRDEM0 | C84, MUA, NEA, PNA |
| 포항시 북구 | KRDEM1 | PNA, POA |

### 대구광역시 (21,936건)

| 시군구 | Route | Region Code |
|---|---|---|
| 군위군 | KRD208 | OKD |
| 남구 | KRD200 | OFA |
| 달서구 | KRD201 | OEA, OEH |
| 달성군 | KRD202 | OHA, OHD |
| 동구 | KRD203 | AOM, OBA, OBC |
| 북구 | KKR065 | ODA |
| 북구 | KRD204 | C75, C83, OCA |
| 북구 | KRD205 | OCA |
| 서구 | KKR065 | ODA |
| 서구 | KRD205 | ODA, OEA |
| 수성구 | KRD206 | OGA, OGC, OLA |
| 중구 | KRD207 | OAA |

### 부산광역시 (19,039건)

| 시군구 | Route | Region Code |
|---|---|---|
| 강서구 | KRD100 | LKA, LOA, LOD |
| 강서구 | KRD108 | LOA |
| 금정구 | KRD101 | LHA, LHC |
| 기장군 | KRD102 | 8, LPA |
| 남구 | KRD103 | LGA, LKA |
| 동구 | KRD104 | LBA |
| 동래구 | KRD105 | LFA |
| 부산진구 | KRD106 | LLA |
| 북구 | KRD107 | LMA |
| 사상구 | KRD108 | LCA, LNA |
| 사하구 | KRD109 | LDA, LDB |
| 서구 | KRD10A | LCA |
| 수영구 | KRD10B | LKA |
| 연제구 | KRD10C | LIA, LLA |
| 영도구 | KRD10D | LEA, LKA |
| 중구 | KRD10E | LAA |
| 해운대구 | KRD10F | LJA, LJD |

### 울산광역시 (8,172건)

| 시군구 | Route | Region Code |
|---|---|---|
| 남구 | KRD600 | NAA |
| 동구 | KRD601 | NCA, PHA |
| 북구 | KRD602 | NDA |
| 울주군 | KRD603 | NEA, NED, PHA |
| 중구 | KRD604 | NBA |


## 계룡RDC

### 광주광역시 (10,128건)

| 시군구 | Route | Region Code |
|---|---|---|
| 광산구 | KRD400 | DEA, IDA, IEA |
| 남구 | KRD401 | IDA |
| 동구 | KRD402 | IBA |
| 동구 | KRD403 | IBA |
| 북구 | KRD403 | IAA, IEA |
| 서구 | KRD404 | ICA |

### 대전광역시 (14,443건)

| 시군구 | Route | Region Code |
|---|---|---|
| 대덕구 | KRD500 | C61, DEA, DEF, DP |
| 대덕구 | KRDA91 | EHA |
| 동구 | KRD501 | DAA |
| 서구 | KRD502 | DCA, DCG |
| 유성구 | KRD503 | DAA, DDA, DDB, DDC |
| 중구 | KRD502 | DCA |
| 중구 | KRD504 | DBA |

### 세종특별자치시 (2,368건)

| 시군구 | Route | Region Code |
|---|---|---|
| 세종특별자치시 | KRD700 | DQA |

### 전라남도 (13,627건)

| 시군구 | Route | Region Code |
|---|---|---|
| 강진군 | KRDD00 | ABD |
| 고흥군 | KRDD10 | JHA |
| 광양시 | KRDD30 | JFA |
| 구례군 | KRDD40 | ADC, JBA |
| 나주시 | KRDD50 | ILA |
| 담양군 | KRDD60 | IIA |
| 목포시 | KRDD70 | DSA, IQA, IQH |
| 무안군 | KRDD80 | IRA |
| 보성군 | KRDD90 | JGA |
| 순천시 | KRDDA0 | C86, JAA, JAF |
| 여수시 | KRDDC0 | JIA, JJA |
| 영광군 | KRDDD0 | IFA |
| 영암군 | KRDDE0 | INB |
| 완도군 | KRDDF0 | IUA, IUB |
| 장성군 | KRDDG0 | C51, IGA |
| 장흥군 | KRDDH0 | IPA |
| 진도군 | KRDDI0 | IVA |
| 함평군 | KRDDJ0 | INA |
| 해남군 | KRDDK0 | ITA |
| 화순군 | KRDDL0 | IKA |

### 전라북도 (14,844건)

| 시군구 | Route | Region Code |
|---|---|---|
| 고창군 | KRDC00 | KCA |
| 군산시 | KRDC10 | JTA, JTC |
| 김제시 | KRDC20 | JVA |
| 남원시 | KRDC30 | KDA |
| 무주군 | KRDC40 | JQA |
| 부안군 | KRDC50 | JXA |
| 순창군 | KRDC60 | KFA |
| 완주군 | KRDC70 | JNA |
| 익산시 | KRDC80 | JRA |
| 임실군 | KRDC90 | JOA |
| 장수군 | KRDCA0 | KGA |
| 전주시 덕진구 | KRDCB0 | JMA |
| 전주시 완산구 | KRDCB1 | JLA, JMA |
| 정읍시 | KRDCC0 | KAA, MNA |
| 진안군 | KRDCD0 | JPA |

### 충청남도 (6,183건)

| 시군구 | Route | Region Code |
|---|---|---|
| 계룡시 | KRDB00 | ABB |
| 공주시 | KRD700 | DGA |
| 공주시 | KRDB10 | DGA |
| 금산군 | KRDB20 | DFA, DFE |
| 논산시 | KRDB30 | DIA, DIB |
| 보령시 | KRDB50 | EDA |
| 부여군 | KRDB60 | DJA |
| 서천군 | KRDB80 | DKA |
| 청양군 | KRDBC0 | DTA, DTB |

### 충청북도 (10,600건)

| 시군구 | Route | Region Code |
|---|---|---|
| 괴산군 | KRDA00 | EKA, EKE |
| 보은군 | KRDA20 | EOA |
| 영동군 | KRDA30 | EMA |
| 옥천군 | KRDA40 | ENA |
| 증평군 | KRDA70 | ABF, ELA |
| 청주시 상당구 | KRDA90 | EGA, EHA, EIA |
| 청주시 서원구 | KRDA91 | EHA, EIA |
| 청주시 청원구 | KRDA90 | EGA |
| 청주시 청원구 | KRDA92 | EGA, EHA, EIA, ELA |
| 청주시 청원구 | KRDA93 | EHA |
| 청주시 흥덕구 | KRDA93 | EHA, EIA |


## 제천RDC

### 강원도 (16,327건)

| 시군구 | Route | Region Code |
|---|---|---|
| 강릉시 | KRD900 | CCA |
| 강릉시 | KRD940 | CCA |
| 고성군 | KRD910 | CGB |
| 동해시 | KRD920 | CPA |
| 삼척시 | KRD930 | CQA |
| 속초시 | KRD940 | CFA, CMA |
| 양구군 | KRD950 | CUA |
| 양양군 | KRD960 | CEA |
| 영월군 | KRD970 | CLA |
| 원주시 | KRD980 | CIA |
| 인제군 | KRD990 | CTA |
| 정선군 | KRD9A0 | CNA |
| 춘천시 | KRD9C0 | CAA |
| 태백시 | KRD9D0 | COA |
| 평창군 | KRD9E0 | CFA, CMA, CMB |
| 홍천군 | KRD9F0 | CSA |
| 화천군 | KRD9G0 | CBA |
| 횡성군 | KRD9H0 | CKA |

### 경기도 (3,391건)

| 시군구 | Route | Region Code |
|---|---|---|
| 여주시 | KRD8J0 | GVA |
| 이천시 | KRD8P0 | GUA |

### 경상북도 (1,529건)

| 시군구 | Route | Region Code |
|---|---|---|
| 봉화군 | KRDE70 | PBA, PCA |
| 영주시 | KRDED0 | PAA |

### 충청북도 (3,454건)

| 시군구 | Route | Region Code |
|---|---|---|
| 단양군 | KRDA10 | ETA |
| 제천시 | KRDA60 | ERA |
| 충주시 | KRDAA0 | EPA |


## 제주RDC

### 제주특별자치도 (7,883건)

| 시군구 | Route | Region Code |
|---|---|---|
| 서귀포시 | KRDG00 | NFE, NFF, NFG |
| 제주시 | KRDG10 | C73, NFA, NFB, NFC, NFD |
