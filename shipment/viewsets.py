#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import os, datetime, chardet, threading, pytz, json
from django.conf import settings
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from django_filters.rest_framework import DjangoFilterBackend
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
        order = ShipmentOrder.objects.create(MarketplaceId=MarketplaceId, create_time=datetime.datetime.now().replace(tzinfo=TZ_ASIA))
        count = 0
        for item_data in items_data:
            product = Product.objects.get(MarketplaceId=MarketplaceId, SellerSKU=item_data.get('SellerSKU'))
            ShipmentOrderItem.objects.create(order=order, product=product, SellerSKU=item_data.get('SellerSKU'), count=item_data.get('count'))
            count += int(item_data.get('count'))
        order.count = count
        order.product_count = len(items_data)
        order.save()
        serializer = self.get_serializer(order)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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

    # def list(self, request, *args, **kwargs):
    #     order = ShipmentOrder.objects.get(pk=kwargs['parent_lookup_order'])
    #     boxs = ShipmentBox.objects.filter(order=order).prefetch_related('products')
    #
    #     queryset = self.filter_queryset(self.get_queryset())
    #
    #     page = self.paginate_queryset(queryset)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return self.get_paginated_response(serializer.data)
    #
    #     serializer = self.get_serializer(queryset, many=True)
    #     return Response(serializer.data)