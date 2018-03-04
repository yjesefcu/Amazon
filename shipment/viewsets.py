#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import os, datetime, chardet, threading, pytz, json
from django.db.utils import IntegrityError
from django.conf import settings
from django.db import transaction
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from django_filters.rest_framework import DjangoFilterBackend
from purchasing.models import OrderStatus
from amazon_services.api import get_exchange_rate
from models import *
from serializer import *


TZ_ASIA = pytz.timezone('Asia/Shanghai')


def to_float(v):
    if not v:
        return 0
    return float(v)


def to_int(v):
    if not v:
        return 0
    return int(v)


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class ShipmentOrderViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = ShipmentOrder.objects.all().order_by('-id').select_related('status')
    serializer_class = ShipmentOrderSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('MarketplaceId',)

    def create(self, request, *args, **kwargs):
        data = request.data
        items_data = data.get('items')
        MarketplaceId = data.get('MarketplaceId')
        try:
            with transaction.atomic():
                order = ShipmentOrder.objects.create(MarketplaceId=MarketplaceId, create_time=datetime.datetime.now().replace(tzinfo=TZ_ASIA))
                count = 0
                for item_data in items_data:
                    product = Product.objects.get(MarketplaceId=MarketplaceId, SellerSKU=item_data.get('SellerSKU'))
                    ShipmentOrderItem.objects.create(order=order, product=product, SellerSKU=item_data.get('SellerSKU'), count=item_data.get('count'))
                    count += int(item_data.get('count'))
                order.count = count
                order.product_count = len(items_data)
                order.status_id = OrderStatus.WaitForPack
                order.save()
                serializer = self.get_serializer(order)
                headers = self.get_success_headers(serializer.data)
                # 如果是编辑保存的话， 那么删除原来的记录
                if data.get('id'):
                    ShipmentOrder.objects.get(pk=data.get('id')).delete()
        except IntegrityError, ex:
            raise IntegrityError(ex)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        data = request.data
        boxs = list()

        product_boxed = dict()
        total_int_weight = 0
        total_weight = 0
        try:
            with transaction.atomic():
                for box_data in data.get('boxs'):
                    if not box_data.get('products', None):
                        continue
                    if box_data.get('id'):
                        box = ShipmentBox.objects.get(pk=box_data.get('id'))
                    else:
                        box = ShipmentBox.objects.create(order=order)
                    BoxProductRelations.objects.filter(box=box).delete()
                    box_count = 0
                    for order_item_id, count in box_data['products'].items():
                        if not count:
                            continue
                        count = int(count)
                        BoxProductRelations.objects.create(order=order, box=box, order_item_id=order_item_id, count=count)
                        box_count += count
                        if product_boxed.get(order_item_id):
                            product_boxed[order_item_id] += count
                        else:
                            product_boxed[order_item_id] = count
                    box.products = json.dumps(box_data.get('products'))
                    del box_data['products']
                    box.count = box_count
                    for field,value in box_data.items():
                        setattr(box, field, value)
                    box.save()
                    boxs.append(box)
                    # 计算总重量
                    total_int_weight += to_float(box_data.get('itn_weight'))
                    total_weight += to_float(box_data.get('weight'))
                # 更新每个产品的实际发货数量
                total_count = 0
                items = list()
                for order_item_id, count in product_boxed.items():
                    order_item = ShipmentOrderItem.objects.get(pk=order_item_id)
                    order_item.boxed_count = count
                    self._calc_item_weight(data.get('ship_type'), to_int(data.get('volume_args')), order_item)
                    order_item.save()
                    total_count += count
                    items.append(order_item)
                if data.get('items', None) is not None:
                    del data['items']
                if data.get('boxs', None) is not None:
                    del data['boxs']
                del data['status']

                data['boxed_count'] = total_count
                data['total_itn_weight'] = total_int_weight
                data['total_weight'] = total_weight
                data['box_count'] = len(boxs)
                order.status_id = OrderStatus.WaitForSettle
                serializer = self.get_serializer(order, data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)

                # 更新商品的国内库存
                self._update_product_inventory(items)
        except IntegrityError, ex:
            raise IntegrityError(ex)
        # order.save()
        serializer = self.get_serializer(order)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def _update_product_inventory(self, items):
        # 更新商品库存
        for item in items:
            product = item.product
            product.domestic_inventory = to_int(product.domestic_inventory) - item.boxed_count
            product.save()

    @detail_route(methods=['patch'])
    def close(self, request, pk):
        order = self.get_object()
        try:
            with transaction.atomic():
                order.status_id = OrderStatus.ShipmentFinish
                order.save()
                serializer = self.get_serializer(order)
                # 结束后才会更新商品的成本
                for item in order.items.all():
                    self._update_product_unit_cost(item)
        except IntegrityError, ex:
            raise IntegrityError(ex)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _calc_item_weight(self, ship_type, volume_args, item):
        # 计算每个商品的体积重
        product = item.product
        volume_weight = (product.package_width * product.package_height * product.package_length) / volume_args
        if ship_type == 'sea':
            unit_weight = max(volume_weight, to_float(product.package_weight))
        else:
            unit_weight = product.package_width * product.package_length * product.package_height / 1000000
        item.volume_weight = volume_weight
        item.unit_weight = unit_weight
        return unit_weight

    @detail_route(methods=['post'])
    def payed(self, request, pk, **kwargs):
        order = self.get_object()
        # 输入运费和关税
        try:
            with transaction.atomic():
                traffic_fee = to_float(request.data.get('traffic_fee'))
                tax_fee = to_float(request.data.get('tax_fee'))
                order.traffic_fee = traffic_fee
                order.tax_fee = tax_fee
                order.status_id = OrderStatus.ShipmentFinish    # 关闭移库单
                order.save()
                # 计算每个商品的费用
                self._calc_item_fee(order)
        except IntegrityError, ex:
            raise IntegrityError(ex)
        return Response(status=status.HTTP_200_OK)

    def _calc_item_fee(self, order):
        # 计算每个商品的费用
        if not order.traffic_fee and not order.tax_fee:
            return
        # 将商品的总重量（=unit_weight*boxed_count），根据每个商品的总重量所在比例计算费用
        total_weight = 0
        items = order.items.all()
        for item in items:
            total_weight += item.unit_weight * item.boxed_count
        for item in items:
            ratio = (item.unit_weight * item.boxed_count) / total_weight
            if order.traffic_fee:
                item.traffic_fee = ratio * order.traffic_fee
            if order.tax_fee:
                item.tax_fee = ratio * order.tax_fee
            item.save()
        for item in items:      # 更新商品单位成本
            self._update_product_unit_cost(item)        # 更新商品的单位成本

    def _update_product_unit_cost(self, item):
        # 更新商品的单位成本和库存
        product = item.product
        new_cost = (to_float(item.traffic_fee) + to_float(item.tax_fee)) / get_exchange_rate()        # 需要除以汇率
        total_cost = to_int(product.amazon_inventory) * to_float(product.shipment_cost) + new_cost
        count = to_int(product.amazon_inventory) + item.boxed_count
        product.amazon_inventory = count
        # 需要除以汇率
        if count:
            product.shipment_cost = total_cost / count
        else:
            product.shipment_cost = total_cost
        # 总的平均成本
        product.cost = product.shipment_cost + to_float(product.supply_cost)
        product.save()


class ShipmentOrderItemViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = ShipmentOrderItem.objects.all().order_by('-id')
    serializer_class = ShipmentOrderItemSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend,)


class ShipmentBoxViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = ShipmentBox.objects.all()
    serializer_class = ShipmentBoxSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend,)

    def create(self, request, *args, **kwargs):
        order = ShipmentOrder.objects.get(pk=kwargs['parent_lookup_order'])
        data = request.data
        boxs = list()

        product_boxed = dict()
        total_int_weight = 0
        total_weight = 0
        for box_data in data:
            if not box_data.get('products', None):
                continue
            if box_data.get('id'):
                box = ShipmentBox.objects.get(pk=box_data.get('id'))
            else:
                box = ShipmentBox.objects.create(order=order)
            BoxProductRelations.objects.filter(box=box).delete()
            box_count = 0
            for order_item_id, count in box_data['products'].items():
                if not count:
                    continue
                count = int(count)
                BoxProductRelations.objects.create(order=order, box=box, order_item_id=order_item_id, count=count)
                box_count += count
                if product_boxed.get(order_item_id):
                    product_boxed[order_item_id] += count
                else:
                    product_boxed[order_item_id] = count
            box.products = json.dumps(box_data.get('products'))
            del box_data['products']
            box.count = box_count
            for field,value in box_data.items():
                setattr(box, field, value)
            box.save()
            boxs.append(box)
            # 计算总重量
            total_int_weight += to_float(box_data.get('itn_weight'))
            total_weight += to_float(box_data.get('weight'))
        # 更新每个产品的实际发货数量
        total_count = 0
        for order_item_id, count in product_boxed.items():
            order_item = ShipmentOrderItem.objects.get(pk=order_item_id)
            order_item.boxed_count = count
            order_item.save()
            total_count += count
        order.boxed_count = total_count
        order.total_itn_weight = total_int_weight
        order.total_weight = total_weight
        order.box_count = len(boxs)
        order.save()
        serializer = self.get_serializer(boxs, many=True)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)