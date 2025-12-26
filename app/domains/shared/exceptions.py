from fastapi_exception_responses import Responses


class PermissionsResponses(Responses):
    PERMISSION_ERROR = 403, "Not enough permissions to perform this action"
