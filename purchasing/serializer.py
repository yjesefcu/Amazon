__author__ = 'liucaiyun'
from rest_framework import serializers
from products.serializer import ProductSerializer
from models import *


class DateTimeFormat(serializers.DateTimeField):

    def to_representation(self, value):
        if not value:
            return ''
        return value.strftime('%Y-%m-%d %H:%M')


class ContractSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contract
        fields = '__all__'


class OrderStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderStatus
        fields = '__all__'


class PurchasingOrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    create_time = DateTimeFormat(read_only=True)
    contract = ContractSerializer(read_only=True)
    status = OrderStatusSerializer()
    status_id = serializers.IntegerField()

    class Meta:
        model = PurchasingOrder
        fields = '__all__'


class InboundSerializer(serializers.ModelSerializer):
    inbound_time = DateTimeFormat()
    status = OrderStatusSerializer()

    class Meta:
        model = InboundProducts
        fields = '__all__'