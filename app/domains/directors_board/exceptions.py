from app.core.common.exceptions import NotFoundError


class DirectionBoardMemberNotFoundError(NotFoundError):
    pass


class InvalidReorderItemsCountError(Exception):
    pass
