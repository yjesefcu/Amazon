#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import re, logging, traceback


# logger = logging.getLogger('amazon')
try:
    import xml.etree.cElementTree as ET
    from xml.etree.ElementTree import Element
except ImportError:
    import xml.etree.ElementTree as ET


class BaseParser(object):

    def __init__(self, s):
        try:
            if s.endswith('.xml'):
                s = self._read_from_file(s)
            encoded = self._encode(s)
            self.root = ET.fromstring(encoded.encode('utf-8'))   # 从字符串传递xml
            self.ns = self._get_namespace(self.root)
            self.error_code = ''
            self.error_msg = ''
            self.items = []
            self.next_token = None
            if not self.is_error_response():
                self._parse()
        except Exception, e:
            # logger.warning('parse xml exception:%s', traceback.format_exc())
            traceback.format_exc(e)
            raise Exception(u'parse xml string exception')

    def is_error_response(self):
        if self.root.tag == '{0}ErrorResponse'.format(self.ns):
            # 失败的话获取失败信息
            self.error_code = self.find(self.root, 'Error/Code')
            self.error_msg = self.find(self.root, 'Error/Message')
            return True
        return False

    def errors(self):
        return self.error_code, self.error_msg

    def get_items(self):
        return self.items

    def get_next_token(self):
        return self.next_token

    def _read_from_file(self, f):
        file_object = open(f)
        try:
             all_the_text = file_object.read( )
        finally:
             file_object.close( )
        return all_the_text

    def _encode(self, s):
        """
        替换字符串中的特殊字符
        &lt;	<	小于
        &gt;	>	大于
        &amp;	&	和号
        &apos;	'	单引号
        &quot;	"	双引号
        """
        s = s.replace('&', '&amp;')
        return s

    def _get_namespace(self, root):
        m = re.match('\{.*\}', root.tag)
        if m and m.group(0):
            return m.group(0)[1: len(m.group(0))-1]
        return None

    def find(self, ele, tag, ns=None):
        """
        在命令空间中查找
        :param ele:
        :param tag:
        :param ns: 命名空间，如果ns为空，使用默认命名空间
        """
        if not ns:
            ns = self.ns
        if ns:
            tags = tag.split('/')
            namespace_tags = ['{%s}%s' % (ns, t) for t in tags]
            return ele.find('/'.join(namespace_tags))
        else:
            return ele.find(tag)

    def findall(self, ele, tag, ns=None):
        """
        在命令空间中查找
        :param ele:
        :param tag:
        :param ns: 命名空间，如果ns为空，使用默认命名空间
        """
        if not ns:
            ns = self.ns
        if ns:
            tags = tag.split('/')
            namespace_tags = ['{%s}%s' % (ns, t) for t in tags]
            return ele.findall('/'.join(namespace_tags))
        else:
            return ele.findall(tag)

    def _parse(self):
        pass


class RequestExceed(BaseParser):

    def __init__(self, s):
        if s.endswith('.xml'):
            s = self._read_from_file(s)
        try:
            encoded = self._encode(s)
            root = ET.fromstring(encoded.encode('utf-8'))   # 从字符串传递xml
            if re.match('\{.*\}ErrorResponse', root.tag) is None:
                self.is_exceed = False
            else:
                self.is_exceed = True
        except BaseException, ex:       # 如果返回的是text文本，则说明没有错误
            self.is_exceed = False


class OrderParse(BaseParser):

    def _parse(self):
        result = self.find(self.root, 'ListOrdersResult')
        if not result:
            result = self.find(self.root, 'ListOrdersByNextTokenResult')
        orders = self.findall(result, 'Orders/Order')
        for order in orders:
            self.items.append(self._parse_order_values(order))
        next_token = self.find(result, 'NextToken')
        if next_token is not None:
            self.next_token = next_token.text

    def _parse_order_values(self, order_element):
        fields = ['LatestShipDate', 'OrderType', 'PurchaseDate', 'AmazonOrderId', 'LastUpdateDate',
                  'IsReplacementOrder', 'ShipServiceLevel', 'OrderStatus', 'SalesChannel',
                  'NumberOfItemsUnshipped', 'IsPremiumOrder', 'MarketplaceId', 'FulfillmentChannel',
                  'IsPrime', 'SellerOrderId']
        order = dict()
        for field in fields:
            e = self.find(order_element, field)
            order[field] = e.text
        return order


