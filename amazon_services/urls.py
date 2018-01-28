__author__ = 'liucaiyun'
from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework_extensions.routers import ExtendedSimpleRouter
from viewsets import *


router = ExtendedSimpleRouter()
router.register(r'markets', MarketViewSet, base_name="api_markets")

urlpatterns = patterns('',
    url(r'^action$', 'amazon_services.views.request_to_amazon', name='request_to_amazon'),
    url(r'^api/', include(router.urls)),
)
