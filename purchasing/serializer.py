#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
from rest_framework import serializers
from products.serializer import ProductSerializer
from models import *


class DateTimeFormat(serializers.DateTimeField):

    def to_representation(self, value):
        if not value:
            return ''
        return value.strftime('%Y-%m-%d %H:%M')


class FloatRoundField(serializers.FloatField):

    def to_representation(self, value):
        if not value:
            return value
        return round(float(value), 2)


class RoleNameSerializer(serializers.CharField):

    def to_representation(self, value):
        if value == 'finance':
            return u'财务'
        if value == 'purchasing_agent':
            return u'采购员'
        if value == 'godown_manager':
            return u'仓库管理员'
        if value == 'operator':
            return '运营人员'


class PaymentRecordsSerializer(serializers.ModelSerializer):

    pay_time = DateTimeFormat()

    class Meta:
        model = PaymentRecord
        fields = '__all__'


class TrackingOrderItemsSerializer(serializers.ModelSerializer):

    product = ProductSerializer()

    class Meta:
        model = TrackingOrderItems
        fields = '__all__'


class OrderStatusSerializer(serializers.ModelSerializer):
    role_name = RoleNameSerializer(source='role')

    class Meta:
        model = OrderStatus
        fields = '__all__'


class TrackingOrderSerializer(serializers.ModelSerializer):

    items = TrackingOrderItemsSerializer(many=True)
    status = OrderStatusSerializer()
    status_id = serializers.IntegerField()

    class Meta:
        model = TrackingOrder
        fields = '__all__'


class PurchasingOrderSerializer(serializers.ModelSerializer):
    create_time = DateTimeFormat(read_only=True)
    status = OrderStatusSerializer()
    status_id = serializers.IntegerField()

    class Meta:
        model = PurchasingOrder
        fields = '__all__'


class PurchasingOrderItemSeriazlier(serializers.ModelSerializer):
    product = ProductSerializer()
    traffic_fee = FloatRoundField()

    class Meta:
        model = PurchasingOrderItems
        fields = '__all__'


class PurchasingOrderDetailSerializer(serializers.ModelSerializer):
    create_time = DateTimeFormat(read_only=True)
    status = OrderStatusSerializer()
    status_id = serializers.IntegerField()
    items = PurchasingOrderItemSeriazlier(many=True)
    payments = PaymentRecordsSerializer(many=True)

    class Meta:
        model = PurchasingOrder
        fields = '__all__'


