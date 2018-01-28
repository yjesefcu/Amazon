__author__ = 'liucaiyun'
from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework_extensions.routers import ExtendedSimpleRouter
from viewsets import *


router = ExtendedSimpleRouter()

product = router.register(r'users', UserViewSet, base_name="api_users")

urlpatterns = patterns('',
    url(r'^$', 'my_auth.views.home'),
    url(r'^api/', include(router.urls)),
    url(r'^login', 'my_auth.views.login'),
    url(r'^logout', 'my_auth.views.logout'),
    url(r'^permissions$', 'my_auth.views.get_role'),
)