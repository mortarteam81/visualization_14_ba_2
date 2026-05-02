# gyeolsan_v1 schema

## Source

- Source organization: 한국사학진흥재단
- Source system: 사학재정알리미 대학재정데이터
- Source URL: <https://uniarlimi.kasfo.or.kr/knowledge/data2Room>
- Raw files:
  - `data/raw/kasfo/gyeolsan/original/2015_2020_corporate_school_account_settlement.zip`
  - `data/raw/kasfo/gyeolsan/original/2021_corporate_school_account_settlement.xlsx`
  - `data/raw/kasfo/gyeolsan/original/2022_corporate_school_account_settlement.xlsx`
  - `data/raw/kasfo/gyeolsan/original/2023_corporate_school_account_settlement.xlsx`
  - `data/raw/kasfo/gyeolsan/original/2024_corporate_school_account_settlement.xlsx`
- Candidate output: `data/conversion_outputs/kasfo/gyeolsan/kasfo_gyeolsan_2015_2024_candidate.csv`
- Processing report: `data/validation/processing_reports/kasfo_gyeolsan.processing_report.json`
- Mismatch report: `data/validation/mismatch_reports/kasfo_gyeolsan.mismatch.csv`

## Candidate Columns

| Column | Description |
| --- | --- |
| `기준년도` | 회계연도에서 추출한 기준년도 |
| `학교명` | 학교명, 기본 분석 범위 alias는 canonical name으로 정규화 |
| `법인명` | 학교법인명 |
| `설립` | 설립 구분 |
| `학급` | 학교급 |
| `학종` | 학교종류 |
| `지역` | 소재 지역 |
| `회계` | `교비` 행만 사용 |
| `운영수입` | `2.운영수입[1086]`, 단위 천원 |
| `등록금수입` | `4.등록금수입[1002]`, 단위 천원 |
| `기부금수입` | `4.기부금수입[1035]`, 단위 천원 |
| `등록금비율` | `등록금수입 / 운영수입 * 100` |
| `기부금비율` | `기부금수입 / 운영수입 * 100` |
| `source_file_name` | 원자료 XLSX 또는 ZIP 내부 XLSX 파일명 |
| `source_sheet_name` | 사용한 자금계산서 sheet |

## Notes

- 이 schema는 후보 데이터 검증용이다. 운영 CSV인 `data/결산(22,23,24).csv`는 자동 교체하지 않는다.
- 업로드된 편람 산식 중 사립대 기준을 적용했다.
- `교비회계(등록금, 비등록금) 결산` 분리 파일은 단순 합산 시 내부 전입 등이 운영수입에 이중 반영될 수 있어 이번 산식 원천으로 사용하지 않는다.
