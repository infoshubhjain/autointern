from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from data.models import JobListing


class BaseScraper(ABC):
    @abstractmethod
    def fetch(self) -> List[JobListing]:
        raise NotImplementedError
