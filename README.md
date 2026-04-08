# 공모사업 공고 수집 MCP 서버

중소기업을 위한 공모사업/지원사업 공고를 수집하고 정리해주는 MCP(Model Context Protocol) 서버입니다.

AI 어시스턴트(Claude Desktop, Claude Code, Cursor 등)에 연결하면 대화로 공모사업을 검색할 수 있습니다.

## 지원 기관

| 코드 | 기관명 |
|------|--------|
| `nia` | 한국지능정보사회진흥원 (NIA) |

> 기관은 계속 추가될 예정입니다. PR 환영합니다!

## 설치

```bash
git clone https://github.com/<your-username>/mcp-gov-announcements.git
cd mcp-gov-announcements
pip install -r requirements.txt
```

## 사용법

### Claude Desktop

`claude_desktop_config.json`에 추가:

```json
{
  "mcpServers": {
    "공모사업": {
      "command": "python3",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Claude Code

```bash
claude mcp add 공모사업 python3 /absolute/path/to/server.py
```

### 직접 실행 (테스트용)

```bash
python3 server.py
```

## MCP 도구

| 도구 | 설명 |
|------|------|
| `list_organizations` | 등록된 기관 목록 조회 |
| `search_announcements` | 공고 검색 (기관, 키워드, 페이지) |
| `get_announcement_detail` | 공고 상세 내용 및 첨부파일 조회 |

### 사용 예시 (Claude에게 말하기)

- "NIA 최신 공모사업 보여줘"
- "AI 관련 공고 검색해줘"
- "이 공고 상세 내용 알려줘"

## 기관 추가 방법

1. `scrapers/` 디렉토리에 새 파일 생성 (예: `kised.py`)
2. `BaseScraper`를 상속하여 `fetch_list()`와 `fetch_detail()` 구현
3. `server.py`의 `SCRAPERS`에 등록

```python
# scrapers/kised.py
from .base import Announcement, BaseScraper

class KISEDScraper(BaseScraper):
    @property
    def org_name(self) -> str:
        return "KISED (창업진흥원)"

    async def fetch_list(self, page=1, keyword="") -> list[Announcement]:
        # 구현
        ...

    async def fetch_detail(self, url: str) -> Announcement:
        # 구현
        ...
```

```python
# server.py SCRAPERS에 추가
from scrapers.kised import KISEDScraper

SCRAPERS = {
    "nia": NIAScraper(),
    "kised": KISEDScraper(),
}
```

## 라이선스

MIT
