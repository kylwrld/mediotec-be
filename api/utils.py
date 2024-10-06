from django.core.exceptions import ValidationError
from functools import wraps
from enum import Enum

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

class EGrade(Enum):
    NANA = "ND"
    NAPA = "ND"
    PANA = "ND"
    NAA = "ND"
    ANA = "ND"
    PAPA = "D"
    PAA = "D"
    APA = "D"
    AA = "D"

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
