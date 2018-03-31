#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import requests, urllib, base64, hmac, hashlib, traceback, time, logging, threading, Queue, json
# from requests.packages.urllib3.exceptions import InsecureRequestWarning
import datetime
from Queue import Queue
from xml_parser import *
from text_parser import *
from models import ReportRequestRecord
from exception import *
from file_utils import save_file, get_file_content
from exception import FileNotExist
logger = logging.getLogger('amazon')
# 禁用安全请求警告
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


HOST = 'mws.amazonservices.com'

DT_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class OrderQueueHandle(threading.Thread):

    def __init__(self, target, args):
        super(OrderQueueHandle, self).__init__(target=target, args=args)
        self.queue = Queue.Queue

    def run(self):
        order = self.queue.get(block=True)
        while order:
            #
            order = self.queue.get(block=True)
        pass

    def add_order(self, order):
        """
        添加订单信息
        :param order: 从amazon查询回来的订单信息
        """
        self.queue.put(order)


class AmazonService(object):
    queue_size = 0
    interval = 0

    @property
    def _queue(self):
        if not self.msg_queue:
            self.msg_queue = Queue(maxsize=self.queue_size)
            for i in range(0, self.queue_size):
                self.msg_queue.put(1)
        return self.msg_queue

    def _request_exceed(self):      # 请求数超出时清空队列

        def _recover_func():
            while True:
                while self.msg_queue.qsize() == self.queue_size:
                    time.sleep(10)
                time.sleep(self.interval)
                self._queue.put(1)
                logger.info('queue recover one: %s', self.__class__.__name__)
                if self._queue.qsize() == self.queue_size:
                    logger.info('request recover')
                    self.recover_thread = None
                    break
        logger.info('request exceed')
        # 清空队列
        for i in range(0, self._queue.qsize()):
            self._queue.get()
        # 开始计数线程
        if self.recover_thread is None:
            logger.info('start recover thread: %s', self.__class__.__name__)
            self.recover_thread = threading.Thread(target=_recover_func)
            self.recover_thread.start()

    def __init__(self, market_account=None):
        self.market = market_account
        self.host = market_account.host if market_account else HOST
        self.SecretKey = market_account.SecretKey #if market_account else SecretKey
        self.MarketplaceId = market_account.MarketplaceId #if market_account else Marketplace_EN
        self.default = {
            'AWSAccessKeyId': market_account.AWSAccessKeyId, #if market_account else AWSAccessKeyId,
            'MWSAuthToken': market_account.MWSAuthToken, #if market_account else MWSAuthToken,
            'MarketplaceId.Id.1': self.MarketplaceId,
            'SellerId': market_account.SellerId, # if market_account else SellerId,
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2'
        }
        self.last_post_time = None

    def post(self, uri, action, param=None, api_version='2013-09-01'):
        try:
            logger.info('start post: %s, action=%s', self.__class__.__name__, action)
            if self._queue.qsize() > 0:
                self._queue.get(block=True)
                logger.info('you can post: %s', self.__class__.__name__)
                r = self._post(uri, action, param, api_version)
                return r
            else:
                logger.info('request cannot post: %s, action=%s', self.__class__.__name__, action)
                self._request_exceed()
                self._queue.get(block=True)
                return self._post(uri, action, param, api_version)
        except RequestExceedException, ex:
            logger.info('request exceed: %s, action=%s', self.__class__.__name__, action)
            self._request_exceed()
            self._queue.get(block=True)
            return self.post(uri, action, param, api_version)

    def _post(self, uri, action, param=None, api_version='2013-09-01'):
        if not param:
            param = dict()
        parameters = {
            'Timestamp': datetime.datetime.utcnow().strftime(DT_FORMAT),
            'Version': api_version,     # API版本
            'Action': action,
        }   # 加上请求需要的参数
        parameters = dict(self.default.items() + parameters.items() + param.items())
        signature = self.create_signature(uri, parameters)
        parameters['Signature'] = signature
        form_data = '&'.join([key+'='+self._url_encode(value) for (key, value) in parameters.items()])
        url = 'https://%s%s?%s' % (self.host, uri, form_data)
        try:
            r = requests.post(url, verify=False, headers={'Connection': 'close'})
            if RequestExceed(r.text).is_exceed:
                    raise RequestExceedException()
            logger.info('post return success: %s, action=%s, status=%d',
                        self.__class__.__name__, action, r.status_code)
            return r
        except Exception, ex:
            traceback.format_exc()
            logger.warning('post exception: %s, action=%s, exception=%s', self.__class__.__name__, action,
                           traceback.format_exc())

        return None

    def create_signature(self, uri, params):
        """
        签名生成器
        :param method 请求方法,POST/GET
        :param action： 服务接口
        :param params:  请求所需参数
        """
        host = self.host
        query_items = params.items()
        query_items.sort()
        form_data = '&'.join([key + '=' + self._url_encode(value) for (key, value) in query_items])
        url = '%s\n%s\n%s\n%s' % ('POST', host, uri, form_data)
        message = bytes(url).encode('utf-8')
        secret = bytes(self.SecretKey).encode('utf-8')
        signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
        return signature

    def _get_api_interval_time(self):
        """
        获取api规定的间隔时间，单位s
        """
        return 0

    @classmethod
    def _url_encode(cls, s):
        return urllib.quote(s).replace('/', '%2F').replace('%7E', '~')


