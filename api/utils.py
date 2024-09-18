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
    NANA = "NA"
    NAPA = "NA"
    PANA = "NA"
    NAA = "NA"
    ANA = "NA"
    PAPA = "PA"
    PAA = "A"
    APA = "A"
    AA = "A"

class Day(Enum):
    SEGUNDA = "SEGUNDA"
    TERCA = "TERCA"
    QUARTA = "QUARTA"
    QUINTA = "QUINTA"
    SEXTA = "SEXTA"
    SABADO = "SABADO"
    DOMINGO = "DOMINGO"
