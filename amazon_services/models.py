#-*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User


class Market(models.Model):
    """
    国家
    """
    id = models.CharField(max_length=10, primary_key=True)  # 市场编码，如en， ur
    cn = models.CharField(max_length=10)
    en = models.CharField(max_length=10)


class MarketAccount(models.Model):
    MarketplaceId = models.CharField(max_length=20, primary_key=True)
    country = models.CharField(max_length=10)   # 国家
    account = models.CharField(max_length=50, null=True, blank=True)   # 账户中文名称
    host = models.CharField(max_length=50)
    MWSAuthToken = models.CharField(max_length=15)
    AWSAccessKeyId = models.CharField(max_length=25)
    SellerId = models.CharField(max_length=20)
    SecretKey = models.CharField(max_length=50)
    currency_code = models.CharField(max_length=10)     # 货币编码
    exchange_rate = models.FloatField(default=6.0)      # 汇率
    period_start = models.DateField(null=True, blank=True)  # 结算周期起点
    period_days = models.IntegerField(default=14)       # 结算周期长度
    sync_report_status = models.IntegerField(default=0)     # 0:Finished， 1：Error， 10：Running


class ApiCategory(models.Model):
    """
    API大类
    """
    desc = models.CharField(max_length=20)        # 类别描述
    uri = models.CharField(max_length=100)      #
    version = models.CharField(max_length=10)   # API版本


class ApiActions(models.Model):
    """
    API动作
    """
    category = models.ForeignKey(ApiCategory, related_name='actions')   # 所属类别
    desc = models.CharField(max_length=20)      # 该动作的描述
    name = models.CharField(max_length=50)   # 动作
    params = models.TextField(null=True, blank=True)    # 参数的json格式，key为参数名，
                                                        # value为参数类型：int/string/datetime等
    max_requests = models.IntegerField(null=True, blank=True)            # 最大请求限制，为空表示无限制
    recover_interval = models.IntegerField(null=True, blank=True)        # 请求恢复的时间间隔，以秒计算
    recover_count = models.IntegerField(null=True, blank=True)           # 每次恢复的请求个数
    request_remain = models.IntegerField(null=True, blank=True)          # 还剩下多少次请求
    last_request = models.DateTimeField(null=True, blank=True)           # 上一次请求的时间


# class RequestRecords(models.Model):
#     """
#     请求记录
#     """
#     SUCCESS = 0
#     FAIL = 1   # 请求超过次数
#     PARSER_FAIL = 2     # 应答无法解析
#     # sender = models.ForeignKey(User)        # 请求发起人
#     market = models.ForeignKey(MarketAccount)
#     # action = models.ForeignKey(ApiActions, related_name='records')
#     uri = models.CharField(max_length=100)      # 请求的链接，即：action.uri
#     action = models.CharField(max_length=50, null=True, blank=True)    # 动作，action.name
#     params = models.TextField(null=True, blank=True)    # 参数，json格式
#     create_time = models.DateTimeField()        # 请求创建的时间
#     sent_time = models.DateTimeField(null=True, blank=True)   # 请求实际发送的时间
#     result = models.IntegerField(default=0)     # 请求结果，0：成功，1：失败
#     errors = models.TextField(null=True, blank=True)    # 失败信息


class ReportRequestRecord(models.Model):

    report_type = models.CharField(max_length=100)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    request_time = models.DateTimeField()       # 请求发起的时间
    request_report_id = models.CharField(max_length=50)
    report_id = models.CharField(max_length=50, null=True, blank=True)