class OrderService(AmazonService):

    def __init__(self, market_account=None):
        super(OrderService, self).__init__(market_account)
        self.order_item_service = OrderItemService()

    def get_orders(self, last_update_time):
        """
        获取订单列表
        :param last_update_time: 字符串格式
        :return:
        """
        return self._get_next_token(last_update_time=last_update_time)

    def _get_next_token(self, last_update_time=None, next_token=None):
        if last_update_time:
            r = self.post('/Orders/2013-09-01', 'ListOrders',
                      {'LastUpdatedAfter': last_update_time})
        else:
            r = self.post('/Orders/2013-09-01', 'ListOrdersByNextToken', {'NextToken': next_token})
        try:
            parser = OrderParse(r.text)
        except Exception, ex:
            traceback.format_exc()
            print r.text
            return None
        orders = parser.get_items()
        if parser.get_next_token():
            next_orders = self._get_next_token(next_token=parser.get_next_token())
            if next_orders:
                orders.extend(next_orders)
        return orders

    def _get_api_interval_time(self):
        return 60


class OrderItemService(AmazonService):

    msg_queue = None
    recover_thread = None
    interval = 2.1
    queue_size = 30

    def list_items(self, amazon_order_id):
        return self._get_next_token(amazon_order_id=amazon_order_id)

    def _get_next_token(self, amazon_order_id=None, next_token=None):
        if amazon_order_id:
            r = self.post('/Orders/2013-09-01', 'ListOrderItems',
                      {'AmazonOrderId': amazon_order_id})
        else:
            r = self.post('/Orders/2013-09-01', 'ListOrderItemsByNextToken', {'NextToken': next_token})
        if not r:
            logger.error('GetMatchingProductForId except. ')
            return None
        try:
            parser = OrderItemParser(r.text)
        except Exception, ex:
            traceback.format_exc()
            logger.warning('OrderItemService parse failed: %s', r.text)
            return None
        items = parser.get_items()
        if parser.get_next_token():
            next_items = self._get_next_token(next_token=parser.get_next_token())
            if next_items:
                items.extend(next_items)
        return items

    def _get_api_interval_time(self):
        return 1


class RequestReportService(AmazonService):

    msg_queue = None
    recover_thread = None
    interval = 61
    queue_size = 15

    def request(self, report_type, start_time=None, end_time=None):
        try:
            exist_request = ReportRequestRecord.objects.get(report_type=report_type, start_time=start_time, end_time=end_time)
            return exist_request.request_report_id
        except ReportRequestRecord.DoesNotExist, ex:
            pass
        param = {
            'ReportType': report_type
        }
        if start_time:
            param['StartDate'] = start_time.strftime(DT_FORMAT)
        if end_time:
            param['EndDate'] = end_time.strftime(DT_FORMAT)
        logger.info('Start request report, type=%s, StartDate:%s, EndDate:%s', report_type, start_time, end_time)
        r = self.post('/', 'RequestReport', param, api_version='2009-01-01')
        request_report_id = RequestReportParser(r.text).get_report_id()
        ReportRequestRecord.objects.create(report_type=report_type, start_time=start_time, end_time=end_time,
                                           request_time=datetime.datetime.now(), request_report_id=request_report_id)
        logger.info('end request report, type=%s, StartDate:%s, EndDate:%s, RequestReportId:%s',
                    report_type, start_time, end_time, request_report_id)
        return request_report_id


class ListReportService(AmazonService):

    msg_queue = None
    recover_thread = None
    interval = 61
    queue_size = 10

    def list_report(self, request_type):
        r = self.post('/', 'GetReportList', {
            'ReportTypeList.Type.1': request_type,
            'MaxCount': '15'
        }, api_version='2009-01-01')
        if r:
            return ReportListParser(r.text).get_items()
        return None


