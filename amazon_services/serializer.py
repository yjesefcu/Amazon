__author__ = 'liucaiyun'
from rest_framework import serializers
from models import *


class MarketSerializer(serializers.ModelSerializer):
    currency = serializers.CharField(source='currency_code')

    class Meta:
        model = MarketAccount
        fields = ['country', 'currency', 'MarketplaceId']