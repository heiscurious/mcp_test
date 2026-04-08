"""공모사업 공고 수집 MCP 서버.

중소기업을 위한 공모사업/지원사업 공고를 기관별로 수집하고 정리합니다.
새 기관 추가: scrapers/ 디렉토리에 BaseScraper를 상속한 스크래퍼를 만들고 SCRAPERS에 등록하면 됩니다.
"""

from mcp.server.fastmcp import FastMCP
from scrapers.base import BaseScraper
from scrapers.nia import NIAScraper

# ──────────────────────────────────────────────
# 기관 스크래퍼 레지스트리 — 새 기관 추가 시 여기에 등록
# ──────────────────────────────────────────────
SCRAPERS: dict[str, BaseScraper] = {
    "nia": NIAScraper(),
    # 예시: "kised": KISEDScraper(),
    # 예시: "smba": SMBAScraper(),
}

mcp = FastMCP(
    "공모사업 공고 수집기",
    instructions="중소기업을 위한 공모사업/지원사업 공고를 수집·정리하는 MCP 서버",
)


def _format_announcement(a) -> str:
    lines = [
        f"📌 {a.title}",
        f"   기관: {a.organization}",
        f"   날짜: {a.date}" if a.date else None,
        f"   조회수: {a.views}" if a.views else None,
        f"   상태: {a.status}" if a.status else None,
        f"   작성자: {a.author}" if a.author else None,
        f"   링크: {a.url}" if a.url else None,
    ]
    return "\n".join(l for l in lines if l)


def _format_detail(a) -> str:
    lines = [
        f"제목: {a.title}",
        f"기관: {a.organization}",
        f"날짜: {a.date}" if a.date else None,
        f"링크: {a.url}" if a.url else None,
        "",
        "── 본문 ──",
        a.content if a.content else "(내용 없음)",
    ]
    if a.attachments:
        lines.append("")
        lines.append("── 첨부파일 ──")
        for att in a.attachments:
            lines.append(f"  - {att}")
    return "\n".join(l for l in lines if l is not None)


@mcp.tool()
async def list_organizations() -> str:
    """등록된 기관 목록을 조회합니다."""
    lines = ["등록된 기관 목록:"]
    for key, scraper in SCRAPERS.items():
        lines.append(f"  - {key}: {scraper.org_name}")
    return "\n".join(lines)


@mcp.tool()
async def search_announcements(
    organization: str = "",
    keyword: str = "",
    page: int = 1,
) -> str:
    """공모사업 공고를 검색합니다.

    Args:
        organization: 기관 코드 (예: nia). 비우면 전체 기관 검색.
        keyword: 검색 키워드 (선택).
        page: 페이지 번호 (기본 1).
    """
    targets = {}
    if organization:
        org_key = organization.lower()
        if org_key not in SCRAPERS:
            available = ", ".join(SCRAPERS.keys())
            return f"'{organization}' 기관을 찾을 수 없습니다. 등록된 기관: {available}"
        targets[org_key] = SCRAPERS[org_key]
    else:
        targets = SCRAPERS

    all_results = []
    for key, scraper in targets.items():
        try:
            announcements = await scraper.fetch_list(page=page, keyword=keyword)
            all_results.extend(announcements)
        except Exception as e:
            all_results.append(None)
            all_results.append(f"[{scraper.org_name}] 조회 실패: {e}")

    if not all_results:
        return "검색 결과가 없습니다."

    output_lines = [f"공모사업 공고 검색 결과 (페이지 {page}):", ""]
    for i, item in enumerate(all_results, 1):
        if item is None:
            continue
        if isinstance(item, str):
            output_lines.append(item)
        else:
            output_lines.append(f"[{i}] {_format_announcement(item)}")
            output_lines.append("")

    return "\n".join(output_lines)


@mcp.tool()
async def get_announcement_detail(
    organization: str,
    url: str,
) -> str:
    """공고의 상세 내용을 조회합니다.

    Args:
        organization: 기관 코드 (예: nia).
        url: 공고 상세 페이지 URL.
    """
    org_key = organization.lower()
    if org_key not in SCRAPERS:
        available = ", ".join(SCRAPERS.keys())
        return f"'{organization}' 기관을 찾을 수 없습니다. 등록된 기관: {available}"

    scraper = SCRAPERS[org_key]
    try:
        detail = await scraper.fetch_detail(url)
        return _format_detail(detail)
    except Exception as e:
        return f"상세 조회 실패: {e}"


if __name__ == "__main__":
    mcp.run()
