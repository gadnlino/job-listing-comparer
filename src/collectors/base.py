from abc import ABC, abstractmethod

from src.models import JobPosting


class BaseCollector(ABC):
    name: str

    @abstractmethod
    def search_jobs(self, query: str, max_results: int, **kwargs) -> list[JobPosting]:
        raise NotImplementedError
