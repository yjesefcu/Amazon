#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
from .models import MarketAccount


def send_request(market_id, action_desc, params):
    """
    向amazon发送请求
    :param market_id: 市场编码
    :param action_desc: action描述，ApiAction.desc
    :param params: 参数
    :return:
    """
    pass


exchange_rate = None


def get_exchange_rate():
    # 获取汇率

    global exchange_rate
    if exchange_rate:
        return exchange_rate
    account = MarketAccount.objects.get(MarketplaceId='ATVPDKIKX0DER')
    return account.exchange_rate
