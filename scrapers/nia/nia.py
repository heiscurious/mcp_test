"""NIA (한국지능정보사회진흥원) 사업공고 스크래퍼."""

import re
import httpx
from bs4 import BeautifulSoup

from scrapers.base import Announcement, BaseScraper

BASE_URL = "https://nia.or.kr"
LIST_URL = f"{BASE_URL}/site/nia_kor/ex/bbs/List.do"
VIEW_URL = f"{BASE_URL}/site/nia_kor/ex/bbs/View.do"
CB_IDX = "78336"  # 사업공고 게시판 ID


class NIAScraper(BaseScraper):
    @property
    def org_name(self) -> str:
        return "NIA (한국지능정보사회진흥원)"

    async def fetch_list(self, page: int = 1, keyword: str = "") -> list[Announcement]:
        params = {
            "cbIdx": CB_IDX,
            "pageIndex": str(page),
        }
        if keyword:
            params["searchKey"] = "all"
            params["searchVal"] = keyword

        async with httpx.AsyncClient(timeout=15, verify=False) as client:
            resp = await client.get(LIST_URL, params=params)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[Announcement] = []

        # 게시판 목록 파싱 — <ul> 안의 <li> 항목
        board_list = soup.select("div.board_list ul li, table.board_list tbody tr, ul.board_list li")

        if not board_list:
            # fallback: 모든 li에서 doBbsFView 링크 포함된 것 찾기
            board_list = soup.find_all("li")
            board_list = [li for li in board_list if li.find("a", onclick=re.compile(r"doBbsFView"))]

        for item in board_list:
            link_tag = item.find("a", onclick=re.compile(r"doBbsFView"))
            if not link_tag:
                continue

            # 링크 태그에서 제목 텍스트만 추출 (아이콘, 뱃지 등 제거)
            title = link_tag.get_text(strip=True)
            # "첨부파일 있음", "new", 날짜, 조회수 등 부가정보 제거
            title = re.sub(r'첨부파일\s*있음', '', title)
            title = re.sub(r'new\d{4}\.\d{2}\.\d{2}.*$', '', title)
            title = re.sub(r'\s+', ' ', title).strip()

            # onclick에서 파라미터 추출: doBbsFView(cbIdx, bcIdx, ...)
            onclick = link_tag.get("onclick", "")
            match = re.search(r"doBbsFView\(['\"]?(\d+)['\"]?\s*,\s*['\"]?(\d+)['\"]?", onclick)
            if match:
                cb_idx, bc_idx = match.group(1), match.group(2)
                detail_url = f"{VIEW_URL}?cbIdx={cb_idx}&bcIdx={bc_idx}"
            else:
                detail_url = ""

            # 날짜, 조회수, 작성자 추출
            text = item.get_text(" ", strip=True)
            date_match = re.search(r"(\d{4}\.\d{2}\.\d{2})", text)
            date = date_match.group(1) if date_match else ""

            views_match = re.search(r"조회수?\s*(\d+)", text)
            views = int(views_match.group(1)) if views_match else 0

            results.append(Announcement(
                title=title,
                organization=self.org_name,
                date=date,
                url=detail_url,
                views=views,
            ))

        return results

    async def fetch_detail(self, url: str) -> Announcement:
        async with httpx.AsyncClient(timeout=15, verify=False) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        detail_area = soup.select_one(".detail_type01")

        # 제목
        title_el = detail_area.select_one(".tit_area") if detail_area else None
        title = title_el.get_text(strip=True) if title_el else ""

        # 날짜
        date = ""
        write_area = detail_area.select_one(".write_area") if detail_area else None
        if write_area:
            for em in write_area.select("em"):
                dm = re.search(r"(\d{4}\.\d{2}\.\d{2})", em.get_text())
                if dm:
                    date = dm.group(1)
                    break

        # 본문
        content_el = soup.select_one(".con_area")
        content = content_el.get_text("\n", strip=True) if content_el else ""

        # 첨부파일
        attachments = []
        file_area = soup.select_one(".fileNew_area")
        if file_area:
            for a in file_area.select("a[href*='Download.do']"):
                fname = a.get_text(strip=True)
                if fname and "다운로드" not in fname:
                    href = a.get("href", "")
                    if href and not href.startswith("http"):
                        href = BASE_URL + href
                    attachments.append(f"{fname} ({href})")

        return Announcement(
            title=title,
            organization=self.org_name,
            date=date,
            url=url,
            content=content[:3000],  # 너무 길면 잘라냄
            attachments=attachments,
        )
