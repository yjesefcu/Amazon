__author__ = 'liucaiyun'
import json, pytz, datetime
from rest_framework import serializers
from products.serializer import ProductSerializer
from purchasing.serializer import OrderStatusSerializer
from amazon_services.serializer import MarketSerializer
from models import *


TZ_ASIA = pytz.timezone('Asia/Shanghai')


class FloatRoundField(serializers.FloatField):

    def to_representation(self, value):
        if not value:
            return value
        return round(float(value), 2)


class MarketAccountField(serializers.DictField):

    def to_representation(self, value):
        account = MarketAccount.objects.get(pk=value)
        return MarketSerializer(account).data


class DateTimeFormat(serializers.DateTimeField):

    def to_representation(self, value):
        if not value:
            return ''
        return (value + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')


class JSONField(serializers.DictField):

    def to_representation(self, value):
        if not value:
            return dict()
        return json.loads(value)


class ShipmentOrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    unit_weight = FloatRoundField()
    traffic_fee = FloatRoundField()
    tax_fee = FloatRoundField()

    class Meta:
        model = ShipmentOrderItem
        fields = '__all__'


class ShipmentOrderSerializer(serializers.ModelSerializer):

    create_time = DateTimeFormat()
    items = ShipmentOrderItemSerializer(many=True)
    status = OrderStatusSerializer()
    # market = MarketAccountField(source='MarketplaceId')

    class Meta:
        model = ShipmentOrder
        fields = '__all__'


class ShipmentBoxSerializer(serializers.ModelSerializer):

    products = JSONField()

    class Meta:
        model = ShipmentBox
        # fields = '__all__'
        exclude = ['order']