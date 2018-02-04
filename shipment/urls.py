__author__ = 'liucaiyun'
from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework_extensions.routers import ExtendedSimpleRouter
from viewsets import *


router = ExtendedSimpleRouter()

shipment = router.register(r'shipments', ShipmentOrderViewSet, base_name="api_shipments")
shipment.register(r'items', ShipmentOrderItemViewSet, base_name="api_shipment_items", parents_query_lookups=['order'])
shipment.register(r'boxs', ShipmentBoxViewSet, base_name="api_shipment_boxs", parents_query_lookups=['order'])

urlpatterns = patterns('',
    url(r'^api/', include(router.urls)),
)
