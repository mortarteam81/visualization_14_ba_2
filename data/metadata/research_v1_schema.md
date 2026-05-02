# 연구비 수혜 실적 v1 Schema

## Source

- Source: 대학알리미 공시데이터 추이
- Item: `12-가. 연구비 수혜 실적_대학_전임교원 1인당 연구비(교내, 교외)`
- Raw file: `data/raw/academyinfo/research/original/12-가. 연구비 수혜 실적_대학_전임교원 1인당 연구비(교내, 교외).xlsx`
- Candidate output: `data/conversion_outputs/academyinfo/research/research_2007_2024_candidate.csv`

## Candidate Columns

| Column | Meaning |
| --- | --- |
| `기준년도` | 연구비 실적 기준년도 |
| `학교명` | 학교명, 기본 분석 scope alias 기준으로 정규화 |
| `본분교명` | 본교/분교 구분 |
| `설립유형` | 국공립/사립 등 설립 유형 |
| `전임교원 1인당 연구비(교내)` | 교내 합계 / 전임교원수, 단위 천원 |
| `전임교원 1인당 연구비(교외)` | 교외 합계 / 전임교원수, 단위 천원 |

## Formula

- `전임교원 1인당 연구비(교내) = 교내 합계 / 전임교원수`
- `전임교원 1인당 연구비(교외) = 교외 합계 / 전임교원수`
- 대학알리미 원자료와 동일하게 소수점 1자리 half-up 반올림을 사용한다.

## Promotion Policy

이 schema는 후보 데이터 검증용이다. 운영 CSV인 `data/연구비_수혜실적.csv`는 자동 교체하지 않는다.
