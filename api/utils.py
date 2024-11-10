from django.core.exceptions import ValidationError
from functools import wraps
from enum import Enum

import environ
env = environ.Env()
environ.Env.read_env()

CLOUDINARY_BASE_PATH = "https://res.cloudinary.com/"
CLOUDINARY_CLOUD_NAME = "dfga9xwlg"
CLOUDINARY_FULL_BASE_PATH = CLOUDINARY_BASE_PATH + CLOUDINARY_CLOUD_NAME + "/"

def check_fields(request, fields: list):
    errors = {}
    for field in fields:
        if not request.data.get(field, None):
            errors[field] = "Este campo é obrigatório"
    return errors

def validate_range(MIN: int, MAX: int):
    '''MAX is included'''

    @wraps(validate_range)
    def inner_func(value):
        if value not in range(MIN, MAX+1):
            raise ValidationError(
                _("%(value)s is not in range"), # type: ignore
                params={"value": value},
            )

    return inner_func

class GRADE_TABLE(Enum):
    NANA = "ND"
    NAPA = "ND"
    PANA = "ND"
    NAA = "ND"
    ANA = "ND"
    PAPA = "D"
    PAA = "D"
    APA = "D"
    AA = "D"

    @classmethod
    def get_final_grade(cls, av1: str, av2: str, default=None):
        final = av1 + av2
        try:
            return cls[final].value
        except:
            return default

class GRADE_WEIGHT(Enum):
    NA = 0
    PA = 1
    A = 2

REVERSE_GRADE_WEIGHT = {
    0:"NA",
    1:"PA",
    2:"A"
}

def higher_grade(av1, av2):
    n1, n2 = GRADE_WEIGHT[av1].value, GRADE_WEIGHT[av2].value
    return REVERSE_GRADE_WEIGHT[max(n1, n2)]

def fill_grades(instance, data: dict):
    for unit in range(1, 4):
        av1 = getattr(instance, f"av1_{unit}")
        av2 = getattr(instance, f"av2_{unit}")
        noa = getattr(instance, f"noa_{unit}")
        if av1 and av2:
            data[f"mu_{unit}"] = GRADE_TABLE.get_final_grade(av1, av2)
        else:
            data[f"mu_{unit}"] = None

        if av1 and av2 and data[f"mu_{unit}"] == "D":
            data[f"cf_{unit}"] = "D"
            data[f"noa_{unit}"] = None
            continue

        if av1 and av2 and noa:
            higher = higher_grade(av1, av2)
            data[f"cf_{unit}"] = GRADE_TABLE.get_final_grade(noa, higher)
        else:
            data[f"cf_{unit}"] = None

    return data

class Day(Enum):
    SEGUNDA = "SEGUNDA"
    TERCA = "TERCA"
    QUARTA = "QUARTA"
    QUINTA = "QUINTA"
    SEXTA = "SEXTA"
    SABADO = "SABADO"
    DOMINGO = "DOMINGO"

# from enum import Enum
# class Hours(Enum):
#     M1 = (7, 0)
#     M2 = (7, 50)
#     M3 = (8, 40)
#     M4 = (10, 0)
#     M5 = (10, 50)
#     M6 = (11, 40)
#     M7 = (12, 30)

#     T1 = (13, 40)
#     T2 = (14, 30)
#     T3 = (15, 20)
#     T4 = (16, 40)
#     T5 = (17, 30)
#     T6 = (18, 20)
#     T7 = (19, 10)

# class Hours(models.TextChoices):
#     M1 = "7h"
#     M2 = "7h50m"
#     M3 = "8h40m"
#     M4 = "10h"
#     M5 = "10h50m"
#     M6 = "11h40m"
#     M7 = "12h30m"

#     T1 = "13h40m"
#     T2 = "14h30m"
#     T3 = "15h20m"
#     T4 = "16h40m"
#     T5 = "17h30m"
#     T6 = "18h20m"
#     T7 = "19h10m"
