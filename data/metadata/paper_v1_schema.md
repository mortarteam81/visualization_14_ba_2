# 논문실적 v1 Schema

## Source

- Source: 대학알리미 공시데이터 추이
- Item: `7-가. 전임교원의 연구실적_대학_전임교원 1인당 논문 실적(국내, 국제)`
- Raw file: `data/raw/academyinfo/paper/original/7-가. 전임교원의 연구실적_대학_전임교원 1인당 논문 실적(국내, 국제).xlsx`
- Candidate output: `data/conversion_outputs/academyinfo/paper/paper_2007_2024_candidate.csv`

## Candidate Columns

| Column | Meaning |
| --- | --- |
| `기준년도` | 논문실적 기준년도 |
| `학교명` | 학교명, 기본 분석 scope alias 기준으로 정규화 |
| `본분교명` | 본교/분교 구분 |
| `설립유형` | 국공립/사립 등 설립 유형 |
| `전임교원1인당논문실적(국내, 연구재단등재지(후보포함))` | 국내 연구재단 등재지 후보 포함 논문실적 / 전임교원 |
| `전임교원1인당논문실적(국제, SCI급/SCOPUS학술지)` | 국제 SCI급·SCOPUS 학술지 논문실적 / 전임교원 |

## Formula

- `전임교원1인당논문실적(국내, 연구재단등재지(후보포함)) = 논문실적(국내, 연구재단등재지(후보포함)) / 전임교원`
- `전임교원1인당논문실적(국제, SCI급/SCOPUS학술지) = 논문실적(국제, SCI급/SCOPUS학술지) / 전임교원`
- 대학알리미 원자료와 동일하게 소수점 4자리 half-up 반올림을 사용한다.

## Promotion Policy

이 schema는 후보 데이터 검증용이다. 운영 CSV인 `data/전임교원 논문실적.csv`는 자동 교체하지 않는다.
