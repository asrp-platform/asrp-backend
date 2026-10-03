from typing import Annotated

from fastapi.params import Depends, Query


def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 25,
) -> dict:
    """returns limit, and offset  page_size, page_size * (page - 1)"""
    return {
        "limit": page_size,
        "offset": page_size * (page - 1),
        "page": page,
        "page_size": page_size,
    }


PaginationParamsDep = Annotated[tuple[int, int], Depends(get_pagination_params)]
OrderingParamsDep = Annotated[str | None, Query(description="Sorting parameters")]
