__author__ = 'liucaiyun'
from django.conf.urls import patterns, include, url
from django.contrib import admin
from rest_framework_extensions.routers import ExtendedSimpleRouter
from viewsets import *


router = ExtendedSimpleRouter()

product = router.register(r'products', ProductViewSet, base_name="api_products")
product.register(r'supply', SupplyViewSet, base_name="api_product_supply", parents_query_lookups=['product'])
product.register(r'shipments', ProductShipmentItemViewSet, base_name="api_product_shipements", parents_query_lookups=['product'])
product.register(r'orders', OrderViewSet, base_name="api_product_orders", parents_query_lookups=['product'])
product.register(r'removals', RemovalViewSet, base_name="api_product_removals", parents_query_lookups=['product'])
product.register(r'refunds', RefundViewSet, base_name="api_product_refunds", parents_query_lookups=['product'])
product.register(r'losts', ProductLostViewSet, base_name="api_product_losts", parents_query_lookups=['product'])

router.register(r'shipments', OutboundShipmentViewSet, base_name="api_ships_oversea")
router.register(r'shipmentItems', OutboundShipmentItemViewSet, base_name="api_ships_oversea_items")
router.register(r'supply', SupplyViewSet, base_name="api_supplies")
router.register(r'orders', OrderViewSet, base_name="api_product_orders")
router.register(r'removals', RemovalViewSet, base_name="api_product_removals")
router.register(r'refunds', RefundViewSet, base_name="api_product_refunds")
router.register(r'losts', ProductLostViewSet, base_name="api_product_losts")

settlement = router.register(r'settlements', SettlementViewSet, base_name="api_settlements")
settlement.register(r'products', SettlementProductViewSet, base_name="api_settlement_products", parents_query_lookups=['settlement'])
settlement.register(r'orders', OrderViewSet, base_name="api_settlement_orders", parents_query_lookups=['settlement'])
settlement.register(r'refunds', RefundViewSet, base_name="api_settlement_refunds", parents_query_lookups=['settlement'])
settlement.register(r'removals', RemovalViewSet, base_name="api_settlement_removals", parents_query_lookups=['settlement'])
settlement.register(r'losts', ProductLostViewSet, base_name="api_settlement_losts", parents_query_lookups=['settlement'])

urlpatterns = patterns('',
    url(r'^api/', include(router.urls)),
    url(r'^product/sku/$', 'products.views.get_product_by_sku'),
    url(r'^product/sync/$', 'products.views.sync_products'),
    url('^image/upload/$', 'products.views.image_upload'),
    url(r'^sync$', 'products.views.sync_orders'),
    url(r'^calcIncome$', 'products.views.calc_income'),
    # url('^file/upload/$', 'products.views.file_upload'),
)
