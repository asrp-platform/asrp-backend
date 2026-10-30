from app.core.common.base_exceptions import NotFoundError


class DirectionBoardMemberNotFoundError(NotFoundError):
    pass


class InvalidReorderItemsCountError(Exception):
    pass
