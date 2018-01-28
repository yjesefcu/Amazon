#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import os, datetime, chardet, threading, pytz
from django.conf import settings
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F
from amazon_services.exception import TextParseException
from models import *
from serializer import *


TZ_ASIA = pytz.timezone('Asia/Shanghai')


def to_float(v):
    if not v:
        return 0
    return float(v)


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class PurchasingOrderViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = PurchasingOrder.objects.all().order_by('-id').select_related('product', 'status')
    serializer_class = PurchasingOrderSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('MarketplaceId', 'product_id')

    def create(self, request, *args, **kwargs):
        data = request.data
        contract_data = data.get('contract')
        contract = Contract.objects.create(**contract_data)
        orders_data = data.get('orders')
        create_time = datetime.datetime.now().replace(tzinfo=TZ_ASIA)
        for d in orders_data:
            product, created = Product.objects.get_or_create(MarketplaceId='ATVPDKIKX0DER', SellerSKU=d.get('SellerSKU'))
            total_price = int(d.get('count')) * float(d.get('price'))
            PurchasingOrder.objects.create(contract=contract, product=product, create_time=create_time,
                                           status_id=OrderStatus.WaitForDepositPayed, received_count=0, total_price=total_price, **d)
        return Response({}, status=status.HTTP_201_CREATED)


class InboundViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = InboundProducts.objects.all().order_by('-id')
    serializer_class = InboundSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend,)

    def create(self, request, *args, **kwargs):
        _query_dict = self.get_parents_query_dict()
        order = PurchasingOrder.objects.get(pk=_query_dict['order'])
        today = datetime.datetime.now().replace(tzinfo=TZ_ASIA).date()
        status_id = OrderStatus.WaitForInbound
        inbound = InboundProducts.objects.create(order=order, product=order.product, shipping_date=today, status_id=status_id, **request.data)
        serializer = self.get_serializer(instance=inbound)
        # 更新订单本身的状态
        order.status_id = status_id
        order.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['post'])
    def putin(self, request, pk, **kwargs):
        # 入库
        instance = self.get_object()
        inbound_data = request.data.get('inbound')
        inbound_data['inbound_time'] = datetime.datetime.now().replace(tzinfo=TZ_ASIA)
        status_id = OrderStatus.WaitForCheck
        # inbound_data['status_id'] = status_id
        instance.status_id = status_id
        serializer = self.get_serializer(instance, data=inbound_data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # 如果product的尺寸有更新
        order = instance.order
        if request.data.get('product'):
            d = request.data.get('product')
            fields = ['width', 'height', 'length', 'weight', 'package_width', 'package_height', 'package_length', 'package_weight']
            product = order.product
            for field in fields:
                setattr(product, field, d.get(field))
            product.save()
        # 更新订单状态
        order.received_count += int(instance.count)
        # 更新订单运费
        order.status_id = status_id
        order.traffic_fee = to_float(order.traffic_fee) + to_float(instance.traffic_fee)
        order.save()
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def confirm(self, request, pk, **kwargs):
        # 确认入库数量
        instance = self.get_object()
        if instance.traffic_fee:
            # 如果物流费不为0，那么需要等待物流费打款
            status_id = OrderStatus.WaitForTrafficFeePayed
        else:
            status_id = OrderStatus.FINISH
        instance.status_id = status_id
        instance.save()

        # 如果订单所有货物已到货，那么关闭订单
        order = instance.order
        order.status_id = status_id
        order.save()
        if status_id == OrderStatus.FINISH:
            self._check_inbound_finish(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def payed(self, request, pk, **kwargs):
        # 物流费打款
        instance = self.get_object()
        instance.traffic_fee_payed = request.data.get('traffic_fee_payed')
        instance.status_id = OrderStatus.FINISH
        instance.save()

        order = instance.order
        order.save()
        self._check_inbound_finish(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def _check_inbound_finish(self, instance):
        # 入库单已完成
        order = instance.order
        if order.received_count < order.count:
            # 如果实际入库数量 < 采购数量，说明订单还未结束
            order.status_id = OrderStatus.WaitForTraffic
        else:
            order.status_id = OrderStatus.FINISH
        order.save()
        if not instance.count:
            return
        # 修改商品的国内库存
        product = instance.product
        inventory = product.domestic_inventory
        if not inventory:
            inventory = 0
        product.domestic_inventory = inventory + int(instance.count)
        # 更新商品成本
        # 计算本次入库的商品成本
        new_cost = (instance.count * instance.order.price + to_float(instance.traffic_fee)) / float(instance.count)
        # 更新商品当前国内总成本
        product.supply_cost = (to_float(product.supply_cost) + new_cost) / float(2)
        product.cost = product.supply_cost + to_float(product.shipment_cost)
        product.save()