class GetReportService(AmazonService):

    msg_queue = None
    recover_thread = None
    interval = 61
    queue_size = 15

    def get_report(self, report_id):
        """
        获取报告内容
        :param report_id:
        :return: 返回response对象
        """
        logger.info('Start get report by ReportId:　%s', report_id)
        r = self.post('/', 'GetReport', {
            'ReportId': report_id
        }, api_version='2009-01-01')
        logger.info('End get report by ReportId:　%s', report_id)
        return r


class ProductService(AmazonService):

    msg_queue = None
    recover_thread = None
    interval = 2
    queue_size = 20

    def get_products(self, sku_list):
        """
        获取商品信息列表
        :param asin_list: SellerSKU列表，不超过5个
        """
        if len(sku_list) > 5:
            return
        param = {'IdType': 'SellerSKU', 'MarketplaceId': self.MarketplaceId}
        i = 1
        for id in sku_list:
            key = 'IdList.Id.%d' % i
            param[key] = id
            i += 1
        r = self.post('/Products/2011-10-01', 'GetMatchingProductForId',
                      param, api_version='2011-10-01')
        if not r:
            logger.error('GetMatchingProductForId except. ')
            return None
        try:
            parser = ProductParser(r.text)
        except Exception, ex:
            traceback.format_exc()
            logger.warning('GetMatchingProductForId parse failed: %s', r.text)
            return None
        items = parser.get_items()
        return items

    def _get_api_interval_time(self):
        return 1


class BaseReportService(AmazonService):

    def __init__(self, market):
        super(BaseReportService, self).__init__(market)
        self._request_service = RequestReportService(market)
        self._list_service = ListReportService(market)
        self._get_service = GetReportService(market)

    def request_report(self, report_type, start_time=None, end_time=None):
        """
        请求报告
        :param report_type: 报告类型
        :param start_time: 报告的起始时间
        :param end_time: 报告的截止时间
        :return: RequestReportId
        """
        # 如果数据库中已有记录，则不重复请求
        return self._request_service.request(report_type, start_time, end_time)

    def _check_report_done(self, report_type, request_report_id, max_try=3, interval=60):
        """
        检查报告是否生成
        :param report_type: 报告类型
        :param request_report_id: 请求id
        :param max_try: 最多尝试次数
        :param interval: 每次等待的间隔时间
        :return: 返回reportID，如果尝试max_try次以后还未生成报告，则返回None
        """
        # 如果数据库中已存在，则不重复请求
        try:
            exist_request = ReportRequestRecord.objects.get(report_type=report_type, request_report_id=request_report_id)
            if exist_request.report_id:
                return exist_request.report_id
        except ReportRequestRecord.DoesNotExist, ex:
            pass
        time.sleep(interval)
        report_id = self._get_report_id(report_type, request_report_id)
        count = 1
        while not report_id and count < max_try:
            time.sleep(interval)
            report_id = self._get_report_id(report_type, request_report_id)
            count += 1
        if report_id:
            try:
                rrr = ReportRequestRecord.objects.get(request_report_id=request_report_id)
                rrr.report_id = report_id
                rrr.save()
            except ReportRequestRecord.DoesNotExist, ex:
                logger.warning('ReportRequestRecord with request report id: %s does not exist')
        return report_id

    def list_report(self, report_type):
        return self._list_service.list_report(report_type)

    def _get_report_id(self, report_type, request_report_id):
        """
        获取报告id，如果报告未生成，则返回Node
        :param request_report_id:
        :return:
        """
        items = self._list_service.list_report(report_type)
        # 如果report_id在reportList中存在，说明报告已经准备好了
        for report in items:
            if report['ReportRequestId'] == request_report_id:
                return report['ReportId']
        return None

    def get_by_report_id(self, report_id):
        """
        获取报告内容
        :param report_id:
        :return: 返回response对象
        """
        return self._get_service.get_report(report_id)

    def _get_api_interval_time(self):
        return 60


class SettlementReportService(BaseReportService):
    """
    结算报告
    """

    def get_list(self):
        """
        获取结算报告列表
        """
        return self._list_service.list_report('_GET_V2_SETTLEMENT_REPORT_DATA_XML_')

    def get_one(self, report_id):
        """
        根据ReportId获取单个报告的xml信息
        :param report_id:
        """
        # 如果本地存在，则不再重复读取
        try:
            content = get_file_content(report_id, report_id + '.xml')
        except FileNotExist, ex:
            r = self._get_service.get_report(report_id)
            content = r.text
            # 保存到本地
            save_file(content, report_id, report_id + '.xml')
        try:
            parser = SettlementReportParser(content)
        except Exception, ex:
            traceback.format_exc()
            logger.warning('SettlementReport parse failed: %s', content)
            return None
        # 不获取NextToken的值
        items = parser.get_items()
        return items


