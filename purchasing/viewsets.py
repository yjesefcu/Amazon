#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import os, datetime, chardet, threading, pytz
from django.conf import settings
from django.db import transaction
from django.db.utils import IntegrityError
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


def to_int(v):
    if not v:
        return 0
    return int(v)


def to_float(v):
    if not v:
        return 0
    return float(v)


def add_int(obj, field, value):
    if not value:
        return
    if getattr(obj, field):
        setattr(obj, field, getattr(obj, field) + int(value))
    else:
        setattr(obj, field, int(value))


def add_float(obj, field, value):
    if not value:
        return
    if getattr(obj, field):
        setattr(obj, field, getattr(obj, field) + float(value))
    else:
        setattr(obj, field, float(value))


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class PurchasingOrderViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = PurchasingOrder.objects.all().order_by('-id').select_related('status')
    serializer_class = PurchasingOrderDetailSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    # filter_backends = (DjangoFilterBackend,)

    def create(self, request, *args, **kwargs):
        data = request.data
        items = data.get('items')
        del data['items']
        create_time = datetime.datetime.now().replace(tzinfo=TZ_ASIA)
        order = PurchasingOrder.objects.create(create_time=create_time, status_id=OrderStatus.WaitForDepositPayed,
                                               next_to_pay=data.get('deposit'), next_payment_comment=u'预付款',
                                               **data)
        count = 0
        total_price = 0
        for d in items:
            product_id = d.get('product').get("id")
            total_price = int(d.get('count')) * float(d.get('price'))
            if 'product' in d:
                del d['product']
            poi = PurchasingOrderItems.objects.create(product_id=product_id, total_price=total_price, order=order, **d)
            count += poi.count
            total_price += poi.total_price
        order.count = count
        order.total_price = total_price
        order.save()
        headers = self.get_success_headers(self.get_serializer(order).data)
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['post'])
    def payed(self, request, pk, **kwargs):
        order = self.get_object()
        fee = to_float(request.data.get('fee'))
        order.next_to_pay -= fee
        add_float(order, 'total_payed', fee)
        fee_comment = ''
        if order.status_id == OrderStatus.WaitForDepositPayed: # 打预付款
            order.status_id = OrderStatus.WaitForProducing
            fee_comment = u'预付款'
        elif order.status_id == OrderStatus.WaitForPaying:
            order.status_id = OrderStatus.WaitForTraffic
            fee_comment = u'尾款'
        try:
            with transaction.atomic():
                order.save()
                PaymentRecord.objects.create(order=order, traffic_order=None, fee_comment=fee_comment,
                                             payment_date=datetime.datetime.now().replace(tzinfo=TZ_ASIA).date(),
                                             creator=request.user, **request.data)
        except IntegrityError, ex:
            raise IntegrityError(ex)
        return Response()


class TrackingOrderViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = TrackingOrder.objects.all().order_by('-id')
    serializer_class = TrackingOrderSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend,)

    def create(self, request, *args, **kwargs):
        _query_dict = self.get_parents_query_dict()
        purchasing_order = PurchasingOrder.objects.get(pk=_query_dict['purchasing_order'])
        today = datetime.datetime.now().replace(tzinfo=TZ_ASIA).date()
        status_id = OrderStatus.WaitForInbound
        data = request.data
        items = request.data['items']
        del data['items']
        try:
            with transaction.atomic():
                inbound = TrackingOrder.objects.create(purchasing_order=purchasing_order, shipping_date=today, status_id=status_id, **data)
                serializer = self.get_serializer(instance=inbound)

                # 增加商品的发货数量信息
                count = 0
                for item in items:
                    product = Product.objects.get(pk=item['product']['id'])
                    titem = TrackingOrderItems.objects.create(purchasing_order=purchasing_order, traffic_order=inbound, shipping_date=today,
                                                      product=product, expect_count=item.get('expect_count'))
                    count += int(item['expect_count'])
                    # 更新每一个商品的发货数量
                    pitem = PurchasingOrderItems.objects.get(product=product, order=purchasing_order)
                    if pitem.expect_count:
                        pitem.expect_count += titem.expect_count
                    else:
                        pitem.expect_count = titem.expect_count
                    pitem.save()
                inbound.expect_count = count
                inbound.save()
                # 更新订单本身的状态
                if purchasing_order.expect_count:
                    purchasing_order.expect_count += count
                else:
                    purchasing_order.expect_count = count
                purchasing_order.status_id = status_id
                purchasing_order.save()
        except IntegrityError, ex:
            raise IntegrityError(ex)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # 是否需要更新商品信息
    def _update_product(self, product, data):
        fields = ['width', 'length', 'height', 'weight', 'package_width', 'package_length', 'package_height', 'package_weight']
        equal = True
        for field in fields:
            if getattr(product, field) != to_float(data.get(field)):
                setattr(product, field, to_float(data.get(field)))
                equal = False
        if not equal:
            product.save()

    @detail_route(methods=['post'])
    def putin(self, request, pk, **kwargs):
        # 入库
        data = request.data
        instance = self.get_object()
        input_date = datetime.datetime.now().replace(tzinfo=TZ_ASIA).date()
        status_id = OrderStatus.WaitForTrafficFeePayed
        # 如果product的尺寸有更新
        received_count = 0
        damage_count = 0
        purchasing_order = instance.purchasing_order
        try:
            with transaction.atomic():
                for item_date in data.get('items'):
                    item = TrackingOrderItems.objects.get(id=item_date.get('id'))
                    product = item.product
                    self._update_product(product, item_date.get('product'))      # 更新商品的尺寸信息
                    item.input_date = input_date
                    item.received_count = item_date.get('received_count')
                    item.damage_count = item_date.get('damage_count')
                    item.save()
                    # 更新采购单商品的数量
                    pitem = PurchasingOrderItems.objects.get(order=purchasing_order, product=product)
                    add_int(pitem, 'received_count', item.received_count)
                    add_int(pitem, 'damage_count', item.damage_count)
                    pitem.save()
                    # 统计
                    received_count += int(item.received_count)
                    damage_count += int(item.damage_count)
                # 更新物流总数据
                add_int(instance, 'received_count', received_count)
                add_int(instance, 'damage_count', damage_count)
                instance.traffic_fee = data.get('traffic_fee')
                instance.input_date = input_date
                instance.status_id = status_id
                instance.save()

                # 更新采购订单的收货数量和损坏数量
                add_int(purchasing_order, 'received_count', received_count)
                add_int(purchasing_order, 'damage_count', damage_count)
                add_float(purchasing_order, 'traffic_fee', data.get('traffic_fee'))
                add_float(purchasing_order, 'next_to_pay', data.get('traffic_fee'))
                purchasing_order.next_payment_comment = '物流费'
                purchasing_order.status_id = status_id
                purchasing_order.save()
        except IntegrityError, ex:
            raise IntegrityError(ex)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def _split_traffic_fee(self, traffic_order):
        # 将运费平摊到每个商品上面
        items = traffic_order.items
        # 按商品的重量*数量进行平摊
        total_weight = 0
        for item in items:
            total_weight += item.product.weight * item.received_count
        for item in items:
            product = item.product
            item.traffic_fee = (product.weight * item.received_count) / total_weight * traffic_order.traffic_fee_payed
            item.save()
            # 加到采购单对应商品中
            poi = PurchasingOrderItems.objects.get(product=product, order=traffic_order.purchasing_order)
            add_float(poi, 'traffic_fee', item.traffic_fee)
            poi.save()
            # 加到商品成本中
            self._add_to_prodcut_inventory(item)

    def _add_to_prodcut_inventory(self, item):
        # 加入到商品库存和成本中
        product = item.product
        count = int(item.received_count) - to_int(item.damage_count)   # 需要减去损坏数量
        # 找出商品单价
        poi = PurchasingOrderItems.objects.get(order_id=item.purchasing_order_id, product=product)
        new_cost = (item.received_count * poi.price + item.traffic_fee) / float(count)      # 由于支付尾款时是按总数量支付的，因此损坏的数量也要算上去
        # 更新商品当前国内总成本
        total = to_float(product.supply_cost) * to_int(product.domestic_inventory) + new_cost
        add_int(product, 'domestic_inventory', count)       # 增加库存
        product.supply_cost = total / product.domestic_inventory
        product.cost = product.supply_cost + to_float(product.shipment_cost)
        product.save()

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
        fee = to_float(request.data.get('traffic_fee_payed'))
        try:
            with transaction.atomic():
                instance.traffic_fee_payed = fee
                instance.status_id = OrderStatus.FINISH
                instance.save()

                order = instance.purchasing_order
                add_float(order, 'total_payed', fee)
                order.next_to_pay -= fee
                order.status_id = OrderStatus.WaitForCheck  # 更新状态为等待确认
                order.save()

                # 增加一条打款记录
                PaymentRecord.objects.create(order=order, traffic_order=instance, fee_comment=u'物流费', need_payed=instance.traffic_fee, payed=fee,
                                             payment_comment=request.data.get('payment_comment'),
                                             pay_time=datetime.datetime.now().replace(tzinfo=TZ_ASIA), creator=request.user)

                # 平摊运费
                self._split_traffic_fee(instance)
        except IntegrityError, ex:
            raise IntegrityError(ex)
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