class OrderItemParser(BaseParser):

    def _parse(self):
        result = self.find(self.root, 'ListOrderItemsResult')
        if not result:
            result = self.find(self.root, 'ListOrderItemsByNextTokenResult')
        items = self.findall(result, 'OrderItems/OrderItem')
        for item in items:
            item_parsed = self._parse_item_values(item)
            if item_parsed:
                self.items.append(item_parsed)
        next_token = self.find(result, 'NextToken')
        if next_token is not None:
            self.next_token = next_token.text

    def _parse_item_values(self, item_element):
        # if not self.find(item_element, 'ItemPrice'):    # 如果没有订单价格，说明该订单还未付款，则不计入实际订单中
        #     return None
        item = dict()
        item['QuantityOrdered'] = self.find(item_element, 'QuantityOrdered').text
        item['SellerSKU'] = self.find(item_element, 'SellerSKU').text
        item['ASIN'] = self.find(item_element, 'ASIN').text
        item['OrderItemId'] = self.find(item_element, 'OrderItemId').text
        if self.find(item_element, 'QuantityShipped') is not None:
            item['QuantityShipped'] = self.find(item_element, 'QuantityShipped').text
        if self.find(item_element, 'ItemPrice') is not None:
            item['ItemPrice'] = self.find(item_element, 'ItemPrice/Amount').text
        if self.find(item_element, 'ItemTax') is not None:
            item['ItemTax'] = self.find(item_element, 'ItemTax/Amount').text
        shipping_discount = self.find(item_element, 'ShippingDiscount/Amount')
        if shipping_discount is not None:
            item['ShippingDiscount'] = shipping_discount.text
        shipping_price = self.find(item_element, 'ShippingPrice/Amount')
        if shipping_price is not None:
            item['ShippingPrice'] = shipping_price.text
        shipping_tax = self.find(item_element, 'ShippingTax/Amount')
        if shipping_tax is not None:
            item['ShippingTax'] = shipping_tax.text
        if self.find(item_element, 'PromotionDiscount') is not None:
            item['PromotionDiscount'] = self.find(item_element, 'PromotionDiscount/Amount').text
        return item


class ProductParser(BaseParser):

    def _parse(self):
        results = self.findall(self.root, 'GetMatchingProductForIdResult')
        for result in results:
            if result.get('status') == 'Success':
                product_data = self.find(result, 'Products/Product')
                item_parsed = self._parse_item_values(product_data)
                if item_parsed:
                    item_parsed[result.get('IdType')] = result.get('Id')
                    self.items.append(item_parsed)

    def _parse_item_values(self, item_element):
        item = dict()
        item['ASIN'] = self.find(item_element, 'Identifiers/MarketplaceASIN/ASIN').text
        item['MarketplaceId'] = self.find(item_element, 'Identifiers/MarketplaceASIN/MarketplaceId').text
        # 获取商品属性
        ns2 = self.ns + '/default.xsd'
        attribute_sets = self.find(item_element, 'AttributeSets')
        attributes = self.find(attribute_sets, 'ItemAttributes', ns2)   # 在第二个命名空间中
        if self.find(attributes, 'Binding', ns2) is not None:
            item['Binding'] = self.find(attributes, 'Binding', ns2).text
        item['Brand'] = self.find(attributes, 'Brand', ns2).text
        if self.find(attributes, 'Color', ns2) is not None:
            item['Color'] = self.find(attributes, 'Color', ns2).text
        if self.find(attributes, 'ListPrice', ns2) is not None:
            item['Amount'] = self.find(attributes, 'ListPrice/Amount', ns2).text
            item['CurrencyCode'] = self.find(attributes, 'ListPrice/CurrencyCode', ns2).text
        item['package_width'] = self.find(attributes, 'PackageDimensions/Width', ns2).text
        item['package_height'] = self.find(attributes, 'PackageDimensions/Height', ns2).text
        item['package_length'] = self.find(attributes, 'PackageDimensions/Length', ns2).text
        if self.find(attributes, 'PackageDimensions/Weight', ns2) is not None:
            item['package_weight'] = self.find(attributes, 'PackageDimensions/Weight', ns2).text
        item['ProductGroup'] = self.find(attributes, 'ProductGroup', ns2).text
        item['ProductTypeName'] = self.find(attributes, 'ProductTypeName', ns2).text
        item['Title'] = self.find(attributes, 'Title', ns2).text
        item['Image'] = self.find(attributes, 'SmallImage/URL', ns2).text
        return item


