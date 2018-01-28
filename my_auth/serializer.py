__author__ = 'liucaiyun'
from django.contrib.auth.models import User
from rest_framework import serializers


class DateTimeFormat(serializers.DateTimeField):

    def to_representation(self, value):
        if not value:
            return ''
        return value.strftime('%Y-%m-%d %H:%M:%S')


class UserSerializer(serializers.ModelSerializer):

    date_joined = DateTimeFormat(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'date_joined']