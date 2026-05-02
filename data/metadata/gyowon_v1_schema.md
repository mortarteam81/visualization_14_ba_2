# 전임교원 확보율 v1 Schema

## Source

- Source: 대학알리미 공시데이터 추이
- Item: `6-나-(1). 전임교원 1인당 학생 수 및 전임교원 확보율_대학`
- Primary raw file: `data/raw/academyinfo/gyowon/original/6-나-(1). 전임교원 1인당 학생 수 및 전임교원 확보율_대학_전임교원 확보율(학생정원 기준, 재학생 기준).xlsx`
- Related raw file: `data/raw/academyinfo/gyowon/original/6-나-(1). 전임교원 1인당 학생 수 및 전임교원 확보율_대학_전임교원 확보율(학생정원 기준, 재학생 기준)_의학계열제외.xlsx`
- Candidate output: `data/conversion_outputs/academyinfo/gyowon/gyowon_2008_2025_candidate.csv`

## Candidate Columns

| Column | Meaning |
| --- | --- |
| `기준년도` | 전임교원 확보율 기준년도 |
| `학교명` | 학교명, 기본 분석 scope alias 기준으로 정규화 |
| `본분교명` | 본교/분교 구분 |
| `전임교원 확보율(학생정원 기준)` | 학생정원 기준 전임교원 확보율, 단위 % |
| `전임교원 확보율(재학생 기준)` | 재학생 기준 전임교원 확보율, 단위 % |

## Formula

- `전임교원 확보율(학생정원 기준) = 전임교원(학생정원 기준) / 교원법정정원(학생정원 기준) * 100`
- `전임교원 확보율(재학생 기준) = 전임교원(재학생 기준) / 교원법정정원(재학생기준) * 100`
- 대학알리미 원자료와 동일하게 소수점 2자리 half-up 반올림을 사용한다.

## Promotion Policy

이 schema는 후보 데이터 검증용이다. 운영 CSV인 `data/전임교원_확보율.csv`는 자동 교체하지 않는다.
