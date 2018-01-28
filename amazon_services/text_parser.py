#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
from exception import TextParseException


class BaseTextParser(object):
    """
    对制表符文本格式的数据进行解析
    """

    def __init__(self, s):
        self.lines = list()
        lines = s.split('\r\n')
        # 第一行作为关键字
        try:
            keys = lines[0].strip().split('\t')
            for l in lines[1:]:
                values = l.strip().split('\t')
                if len(values) < len(keys):
                    continue
                i = 0
                item = dict()
                while i < len(keys):
                    item[keys[i]] = values[i]
                    i += 1
                self.lines.append(item)
            self.items = list()
            self._parse()
        except Exception, ex:
            raise TextParseException('text parser exception:%s', s)

    def _parse(self):
        pass

    def get_items(self):
        return self.items


class InventorySummaryParser(BaseTextParser):
    """
    物流库存事件详情报告  解析
    """

    def _parse(self):

        for item in self.lines:
            snap_date, transaction_type, sku, fulfillment, quantity, disposition = item
            self.items.append({
                'UpdateDate': snap_date,
                'TransactionType': transaction_type,
                'SellerSKU': sku,
                'Quantity': quantity,
                'Disposition': disposition
            })


class ProductRemovalParser(BaseTextParser):
    """
    商品移除表
    """
    def _parse(self):
        for item in self.lines:
            self.items.append({
                'RequestDate': item['request-date'],
                'UpdateDate': item['last-updated-date'],
                'OrderId': item['order-id'],
                'OrderType': item['order-type'],
                'OrderStatus': item['order-status'],
                'SellerSKU': item['sku'],
                'FNSKU': item['fnsku'],
                'Quantity': item['requested-quantity'],
                'Disposition': item['disposition'],
                'Fee': item['removal-fee']
            })


class AdvertisingParser(BaseTextParser):
    # 广告业绩表
    def _parse(self):
        for item in self.lines:
            self.items.append({
                'StartDate': item['Start Date'],
                'EndDate': item['End Date'],
                'SellerSKU': item['SKU'],
                'TotalSpend': item['Total Spend']
            })


class MonthlyStorageFeeParser(BaseTextParser):
    """
    月度仓储费解析
    """
    def _parse(self):
        for item in self.lines:
            self.items.append({
                'ASIN': item['asin'],
                'ChargeDate': item['month-of-charge'],
                'Fee': item['estimated-monthly-storage-fee']
            })


if __name__ == '__main__':
    f = open('text.txt', 'rb')
    string = f.readlines()
    f.close()
    parser = InventorySummaryParser(string)
    items = parser.get_items()
    print items