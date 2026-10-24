from enum import Enum

from sqlalchemy import Enum as SAEnum


class UserRole(str, Enum):
    OPERATOR = "operator"
    FIELD_AGENT = "field_agent"


class BusinessType(str, Enum):
    MAIZE_MILL = "maize_mill"
    WELDING = "welding"
    BUTCHERY = "butchery"
    BAKERY = "bakery"
    BAR = "bar"
    RESTAURANT = "restaurant"
    SALON = "salon"
    RETAIL = "retail"
    IRRIGATION = "irrigation"
    COLD_STORAGE = "cold_storage"
    OTHER = "other"


class ConnectionStatus(str, Enum):
    PROSPECTIVE = "prospective"
    PURSUING = "pursuing"
    CONNECTED = "connected"
    DECLINED = "declined"


class StartupDataLabel(str, Enum):
    USER_ENTERED = "user_entered"
    ESTIMATED = "estimated"


class DeviceStatus(str, Enum):
    ACTIVE = "active"
    FAULTY = "faulty"
    RETIRED = "retired"


class SolarDayType(str, Enum):
    AVERAGE = "average"
    LOW_SUN = "low_sun"


class Outcome(str, Enum):
    FEASIBLE = "feasible"
    CONDITIONALLY_FEASIBLE = "conditionally_feasible"
    NOT_FEASIBLE = "not_feasible"


class LimitingCheck(str, Enum):
    POWER = "power"
    STARTUP = "startup"
    ENERGY = "energy"
    BATTERY = "battery"


class RevenueBasis(str, Enum):
    DELIVERED = "delivered"
    PLANNED = "planned"


class DataLabel(str, Enum):
    OBSERVED = "observed"
    USER_ENTERED = "user_entered"
    ESTIMATED = "estimated"
    SIMULATED = "simulated"


class Decision(str, Enum):
    PURSUE = "pursue"
    NOT_PURSUE = "not_pursue"


def varchar_enum(enum_class, length, name):
    return SAEnum(
        enum_class,
        native_enum=False,
        create_constraint=True,
        length=length,
        name=name,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )