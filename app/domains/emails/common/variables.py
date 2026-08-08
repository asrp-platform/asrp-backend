from dataclasses import dataclass


@dataclass
class EmailTemplateVariableDTO:
    key: str
    name: str
    description: str | None = None


VARIABLES_LIST = [
    EmailTemplateVariableDTO("user.firstname", "User Firstname"),
    EmailTemplateVariableDTO("user.lastname", "User Lastname"),
    EmailTemplateVariableDTO("user.country", "User Country"),
    EmailTemplateVariableDTO("user.city", "User City"),

    EmailTemplateVariableDTO("membership_type.name", "Membership type name"),
    EmailTemplateVariableDTO("membership_type.price_usd", "Membership type price"),
    EmailTemplateVariableDTO("membership_type.duration", "Membership type duration"),
]
