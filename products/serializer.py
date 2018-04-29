#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import datetime
from rest_framework import serializers
from models import *


class ProfitRateField(serializers.CharField):

    def to_representation(self, value):
        if not value:
            return '0%'
        return '%d%%' % (round(float(value), 3) * 100)


class FloatRoundField(serializers.FloatField):

    def to_representation(self, value):
        if not value:
            return value
        return round(float(value), 2)


class TransactionTypeField(serializers.CharField):
    def to_representation(self, value):
        if value == 'REVERSAL_REIMBURSEMENT':
            return u'卖家退货'
        if value == 'INCORRECT_FEES_ITEMS':
            return u'费用更正'
        if value == 'MISSING_FROM_INBOUND':
            return u'丢失：仓库'
        return value


class DateTimeFormat(serializers.DateTimeField):

    def to_representation(self, value):
        if not value:
            return ''
        return value.strftime('%Y-%m-%d %H:%M:%S')


class DateFormatField(serializers.DateTimeField):

    def to_representation(self, value):
        if not value:
            return ''
        return value.strftime('%m-%d')


class DateFormat(serializers.DateTimeField):

    def to_representation(self, value):
        return value.strftime('%Y-%m-%d')


class SettlementSerializer(serializers.ModelSerializer):
    StartDate = DateFormat()
    EndDate = DateFormat()
    sales = FloatRoundField()
    refund = FloatRoundField()
    other_fee = FloatRoundField()
    other_trade = FloatRoundField()
    income = FloatRoundField()
    profit = FloatRoundField()
    profit_rate = ProfitRateField()
    total_cost = FloatRoundField()

    class Meta:
        model = Settlement
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    supply_cost = FloatRoundField(read_only=True)
    shipment_cost = FloatRoundField(read_only=True)
    package_width = FloatRoundField(read_only=True)
    package_height = FloatRoundField(read_only=True)
    package_length = FloatRoundField(read_only=True)
    package_weight = FloatRoundField(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


class ProductWithGigftsSeriazlier(serializers.ModelSerializer):
    supply_cost = FloatRoundField(read_only=True)
    shipment_cost = FloatRoundField(read_only=True)
    gifts = ProductSerializer(source='get_gifts', many=True)
    package_width = FloatRoundField(read_only=True)
    package_height = FloatRoundField(read_only=True)
    package_length = FloatRoundField(read_only=True)
    package_weight = FloatRoundField(read_only=True)

    class Meta:
        model= Product
        fields = '__all__'


class SimpleProductSettlementSerializer(serializers.ModelSerializer):
    sales = FloatRoundField()
    refund = FloatRoundField()
    other_fee = FloatRoundField()
    other_trade = FloatRoundField()
    income = FloatRoundField()
    profit = FloatRoundField()
    profit_rate = ProfitRateField()
    total_cost = FloatRoundField()
    subscription_fee = FloatRoundField()
    advertising_fee = FloatRoundField()
    storage_fee = FloatRoundField()

    class Meta:
        model = ProductSettlement
        exclude = ['settlement', 'product']


class ProductSettlementSerializer(SimpleProductSettlementSerializer):
    settlement = SettlementSerializer()
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductSettlement
        fields = '__all__'


class SimpleOrderItemSerializer(serializers.ModelSerializer):
    PostedDate = DateTimeFormat()
    Principal = FloatRoundField()
    Promotion = FloatRoundField()
    OtherPrice = FloatRoundField()
    Fee = FloatRoundField()
    income = FloatRoundField()
    profit = FloatRoundField()
    profit_rate = ProfitRateField(read_only=True)
    total_cost = FloatRoundField()
    storage_fee = FloatRoundField()
    subscription_fee = FloatRoundField()
    cost = FloatRoundField()

    class Meta:
        model = SettleOrderItem
        exclude = ['product']


class OrderItemSerializer(SimpleOrderItemSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = SettleOrderItem
        fields = '__all__'


class InboundShipmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = InboundShipment
        fields = '__all__'


class SimpleOutboundShipmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = OutboundShipment
        fields = '__all__'


class OutboundShipmentItemSerializer(serializers.ModelSerializer):
    shipment_id = serializers.IntegerField(source='shipment.id')
    unit_cost = FloatRoundField()
    total_freight = FloatRoundField()
    duty = FloatRoundField()

    class Meta:
        model = OutboundShipmentItem
        # fields = '__all__'
        exclude = ['shipment', 'product']


class OutboundShipmentSerializer(serializers.ModelSerializer):
    products = OutboundShipmentItemSerializer(many=True, read_only=True)

    class Meta:
        model = OutboundShipment
        fields = '__all__'


class AdvertisingItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdvertisingProductItems
        fields = '__all__'


class SimpleProductRemovalItemSerializer(serializers.ModelSerializer):
    UpdateDate = DateFormatField(read_only=True)
    profit = FloatRoundField()
    total_cost = FloatRoundField()
    cost = FloatRoundField()

    class Meta:
        model = ProductRemovalItem
        exclude = ['product']


class OrderTypeField(serializers.CharField):

    def to_representation(self, value):
        if value == 'Return':
            return u'买家退货'
        if value == 'Disposal':
            return u'弃置'
        return value


class DispositionField(serializers.CharField):

    def to_representation(self, value):
        if value == 'Sellable':
            return u'可销售'
        if value == 'Unsellable':
            return u'不可销售'


class ProductRemovalItemSerializer(SimpleProductRemovalItemSerializer):
    # product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductRemovalItem
        fields = '__all__'


class SimpleProductLostSerializer(serializers.ModelSerializer):
    PostedDate = DateTimeFormat(read_only=True)
    profit = FloatRoundField()
    profit_rate = ProfitRateField(read_only=True)
    Amount = FloatRoundField()
    total_cost = FloatRoundField()
    cost = FloatRoundField()
    TransactionType = TransactionTypeField(read_only=True)

    class Meta:
        model = OtherTransactionItem
        exclude = ['product']


class ProductLostSerializer(SimpleProductLostSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OtherTransactionItem
        fields = '__all__'


class SimpleRefundItemSerializer(serializers.ModelSerializer):
    PostedDate = DateTimeFormat(read_only=True)
    Principal = FloatRoundField()
    Promotion = FloatRoundField()
    OtherPrice = FloatRoundField()
    Fee = FloatRoundField()
    income = FloatRoundField()
    profit = FloatRoundField()
    profit_rate = ProfitRateField(read_only=True)
    cost = FloatRoundField()
    total_cost = FloatRoundField()

    class Meta:
        model = RefundItem
        exclude = ['product']


class RefundItemSerializer(SimpleRefundItemSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = RefundItem
        # fields = '__all__'
        exclude = ['product']


class DateTimezoneFormat(serializers.DateTimeField):

    def to_representation(self, value):
        if not value:
            return ''
        return (value + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M')


class GiftPackingSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    create_time = DateTimezoneFormat()

    class Meta:
        model = GiftPacking
        fields = '__all__'