from abc import ABC, abstractmethod


class EmailProvider(ABC):
    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str):
        raise NotImplementedError
