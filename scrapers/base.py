"""기관 스크래퍼 베이스 클래스."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Announcement:
    """공모사업 공고 데이터."""
    title: str
    organization: str  # 기관명
    date: str           # 게시일
    url: str            # 상세 링크
    status: str = ""    # 상태 (모집중, 마감 등)
    views: int = 0      # 조회수
    author: str = ""    # 작성자/담당부서
    content: str = ""   # 상세 내용 (선택)
    attachments: list[str] = field(default_factory=list)  # 첨부파일


class BaseScraper(ABC):
    """기관별 스크래퍼의 베이스 클래스. 새 기관 추가 시 이 클래스를 상속합니다."""

    @property
    @abstractmethod
    def org_name(self) -> str:
        """기관명 반환."""

    @abstractmethod
    async def fetch_list(self, page: int = 1, keyword: str = "") -> list[Announcement]:
        """공고 목록을 가져옵니다."""

    @abstractmethod
    async def fetch_detail(self, url: str) -> Announcement:
        """공고 상세 내용을 가져옵니다."""
