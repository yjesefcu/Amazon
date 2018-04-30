__author__ = 'liucaiyun'
from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework_extensions.routers import ExtendedSimpleRouter
from viewsets import *
from purchasing.views import get_all_suppliers


router = ExtendedSimpleRouter()

product = router.register(r'purchasing', PurchasingOrderViewSet, base_name="api_purchasing")
product.register(r'inbounds', TrackingOrderViewSet, base_name="api_purchasing_inbounds", parents_query_lookups=['purchasing_order'])
router.register(r'inbounds', TrackingOrderViewSet, base_name="api_inbounds")

urlpatterns = patterns('',
    url(r'^api/', include(router.urls)),
    url(r'^api/suppliers/$', get_all_suppliers),
)
