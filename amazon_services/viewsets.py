#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import status
from rest_framework.response import Response
from models import *
from serializer import *


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class MarketViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = MarketAccount.objects.all()
    serializer_class = MarketSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
