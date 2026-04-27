"""Source acquisition metadata for first-wave pending metrics.

The records here document what has been verified from public source pages.  They
separate raw-first acquisition from API-refresh acquisition so implementation can
avoid premature API coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal


SourceKind = Literal["file", "api", "web-indicator"]
AuthMode = Literal["none", "service-key", "web-session-unknown"]


@dataclass(frozen=True)
class SourceAcquisitionSpec:
    metric_id: str
    purpose: Literal["raw-first", "api-refresh"]
    source_name: str
    url: str
    kind: SourceKind
    format: str
    auth: AuthMode
    verified_fields: tuple[str, ...]
    caveats: tuple[str, ...] = ()


FIRST_WAVE_SOURCE_ACQUISITION: Final[tuple[SourceAcquisitionSpec, ...]] = (
    SourceAcquisitionSpec(
        metric_id="student_recruitment",
        purpose="raw-first",
        source_name="교육부_대학알리미_대학주요정보_학생_교원_연구_재정_교육여건",
        url="https://www.data.go.kr/data/15118998/fileData.do",
        kind="file",
        format="XLSX",
        auth="none",
        verified_fields=(
            "공시년도",
            "학교명",
            "본분교명",
            "학교종류",
            "학교유형",
            "설립유형",
            "지역명",
            "입학정원(학부)",
            "재학생(학부)",
            "신입생경쟁률(학부)",
            "신입생 충원율(학부)",
        ),
        caveats=(
            "재학생 충원율은 이 XLSX 설명에서 직접 확인되지 않아 학생 현황 API/원자료 보강 필요.",
            "제공 URL은 academyinfo.go.kr 다운로드 화면으로 연결된다.",
            "실제 공개 화면 데이터 엔드포인트는 https://www.academyinfo.go.kr/main/main2130/selectSchlList.do 로 확인됨.",
        ),
    ),
    SourceAcquisitionSpec(
        metric_id="student_recruitment",
        purpose="api-refresh",
        source_name="한국대학교육협의회 대학정보공시 학생 현황",
        url="https://www.data.go.kr/data/15037346/openapi.do",
        kind="api",
        format="XML REST",
        auth="service-key",
        verified_fields=(
            "신입생 충원율",
            "재학생 충원율",
            "재학생수",
            "재적학생수",
            "졸업자 수",
            "취업자 수",
            "schlId",
            "svyYr",
        ),
        caveats=(
            "ServiceKey 필수.",
            "개발/운영 활용승인은 자동승인으로 표시됨.",
        ),
    ),
)


__all__ = [
    "FIRST_WAVE_SOURCE_ACQUISITION",
    "SourceAcquisitionSpec",
]
