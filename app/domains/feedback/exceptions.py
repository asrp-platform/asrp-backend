from app.core.common.exceptions import NotFoundError, ResourceAlreadyExistsError


class FeedbackAdditionalInfoAlreadyExistsError(ResourceAlreadyExistsError):
    pass

class ContactMessageNotFoundError(NotFoundError):
    pass