class RequestReportParser(BaseParser):

    def __init__(self, s):
        self.report_id = None
        super(RequestReportParser, self).__init__(s)

    def _parse(self):
        result = self.find(self.root, 'RequestReportResult')
        self.report_id = self.find(result, 'ReportRequestInfo/ReportRequestId').text

    def get_report_id(self):
        return self.report_id


class ReportListParser(BaseParser):
    """
    解析GetReportList的应答
    """

    def _parse(self):
        result = self.find(self.root, 'GetReportListResult')

        for report in self.findall(result, 'ReportInfo'):
            self.items.append(self._parse_item_values(report))
        next_token = self.find(result, 'NextToken')
        if next_token is not None:
            self.next_token = next_token.text

    def _parse_item_values(self, item_element):
        item = dict()
        item['ReportType'] = self.find(item_element, 'ReportType').text
        item['Acknowledged'] = self.find(item_element, 'Acknowledged').text
        item['ReportId'] = self.find(item_element, 'ReportId').text
        item['ReportRequestId'] = self.find(item_element, 'ReportRequestId').text
        item['AvailableDate'] = self.find(item_element, 'AvailableDate').text
        return item


class SettlementReportParser(BaseParser):
    """
    解析GetReportList的应答
    """
    def __init__(self, s):
        self.SettlementData = dict()
        self.Orders = list()    # 订单列表
        self.Refunds = list()   # 退款列表
        self.OtherTransactions = list()    # 服务费列表
        self.SellerDealPayment = list()
        self.AdvertisingTransactionDetails = list()
        self.SellerCouponPayment = list()   # 优惠券
        super(SettlementReportParser, self).__init__(s)

    def _parse(self):
        report = self.find(self.root, 'Message/SettlementReport')
        if report is None:
            return
        self.SettlementData = self._parse_settlement_data(self.find(report, 'SettlementData'))
        for ele in self.findall(report, 'Order'):
            self.Orders.append(self._parse_order(ele))
        for ele in self.findall(report, 'Refund'):
            self.Refunds.append(self._parse_refund(ele))
        for ele in self.findall(report, 'OtherTransaction'):
            self.OtherTransactions.append(self._parse_transaction(ele))
        for ele in self.findall(report, 'SellerDealPayment'):
            self.SellerDealPayment.append(self._parse_deal_payment(ele))
        for ele in self.findall(report, 'AdvertisingTransactionDetails'):
            self.AdvertisingTransactionDetails.append(self._parse_advertising_transaction(ele))
        for ele in self.findall(report, 'SellerCouponPayment'):
            self.SellerCouponPayment.append(self._parse_coupon_payment(ele))
        self.items = {
            'SettlementData': self.SettlementData,
            'Order': self.Orders,
            'Refund': self.Refunds,
            'OtherTransactions': self.OtherTransactions,
            'SellerDealPayment': self.SellerDealPayment,
            'AdvertisingTransactionDetails': self.AdvertisingTransactionDetails,
            'SellerCouponPayment': self.SellerCouponPayment
        }

    def _parse_settlement_data(self, element):
        settlement = dict()
        settlement['AmazonSettlementID'] = self.find(element, 'AmazonSettlementID').text
        settlement['TotalAmount'] = self.find(element, 'TotalAmount').text
        settlement['currency'] = self.find(element, 'TotalAmount').get('currency')
        settlement['StartDate'] = self.find(element, 'StartDate').text
        settlement['EndDate'] = self.find(element, 'EndDate').text
        return settlement

    def _parse_order(self, element):
        order = dict()
        order['AmazonOrderId'] = self.find(element, 'AmazonOrderID').text
        order['ShipmentID'] = self.find(element, 'ShipmentID').text
        order['MarketplaceName'] = self.find(element, 'MarketplaceName').text
        # 获取订单商品详细信息
        fulfillment = self.find(element, 'Fulfillment')
        order['PostedDate'] = self.find(fulfillment, 'PostedDate').text
        items = list()
        for item_ele in self.findall(fulfillment, 'Item'):
            items.append(self._parse_order_item(item_ele))
        order['items'] = items
        return order

    def _parse_order_item(self, ele):
        # Order/Fulfillment/Item
        item = dict()
        item['OrderItemId'] = self.find(ele, 'AmazonOrderItemCode').text
        item['SellerSKU'] = self.find(ele, 'SKU').text
        item['Quantity'] = self.find(ele, 'Quantity').text
        price_total = 0
        for component in self.findall(ele, 'ItemPrice/Component'):  # 获取商品总价和运费
            if self.find(component, 'Type').text == 'Principal':
                item['Principal'] = self.find(component, 'Amount').text
            else:
                price_total += float(self.find(component, 'Amount').text)
        item['OtherPrice'] = price_total
        if self.find(ele, 'ItemFees') is not None:      # 亚马逊物流基础服务费
            fee_total = 0
            for fee in self.findall(ele, 'ItemFees/Fee'):
                fee_total += float(self.find(fee, 'Amount').text)
            item['Fee'] = fee_total
        promotion_total = 0
        for promotion in self.findall(ele, 'Promotion'):    # 促销返点
            promotion_total += float(self.find(promotion, 'Amount').text)
        item['Promotion'] = promotion_total
        return item

    def _parse_refund(self, element):
        # Refund
        refund = dict()
        refund['AmazonOrderId'] = self.find(element, 'AmazonOrderID').text
        refund['MarketplaceName'] = self.find(element, 'MarketplaceName').text
        refund['AdjustmentID'] = self.find(element, 'AdjustmentID').text
        fulfillment = self.find(element, 'Fulfillment')
        refund['PostedDate'] = self.find(fulfillment, 'PostedDate').text
        items = list()
        for adjusted_item in self.findall(fulfillment, 'AdjustedItem'):
            items.append(self._parse_refund_adjusted_item(adjusted_item))
        refund['items'] = items
        return refund

    def _parse_refund_adjusted_item(self, element):
        # Refund/Fulfillment/AdjustedItem
        item = dict()
        item['OrderItemId'] = self.find(element, 'AmazonOrderItemCode').text
        item['MerchantAdjustmentItemID'] = self.find(element, 'MerchantAdjustmentItemID').text
        item['SellerSKU'] = self.find(element, 'SKU').text
        if self.find(element, 'ItemPriceAdjustments') is not None:
            total = 0    # 除了Principal和Shipping以外的退款
            for component in self.findall(element, 'ItemPriceAdjustments/Component'):
                # PriceAdjustmentType 退款类型，有很多种
                t = self.find(component, 'Type').text
                value = self.find(component, 'Amount').text
                if t == 'Principal':
                    item['Principal'] = value
                else:
                    total += float(value)
            item['OtherPrice'] = total
        if self.find(element, 'ItemFeeAdjustments') is not None:
            total = 0
            for fee in self.findall(element, 'ItemFeeAdjustments/Fee'):
                # item[self.find(fee, 'Type').text] = self.find(fee, 'Amount').text
                total += float(self.find(fee, 'Amount').text)
            item['Fee'] = total
        promotion_total = 0
        for promotion in self.findall(element, 'PromotionAdjustment'):
            # t = 'Promotion' + self.find(promotion, 'Type').text
            # item[t] = self.find(promotion, 'Amount').text
            promotion_total += float(self.find(promotion, 'Amount').text)
        item['Promotion'] = promotion_total
        return item

    def _parse_transaction(self, element):
        transaction = dict()
        if self.find(element, 'AmazonOrderID') is not None:
            transaction['AmazonOrderId'] = self.find(element, 'AmazonOrderID').text
        transaction['TransactionType'] = self.find(element, 'TransactionType').text
        transaction['TransactionID'] = self.find(element, 'TransactionID').text
        transaction['PostedDate'] = self.find(element, 'PostedDate').text
        transaction['Amount'] = self.find(element, 'Amount').text
        if self.findall(element, 'Fees/Fee') is not None:
            fees = list()
            for fee in self.findall(element, 'Fees/Fee'):
                fees.append({
                    'Type': self.find(fee, 'Type').text,
                    'Amount': self.find(fee, 'Amount').text
                })
                transaction['fees'] = fees
        if self.findall(element, 'OtherTransactionItem') is not None:
            # 服务子项，一般指赔偿类
            items = list()
            for item in self.findall(element, 'OtherTransactionItem'):
                items.append({
                    'SellerSKU': self.find(item, 'SKU').text,
                    'Quantity': self.find(item, 'Quantity').text,
                    'Amount': self.find(item, 'Amount').text
                })
                transaction['items'] = items
        return transaction

    def _parse_deal_payment(self, element):
        # SellerDealPayment
        deal_payment = dict()
        deal_payment['MarketplaceName'] = self.find(element, 'MarketplaceName').text
        deal_payment['PostedDate'] = self.find(element, 'PostedDate').text
        deal_payment['TransactionType'] = self.find(element, 'TransactionType').text
        deal_payment['PaymentReason'] = self.find(element, 'PaymentReason').text
        deal_payment['DealID'] = self.find(element, 'DealID').text
        deal_payment['DealDescription'] = self.find(element, 'DealDescription').text
        deal_payment['DealFeeType'] = self.find(element, 'DealFee/Type').text
        deal_payment['DealFeeAmount'] = self.find(element, 'DealFee/Amount').text
        return deal_payment

    def _parse_advertising_transaction(self, element):
        # AdvertisingTransactionDetails
        advertising = dict()
        advertising['TransactionType'] = self.find(element, 'TransactionType').text
        advertising['PostedDate'] = self.find(element, 'PostedDate').text
        advertising['InvoiceId'] = self.find(element, 'InvoiceId').text
        advertising['BaseAmount'] = self.find(element, 'BaseAmount').text
        advertising['TransactionAmount'] = self.find(element, 'TransactionAmount').text
        return advertising

    def _parse_coupon_payment(self, element):
        coupon = dict()
        coupon['PostedDate'] = self.find(element, 'PostedDate').text
        coupon['Amount'] = self.find(element, 'CouponFee').find('Amount').text
        coupon['Count'] = self.find(element, 'Count').text
        return coupon


if __name__ == '__main__':
    # from file_utils import get_file_content
    # content = get_file_content('7548637834017515', '7548637834017515.xml')
    f = open('1117-1201.xml', 'rb')
    content = ''.join(f.readlines())
    parser = SettlementReportParser(content)
    orders = parser.items['Order']
    for order in orders:
        if order['AmazonOrderId'] == '112-9507060-2421826':
            pass
    parser.items
    # print parser.is_error_response()
    # print parser.get_orders()
    # print parser.get_next_token()