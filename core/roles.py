from enum import Enum


class UserRole(str, Enum):
    OPERATOR = "operator"
    FIELD_AGENT = "field_agent"