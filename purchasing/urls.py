__author__ = 'liucaiyun'
from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework_extensions.routers import ExtendedSimpleRouter
from viewsets import *


router = ExtendedSimpleRouter()

product = router.register(r'purchasing', PurchasingOrderViewSet, base_name="api_purchasing")
product.register(r'inbounds', InboundViewSet, base_name="api_purchasing_inbounds", parents_query_lookups=['order'])
# product.register(r'supply', SupplyViewSet, base_name="api_product_supply", parents_query_lookups=['product'])

urlpatterns = patterns('',
    url(r'^api/', include(router.urls)),
)
