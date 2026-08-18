import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field
from pydantic_core import PydanticCustomError

from app.core.database.mixins import UCIMixinSchema


def validate_year_range(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{4}", value):
        raise PydanticCustomError("year_range_error", "Format must be YYYY-YYYY")
    start, end = map(int, value.split("-"))
    if start > end:
        raise PydanticCustomError("year_range_error", "Start year cannot be greater than end year")
    if start < 1900 or end > 2100:
        raise PydanticCustomError("year_range_error", "Year out of valid range")
    return value


YearRange = Annotated[str, AfterValidator(validate_year_range)]


class ProfessionalExperienceMixin(BaseModel):
    current_position: bool
    institution: str = Field(min_length=2)
    speciality: str = Field(min_length=2)
    city: str = Field(min_length=2)
    state: str = Field(min_length=2)
    country: str = Field(min_length=2)
    years_from_to: YearRange = Field(default="2000-2006")

    model_config = {"from_attributes": True}


class ViewMixin(UCIMixinSchema):
    user_id: int


class ProfessionalInformationCreateOrUpdateSchema(BaseModel):
    medical_school: str
    medical_school_country: str
    years_from_to: YearRange
    is_board_certified_pathologist: bool = False
    is_us_pathology_trainee: bool = False
    is_us_lab_professional: bool = False


class ProfessionalInformationViewSchema(ViewMixin, ProfessionalInformationCreateOrUpdateSchema):
    model_config = {"from_attributes": True}


class ResidencyCreateSchema(ProfessionalExperienceMixin):
    pass


class ResidencyUpdateSchema(ResidencyCreateSchema):
    pass


class ResidencyViewSchema(ViewMixin, ResidencyCreateSchema):
    pass


class FellowshipCreateSchema(ProfessionalExperienceMixin):
    pass


class FellowshipUpdateSchema(FellowshipCreateSchema):
    pass


class FellowshipViewSchema(ViewMixin, FellowshipCreateSchema):
    pass


class JobCreateSchema(ProfessionalExperienceMixin):
    pass


class JobUpdateSchema(JobCreateSchema):
    pass


class JobViewSchema(ViewMixin, JobCreateSchema):
    pass