class AdvertiseReportService(BaseReportService):
    """
    广告账单报告
    """

    def request_by_day(self, day):
        # 只发起请求
        return self._request_service.request('_GET_PADS_PRODUCT_PERFORMANCE_OVER_TIME_DAILY_DATA_TSV_', day)

    def request_by_week(self, day):
        # 只发起请求
        return self._request_service.request('_GET_PADS_PRODUCT_PERFORMANCE_OVER_TIME_WEEKLY_DATA_TSV_', day)

    def get_items_by_report_id(self, report_id, start_day=None):
        # 保存到本地的文件名
        if start_day:
            name = 'week_%s_%s.txt' % (start_day, report_id)
        else:
            name = 'week_%s.txt' % report_id
        content = get_file_content('advertising', name)
        if not content:
            r = self.get_by_report_id(report_id)
            # 保存到本地
            save_file(r.text, 'advertising', name)
            content = r.text
        parser = AdvertisingParser(content)
        return parser.get_items()

    def get_by_day(self, day, request_report_id=None):
        """
        请求广告日报告
        """
        return self._get_advertising_report('_GET_PADS_PRODUCT_PERFORMANCE_OVER_TIME_DAILY_DATA_TSV_', day, request_report_id)

    def get_by_week(self, start_day, request_report_id=None):
        """
        请求广告周报告，起始时间必须是周日
        day：起始时间，必须是周日
        """
        return self._get_advertising_report('_GET_PADS_PRODUCT_PERFORMANCE_OVER_TIME_WEEKLY_DATA_TSV_', start_day, request_report_id)

    def _get_advertising_report(self, report_type, start_day, request_report_id=None):
        """
        :param type: 类型
        :param start_day: 时间
        """
        if not request_report_id:
            request_report_id = self._request_service.request(report_type, start_day)
        report_id = self._check_report_done(report_type, request_report_id)
        if report_id:
            return self.get_items_by_report_id(report_id, start_day)
        return None


if __name__ == '__main__':
    # token = 'pXPDw7T+Fup/YYuZQbKv1QafEPREmauvizt1MIhPYZbaSgEpfAaYkXTkBHvJ93W/XVvMiz84ZXbNeGyEmOrLe7q8xqAchQNKtU38YwqRuVIwqcbUqh/LhCJ0wMvlylZkE3RvwDUQBA1G6ShfNgiExkSDtsD4aPvQcv0UYHXV8K5jpIXqERozsh35jNz11rwFKFx4/9h+5BG5ki8QZ/nAov0IfGeAvb95J/gMIjfO756fpVJGS+vu5pFHMXy6XL5lQW8Xd/Zkc1SuQyquFjSkBowoP8liP7H3sJdJobvDtjbZkLh8ZQWZdmTZrNwXH6VTGi/TbfXVDR7tObdzBnmaYnGsHLYYIfzBGxpr1p/cLrO96kATpJ2Ci+OjokijmI8Bbe7jhwcQGngpvkbRUhFumapDFyJ4Aaz0lmrLJ6gfmjoSyoYkkmy7z4+envNcHi41tHdkruHJ4Z15itQRr/9F9A=='
    # r = AmazonService().post('/Orders/2013-09-01', 'ListOrders', {'LastUpdatedAfter': '2017-05-01T00:00:00Z'})
    # r = AmazonService().post('/Orders/2013-09-01', 'ListOrdersByNextToken', {'NextToken': token})
    # r = AmazonService().post('/Orders/2013-09-01', 'ListOrdersByNextToken', {'NextToken': token})
    # print r.text
    # # r = AmazonService().post('/Products/2011-10-01', 'ListMatchingProducts',
    # #                          {'Query': 'MLA000153-SG', 'MarketplaceId': Marketplace_EN}, api_version='2011-10-01').text
    # print r.text
    # pass
    # print OrderService(None).get_orders('2017-05-01T00:00:00Z')
    # print OrderItemService(None).list_items('114-6870523-5093814')
    # print ProductService(None).get_products(['MLA000125', 'MLA000327'])
    # print SettlementReportService().get_items()
    start = datetime.datetime(year=2017, month=5, day=20)
    end = datetime.datetime(year=2017, month=6, day=10)

    # file_object = open('orders.txt')
    # try:
    #      all_the_text = file_object.read( )
    # finally:
    #      file_object.close( )
    # import json
    # orders = json.loads(all_the_text)
    # print 'order length: %d' % len(orders)
    # amazon_sell_id = [o['AmazonOrderId'] for o in orders]
    # print 'AmazonOrderId length: %d' % len(set(amazon_sell_id))
    # amazon_sell_id = [o['SellerOrderId'] for o in orders]
    # print 'SellerOrderId length: %d' % len(set(amazon_sell_id))
    SettlementReportService().get_one('5169113822017305')