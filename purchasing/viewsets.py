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
from amazon_services.api import get_exchange_rate
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
        setattr(obj, field, getattr(obj, field) + to_float(value))
    else:
        setattr(obj, field, to_float(value))


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
        data['status_id'] = OrderStatus.WaitForTraffic
        data['create_time'] = create_time
        exist_order_id = data.get('id')
        if exist_order_id:
            del data['id']
            del data['status']
            del data['payments']
        try:
            with transaction.atomic():
                order = PurchasingOrder.objects.create(**data)
                count = 0
                total_price = 0
                for d in items:
                    product_id = d.get('product').get("id")
                    price = int(d.get('count')) * float(d.get('price'))
                    if 'product' in d:
                        del d['product']
                    if 'id' in d:
                        del d['id']
                    d['product_id'] = product_id
                    d['total_price'] = price
                    d['order'] = order
                    poi = PurchasingOrderItems.objects.create(**d)
                    count += to_int(poi.count)
                    total_price += poi.total_price
                order.count = count
                order.total_price = total_price
                order.save()
                # 如果编辑的话，需要删除老的采购单信息
                if exist_order_id:
                    PurchasingOrder.objects.get(pk=exist_order_id).delete()
        except IntegrityError, ex:
            raise IntegrityError(ex)
        headers = self.get_success_headers(self.get_serializer(order).data)
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data
        try:
            with transaction.atomic():

                if data.get('status_id') == OrderStatus.WaitForPayment:
                    # 提交到财务确认时，需要确认采购单花费是否争正确
                    post_items = data.get('items')
                    db_items = instance.items.all()
                    total_fee = 0
                    for post_item in post_items:
                        item_fee = to_float(post_item.get('total_fee'))
                        total_fee += to_float(item_fee)
                        for db_item in db_items:
                            if db_item.id == post_item.get("id"):
                                if db_item.total_fee != item_fee:
                                    self._update_prodcut_total_fee(db_item, item_fee)
                    del data['items']
                    data['total_payed'] = total_fee
                serializer = self.get_serializer(instance, data=data, partial=partial)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
        except IntegrityError, ex:
            raise IntegrityError(ex)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def _update_prodcut_total_fee(self, item, new_total_fee):
        # 如果订单中商品的实际花费与之前的不吻合，需要更新商品成本
        old_total_fee = item.total_fee
        item.total_fee = new_total_fee
        item.save()
        diff = new_total_fee - old_total_fee
        # 更新商品成本
        product = item.product
        product.supply_cost += diff / product.domestic_inventory if product.domestic_inventory else 0
        product.save()


    @detail_route(methods=['post'])
    def payed(self, request, pk, **kwargs):
        order = self.get_object()
        data = request.data
        order.deposit_payed = to_float(data.get('deposit_payed'))
        order.final_payment_payed = to_float(data.get('final_payment_payed'))
        order.traffic_fee_payed = to_float(data.get('traffic_fee_payed'))
        order.total_payed = order.deposit_payed + order.final_payment_payed + order.traffic_fee_payed
        # 比较实际付款与需要付的金额，将差异的部分从成本中减去


class TrackingOrderViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = TrackingOrder.objects.all().order_by('-id')
    serializer_class = TrackingOrderSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend,)

    def create(self, request, *args, **kwargs):
        _query_dict = self.get_parents_query_dict()
        purchasing_order = PurchasingOrder.objects.get(pk=_query_dict['purchasing_order'])
        today = datetime.datetime.now().replace(tzinfo=TZ_ASIA).date()
        status_id = OrderStatus.TrafficConfirm
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
                    price = to_float(item.get('price'))
                    titem = TrackingOrderItems.objects.create(purchasing_order=purchasing_order, traffic_order=inbound, shipping_date=today,
                                                      product=product, expect_count=item.get('expect_count'), price=price,
                                                              total_price=price * int(item.get('expect_count')))
                    count += int(item['expect_count'])
                    # 更新每一个商品的发货数量
                    pitem = PurchasingOrderItems.objects.get(product=product, order=purchasing_order)
                    if pitem.expect_count:
                        pitem.expect_count += to_int(titem.expect_count)
                    else:
                        pitem.expect_count = to_int(titem.expect_count)
                    pitem.price = price # 更新单价
                    pitem.save()
                inbound.expect_count = count
                inbound.save()
                # 更新订单本身的状态
                if purchasing_order.expect_count:
                    purchasing_order.expect_count += count
                else:
                    purchasing_order.expect_count = count
                add_float(purchasing_order, 'final_payment', data.get('final_payment'))
                purchasing_order.status_id = status_id
                purchasing_order.save()
        except IntegrityError, ex:
            raise IntegrityError(ex)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @detail_route(methods=['post'])
    def received(self, request, pk, **kwargs):
        # 确认到货
        instance = self.get_object()
        instance.status_id = OrderStatus.WaitForInbound     # 状态更新为等待入库
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

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
        status_id = OrderStatus.TrafficReceived
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
                    add_float(pitem, 'total_fee', item.total_price)
                    pitem.save()
                    # 统计
                    received_count += int(item.received_count)
                    damage_count += int(item.damage_count)
                # 更新物流总数据
                add_int(instance, 'received_count', received_count)
                add_int(instance, 'damage_count', damage_count)
                instance.expect_count -= received_count
                instance.traffic_fee = data.get('traffic_fee')
                instance.input_date = input_date
                instance.status_id = status_id
                instance.save()

                # 更新采购订单的收货数量和损坏数量
                add_int(purchasing_order, 'received_count', received_count)
                add_int(purchasing_order, 'damage_count', damage_count)
                add_float(purchasing_order, 'traffic_fee', data.get('traffic_fee'))
                purchasing_order.status_id = OrderStatus.WaitForCheck
                purchasing_order.save()

                # 更新运费到每个商品
                self._split_traffic_fee(instance)
                # 入库后立即更新国内库存和成本
        except IntegrityError, ex:
            raise IntegrityError(ex)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def _split_traffic_fee(self, traffic_order):
        # 将运费平摊到每个商品上面
        items = traffic_order.items.all()
        # 按商品的重量*数量进行平摊
        total_weight = 0
        for item in items:
            total_weight += item.product.weight * item.received_count
        total_traffic_fee = to_float(traffic_order.traffic_fee)
        for item in items:
            if total_traffic_fee:
                product = item.product
                item.traffic_fee = (product.weight * item.received_count) / total_weight * total_traffic_fee
                item.save()
                # 加到采购单对应商品中
                poi = PurchasingOrderItems.objects.get(product=product, order=traffic_order.purchasing_order)
                add_float(poi, 'traffic_fee', item.traffic_fee)
                poi.total_fee += float(item.traffic_fee)
                poi.save()
            # 加到商品成本中
            self._add_to_prodcut_inventory(item)

    def _add_to_prodcut_inventory(self, item):
        # 加入到商品库存和成本中
        product = item.product
        count = int(item.received_count) - to_int(item.damage_count)   # 需要减去损坏数量
        # 找出商品单价
        # poi = PurchasingOrderItems.objects.get(order_id=item.purchasing_order_id, product=product)
        new_cost = (item.total_price + to_float(item.traffic_fee)) / float(count)      # 由于支付尾款时是按总数量支付的，因此损坏的数量也要算上去
        # 需要处以汇率
        new_cost = new_cost / get_exchange_rate()
        # 更新商品当前国内总成本
        total = to_float(product.supply_cost) * to_int(product.domestic_inventory) + new_cost
        add_int(product, 'domestic_inventory', count)       # 增加库存
        product.supply_cost = total / product.domestic_inventory
        product.cost = product.supply_cost + to_float(product.shipment_cost)
        product.save()
