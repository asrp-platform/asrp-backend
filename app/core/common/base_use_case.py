from abc import ABC, abstractmethod
from typing import Generic, TypeVar

# Type variables for input and output data
RequestType = TypeVar("RequestType")
ResponseType = TypeVar("ResponseType")


class BaseUseCase(ABC, Generic[RequestType, ResponseType]):
    """
    Base class for all Use Cases.
    Standardizes the execution flow and dependency management.
    """

    @abstractmethod
    async def execute(self, request_data: RequestType) -> ResponseType:
        """
        The main method to execute the business logic of the use case.
        """
        ...
