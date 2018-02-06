__author__ = 'liucaiyun'
import json
from rest_framework import serializers
from products.serializer import ProductSerializer
from purchasing.serializer import OrderStatusSerializer
from models import *


class DateTimeFormat(serializers.DateTimeField):

    def to_representation(self, value):
        if not value:
            return ''
        return value.strftime('%Y-%m-%d %H:%M')


class JSONField(serializers.DictField):

    def to_representation(self, value):
        if not value:
            return dict()
        return json.loads(value)


class ShipmentOrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()


    class Meta:
        model = ShipmentOrderItem
        fields = '__all__'


class ShipmentOrderSerializer(serializers.ModelSerializer):

    create_time = DateTimeFormat()
    items = ShipmentOrderItemSerializer(many=True)
    status = OrderStatusSerializer()

    class Meta:
        model = ShipmentOrder
        fields = '__all__'


class ShipmentBoxSerializer(serializers.ModelSerializer):

    products = JSONField()

    class Meta:
        model = ShipmentBox
        # fields = '__all__'
        exclude = ['order']