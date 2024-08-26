from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Conceito
@api_view(['GET'])
def hello_world(request):
    print(Conceito.get_final_grade("A", "NA"))
    return Response({"message": "Hello, world!"})
