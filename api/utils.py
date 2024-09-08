def check_fields(request, fields: list):
    errors = {}
    for field in fields:
        if not request.data.get(field, None):
            errors[field] = "Este campo é obrigatório"
    return errors
