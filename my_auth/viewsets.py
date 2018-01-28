#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rolepermissions.roles import assign_role
from serializer import *


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


def get_role_name(role):
    if role == 'system_admin':
        return u'管理员'
    if role == 'purchasing_agent':
        return u'采购员'
    if role == 'finance':
        return u'财务'
    if role == 'godown_manager':
        return u'入库管理员'


class UserViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = User.objects.all().filter(is_active=True, is_superuser=False).order_by('-date_joined')
    serializer_class = UserSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def create(self, request, *args, **kwargs):
        data = request.data
        user = User.objects.create_user(data.get('username'), '', data.get('password'))
        user.is_staff = True
        user.first_name = data.get('first_name')
        user.last_name = get_role_name(data.get('role'))
        user.save()
        # 保存用户的角色
        assign_role(user, request.data.get('role'))
        serializer = self.serializer_class(user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_destroy(self, instance):
        instance.is_active = 0
        instance.is_staff = 0
        instance.save()