import json
from django.shortcuts import render
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, Http404
from .models import Supplier

# Create your views here.


def get_all_suppliers(request):
    data = list()
    for s in Supplier.objects.all():
        data.append(s.name)
    return HttpResponse(json.dumps(data), content_type='application/json')