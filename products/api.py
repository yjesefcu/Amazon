#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import os, datetime, urllib, json, logging, traceback, time, threading
from PIL import Image
from random import Random
import dateutil.parser
from django.conf import settings
from django.db.models import Q, F, Sum
from amazon_services.service import OrderService, OrderItemService
from models import *
from errors import Error


logger = logging.getLogger('product')
DT_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
DB_DT_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_public_product(SellerSKU):
    product, created = Product.objects.get_or_create(MarketplaceId="public", SellerSKU=SellerSKU)
    return product


def get_or_create_product(MarketplaceId, SellerSKU):

    def _copy_product(pp):
        new_p = Product()
        fields = ['SellerSKU', 'ASIN', 'FNSKU', 'Brand', 'Color', 'Image', 'Title', 'TitleCn', 'ProductGroup',
                  'width', 'height', 'length', 'weight', 'package_width', 'package_height', 'package_length', 'package_weight',
                  'volume_weight', 'gifts']
        new_p.MarketplaceId = MarketplaceId
        for field in fields:
            setattr(new_p, field, getattr(pp, field))
        return new_p

    try:
        product = Product.objects.get(MarketplaceId=MarketplaceId, SellserSKU=SellerSKU)
    except Product.DoesNotExist, ex:
        Product.objects.get_or_create(MarketplaceId="public", SellerSKU=SellerSKU)
        product, created = Product.objects.get_or_create(MarketplaceId=MarketplaceId, SellerSKU=SellerSKU)
    return product


def get_float_from_model(instance, field):
    # 从数据库对象中读取某个字段的浮点值
    if not instance or not hasattr(instance, field):
        return 0
    return to_float(getattr(instance, field))


def to_float(value):
    if not value:
        return 0
    return float(value)


def to_int(value):
    if not value:
        return 0
    return int(value)


def sum_fields(items, fields, result_item=None):
    # 计算多条记录的多个字段的求和，并将最后结果付给result_item
    total = {}
    for field in fields:
        total[field] = 0
    for item in items:
        for field in fields:
            total[field] += to_float(getattr(item, field))
    if result_item:
        for field in fields:
            setattr(result_item, field, total.get(field))
        result_item.save()
    return total


def sum_queryset(query_set, field, is_integer=False):
    if is_integer:
        return to_int(query_set.aggregate(total=Sum(field)).get('total'))
    return to_float(query_set.aggregate(total=Sum(field)).get('total'))


def get_float(data, key):
    value = data.get(key)
    if not value:
        return 0
    return float(value)


def update_product_to_db(product_data):
    """
    """
    try:
        public_product = Product.objects.get(MarketplaceId="public", SellerSKU=product_data['SellerSKU'])
        product = get_or_create_product(MarketplaceId=product_data['MarketplaceId'],
                                                         SellerSKU=product_data['SellerSKU'])
        for key, value in product_data.items():
            setattr(public_product, key, value)
            setattr(product, key, value)
        # 计算体积重
        public_product.volume_weight = float(public_product.package_width) * float(public_product.package_height) \
                                * float(public_product.package_length) / 5000
        public_product.save()
        if not public_product.Image:
            # 下载image到本地
            image = download_image(product_data['Image'])
            if image:
                product_data['Image'] = image
                public_product.Image = image
                public_product.save()
        # 同步到市场商品中
        product.volume_weight = public_product.volume_weight
        product.Image = public_product.Image
        product.save()

    except BaseException, ex:
        traceback.format_exc()
        raise ex


def create_image_path():
    def _random_str(randomlength=8):
        str = ''
        chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
        length = len(chars) - 1
        random = Random()
        for i in range(randomlength):
            str+=chars[random.randint(0, length)]
        return str
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    p = os.path.join(settings.MEDIA_ROOT, 'icon')
    if not os.path.exists(p):
        if not os.path.exists(settings.MEDIA_ROOT):
            os.mkdir(settings.MEDIA_ROOT)
        os.mkdir(p)
    return 'icon/%s%s.bmp' % (timestamp, _random_str())


def download_image(img_url):
    name = create_image_path()
    image_path = os.path.join(settings.MEDIA_ROOT, name)
    urllib.urlretrieve(img_url, os.path.join(settings.MEDIA_ROOT, name))
    io = Image.open(image_path)
    io.convert('RGB')
    io.save(image_path)
    return settings.MEDIA_URL + name


##################  Settlement ####################
def check_order_validation(settlement):
    """
    检查数据有效性:
    """
    # 检查每个商品库存与订单数是否匹配


class ValidationChecker(object):

    def __init__(self, settlement):
        self.settlement = settlement
        self.invalid_products = []

    def check(self):
        for p in Product.objects.all():
            self.check_product(p)
        return self.invalid_products

    def check_product(self, product):
        try:
            product_settlement = ProductSettlement.objects.get(product=product, settlement=self.settlement)
        except ProductSettlement.DoesNotExist, ex:
            return True
        quantity = 0
        quantity += sum_queryset(SettleOrderItem.objects.filter(settlement=self.settlement, product=product), 'Quantity')
        quantity -= sum_queryset(RefundItem.objects.filter(settlement=self.settlement, product=product), 'Quantity')
        quantity += sum_queryset(OtherTransactionItem.objects.filter(settlement=self.settlement, product=product), 'Quantity')
        quantity += sum_queryset(ProductRemovalItem.objects.filter(settlement=self.settlement, product=product), 'Quantity')
        # 如果售出数量 大于 库存加上计算时扣除的数量，说明非法
        if int(quantity) > int(product.amazon_inventory + get_float_from_model(product_settlement, 'Quantity')):
            self.invalid_products.append(product)
            return False
        return True


class SettlementDbHandler(object):

    def __init__(self, market):
        self.market = market
        self.MarketplaceId = market.MarketplaceId

    def update_settlement_to_db(self, data):
        if not data:
            return None
        settlement = self._update_settlement_to_db(data['SettlementData'])
        if not settlement:
            logger.error('create settlement failed: %s', json.dumps(data['SettlementData']))
            return None
        # 更新详细内容
        if 'Order' in data:
            # 删除已有的
            settlement.orders.all().delete()
            for item in data['Order']:
                self._update_order_to_db(settlement, item)
        if 'Refund' in data:
            # 删除已有的
            settlement.refunds.all().delete()
            for item in data['Refund']:
                self._update_refund_to_db(settlement, item)
        if 'OtherTransactions' in data:
            # 删除已有的
            settlement.other_transactions.all().delete()
            for item in data['OtherTransactions']:
                self._update_transaction_to_db(settlement, item)
            # todo
            self._update_custom_return_fee(settlement)      # 将FBACustomReturn的退货费用更新到退款表中
        if 'SellerDealPayment' in data:
            settlement.seller_deal_payments.all().delete()
            for item in data['SellerDealPayment']:
                self._update_deal_payment_to_db(settlement, item)
        if 'AdvertisingTransactionDetails' in data:
            settlement.advertising_transactions.all().delete()
            for item in data['AdvertisingTransactionDetails']:
                self._update_advertising_transaction_to_db(settlement, item)
        if 'SellerCouponPayment' in data:
            # 删除已有的
            settlement.coupons.all().delete()
            for item in data['SellerCouponPayment']:
                self._update_coupon_payment_to_db(settlement, item)
        # self._init_settlement_products(settlement)
        return settlement

    def _init_settlement_products(self, settlement):
        """
        默认创建settlement与product的关系
        :return:
        """
        records = list()
        for product in Product.objects.all():
            item = ProductSettlement(MarketplaceId=settlement.MarketplaceId, settlement=settlement, product=product)
            records.append(item)
        try:
            ProductSettlement.objects.bulk_create(records)
        except BaseException, ex:
            logger.warning('create ProductSettlement failed, settlemen id:%d', settlement.pk)

    def _update_settlement_to_db(self, data):
        if not data:
            return None
        settlement, created = Settlement.objects.get_or_create(MarketplaceId=self.MarketplaceId, AmazonSettlementID=data['AmazonSettlementID'])
        if created:
            for key, value in data.items():
                setattr(settlement, key, value)
            settlement.save()
        return settlement

    def calc_and_update_amount(self, settlement):
        """
        计算订单或退款信息中的总收入amount，并更新到数据库中
        """

    def _update_order_to_db(self, settlement, data):
        """
        更新结算订单信息至数据库
        """
        if not data:
            return None
        items = data['items']
        del data['items']
        order = SettleOrder.objects.create(MarketplaceId=self.MarketplaceId, settlement=settlement, **data)
        # 保存订单Item至数据库
        for item in items:
            self._update_order_item_to_db(order, item)
        return order

    def _update_order_item_to_db(self, order, data):
        if not data:
            return None
        data['order'] = order
        data['MarketplaceId'] = self.MarketplaceId
        data['settlement'] = order.settlement
        data['AmazonOrderId'] = order.AmazonOrderId
        data['PostedDate'] = order.PostedDate
        product = get_or_create_product(SellerSKU=data['SellerSKU'], MarketplaceId=self.MarketplaceId)
        data['product'] = product
        # data['SellerSKU'] = product.SellerSKU
        # 单价
        if data['Quantity'] and int(data['Quantity']) > 0:
            data['UnitPrice'] = float(data['Principal']) / int(data['Quantity'])
        #汇总
        data['income'] = to_float(data.get('Principal', 0)) + to_float(data.get('Promotion', 0)) + \
                         to_float(data.get('OtherPrice', 0)) + to_float(data.get('Fee', 0))
        return SettleOrderItem.objects.create(**data)

    def _update_refund_to_db(self, settlement, data):
        if not data:
            return None
        data['MarketplaceId'] = self.MarketplaceId
        data['settlement'] = settlement
        items = data['items']
        del data['items']
        refund = Refund.objects.create(**data)
        for item in items:
            self._update_refund_item_to_db(refund, item)
        return refund

    def _update_refund_item_to_db(self, refund, data):
        if not data:
            return None
        data['PostedDate'] = refund.PostedDate
        data['MarketplaceId'] = refund.MarketplaceId
        data['settlement'] = refund.settlement
        data['refund'] = refund
        data['AmazonOrderId'] = refund.AmazonOrderId
        product = get_or_create_product(SellerSKU=data['SellerSKU'], MarketplaceId=self.MarketplaceId)
        data['product'] = product
        data['SellerSKU'] = product.SellerSKU

        # 获取该订单的商品数量、以及退款的总额
        order_list = SettleOrderItem.objects.filter(OrderItemId=data['OrderItemId'])
        exist = False
        order = None
        count = order_list.count()
        # if not count:
        #     logger.error('SettleOrderItem not exist:%s', data['OrderItemId'])
        #     data['UnitPrice'], data['quantity'] = self._get_order_item_quantity_from_amazon(data['OrderItemId'], data['AmazonOrderId'])
        # else:
        # 找到关联的订货单
        if count:
            if count > 1:
                logger.info('SettleOrderItem return more than one: %s', data['OrderItemId'])
                for o in order_list:
                    if (-o.Principal) == to_float(data.get('Principal', 0)):
                        exist = True
                        order = o
                        break
                if not exist:
                    logger.error('return more than one but cannot found OrderItem for RefundItem: %s', data['OrderItemId'])
            if not order:
                order = order_list.first()
            data['order_item'] = order
            data['Quantity'] = -order.Quantity
            data['UnitPrice'] = order.UnitPrice
        else:
            data['Quantity'] = -1

        # 找到对应的订单信息
        data['income'] = to_float(data.get('Principal', 0)) + to_float(data.get('Promotion')) + to_float(data.get('OtherPrice')) + to_float(data.get('Fee'))
        refund = RefundItem.objects.create(**data)
        if order:
            order.refund_order = refund
            order.save()
        return refund

    def _get_order_item_quantity_from_amazon(self, order_item_id, amazon_order_id):
        # 从亚马逊请求订单数量
        from amazon_services.models import MarketAccount
        market = MarketAccount.objects.get(MarketplaceId=self.MarketplaceId)
        orders = OrderItemService(market).list_items(amazon_order_id)
        for order in orders:
            if order['OrderItemId'] == order_item_id:
                price = get_float(order, 'ItemPrice')
                quantity = int(order.get('QuantityShipped', 0))
                unit_price = price/quantity if quantity else 0
                return unit_price, -quantity
        logger.error('cannot get order item from amazon: %s', amazon_order_id)
        return None

    def _update_transaction_to_db(self, settlement, data):
        if not data:
            return None
        data['MarketplaceId'] = self.MarketplaceId
        data['settlement'] = settlement
        fees = data.get('fees', None)
        items = data.get('items', None)
        if 'fees' in data:
            del data['fees']
        if 'items' in data:
            del data['items']
        obj = OtherTransaction.objects.create(**data)
        self._update_transaction_fees_to_db(obj, fees)
        self._update_transaction_items_to_db(obj, items)
        return obj

    def _update_transaction_fees_to_db(self, transaction, data):
        if not data:
            return
        fields = ['MarketplaceId', 'TransactionID', 'AmazonOrderId', 'TransactionType', 'PostedDate']
        for item in data:
            for field in fields:
                item[field] = getattr(transaction, field)
            OtherTransactionFee.objects.create(transaction=transaction, settlement=transaction.settlement, **item)

    def _update_transaction_items_to_db(self, transaction, data):
        if not data:
            return
        fields = ['MarketplaceId', 'TransactionID', 'AmazonOrderId', 'TransactionType', 'PostedDate']
        for item in data:
            for field in fields:
                item[field] = getattr(transaction, field)
            product = get_or_create_product(MarketplaceId=transaction.MarketplaceId, SellerSKU=item['SellerSKU'])
            quantity = int(item.get('Quantity', 0))
            item['UnitPrice'] = get_float(item, 'Amount') / quantity if quantity else 0
            OtherTransactionItem.objects.create(transaction=transaction, settlement=transaction.settlement, product=product, **item)

    def _update_deal_payment_to_db(self, settlement, data):
        if not data:
            return None
        try:
            obj = SellerDealPayment.objects.get(settlement=settlement, DealID=data['DealID'])
            print 'SellerDealPayment exist:　%s' % json.dumps(data)
            return obj
        except SellerDealPayment.DoesNotExist, ex:
            pass
        data['MarketplaceId'] = self.MarketplaceId
        data['settlement'] = settlement
        return SellerDealPayment.objects.create(**data)

    def _update_coupon_payment_to_db(self, settlement, data):
        if not data:
            return None
        data['settlement'] = settlement
        data['cost'] = data['Amount']
        return SellerCouponPayment.objects.create(**data)

    def _update_advertising_transaction_to_db(self, settlement, data):
        if not data:
            return None
        # try:
        #     obj = AdvertisingTransactionDetails.objects.get(settlement=settlement, InvoiceId=data['InvoiceId'])
        #     print 'Advertising exist:　%s' % json.dumps(data)
        #     return obj
        # except AdvertisingTransactionDetails.DoesNotExist, ex:
        #     pass
        data['settlement'] = settlement
        data['MarketplaceId'] = self.MarketplaceId
        data['settlement'] = settlement
        return AdvertisingTransactionDetails.objects.create(**data)

    @staticmethod
    def _get_product_info_of_traction_fee(market, fee):
        # 根据赔偿记录的订单id，找到对应的商品信息
        logger.warning('FBACustomReturn: cannot find refund item:%s', fee.AmazonOrderId)
        items = OrderItemService(market).list_items(fee.AmazonOrderId)
        if not items:
            logger.error('exception occurred when get OrderItem related to FBACustomerReturn: %s', fee.AmazonOrderId)
            return
        fee.SellerSKU = items[0]['SellerSKU']
        fee.save()

    def _update_custom_return_fee(self, settlement):
        """
        退货费
        """
        return_fees = OtherTransaction.objects.filter(settlement=settlement, TransactionType='FBACustomerReturn')
        for fee in return_fees:
            try:
                refund = RefundItem.objects.get(AmazonOrderId=fee.AmazonOrderId, FBAReturnFee__isnull=True)
            except RefundItem.MultipleObjectsReturned, ex:
                logger.warning('FBACustomReturn: multi object return when find AmazonOrderId in RefundItem:%s', fee.AmazonOrderId)
                refund = RefundItem.objects.filter(AmazonOrderId=fee.AmazonOrderId, FBAReturnFee__isnull=True).first()
            except RefundItem.DoesNotExist, ex:
                # 找不到的话，查找订单信息，找到对应的商品SellerSKU
                # 单独起一个线程进行查询
                #
                # threading.Thread(target=SettlementDbHandler._get_product_info_of_traction_fee, args=(self.market, fee,), ).start()
                logger.warning('FBACustomReturn: no RefundItem found for AmazonOrderId:%s', fee.AmazonOrderId)
                continue
            fee.refund_item = refund
            fee.SellerSKU = refund.SellerSKU
            fee.save()
            refund.FBAReturnFee = fee.Amount     # 将退货费加到refund里
            refund.income = refund.income + refund.FBAReturnFee
            refund.save()


class RemovalDbHandler(object):

    def update_to_db(self, settlement, data):
        results = list()
        start_date = settlement.StartDate.strftime(DT_FORMAT)
        end_date = settlement.EndDate.strftime(DT_FORMAT)
        if data:
            # 先清除原有的记录
            ProductRemovalItem.objects.filter(settlement=settlement).delete()
        for item in data:
            update_data = dateutil.parser.parse(item['UpdateDate']).replace(tzinfo=None).strftime(DT_FORMAT)
            if update_data > end_date \
                or update_data < start_date:   # 如果报告日期超出结算日期，则不处理
                continue
            item['settlement'] = settlement
            item['MarketplaceId'] = settlement.MarketplaceId
            product = get_or_create_product(SellerSKU=item['SellerSKU'], MarketplaceId=settlement.MarketplaceId)
            item['product'] = product
            item['Fee'] = -float(item['Fee'])
            results.append(ProductRemovalItem.objects.create(**item))
        return results


class StorageDbHandler(object):
    """
    月度仓促费数据库更新
    """

    def update_to_db(self, settlement, data):
        # 仓储费无需判断日期
        results = list()
        # 先将仓储费按ASIN进行汇总
        data_by_asin = dict()
        for item in data:
            asin = item['ASIN']
            if asin in data_by_asin:
                data_by_asin[asin] += to_float(item['Fee'])
            else:
                data_by_asin[asin] = to_float(item['Fee'])
        total_fee = 0   #
        for asin, fee in data_by_asin.items():
            fee = -fee
            try:
                p = Product.objects.get(ASIN=asin)
                total_fee += fee
                obj, created = ProductSettlement.objects.get_or_create(product=p, settlement=settlement)
                obj.storage_fee = fee
                obj.save()
                # 平均到每个订单上
                orders = SettleOrderItem.objects.filter(settlement=settlement, product=p, is_total=False)
                if orders.exists():
                    orders.update(storage_fee=fee/float(orders.count()))
                    t = SettleOrderItem.objects.get(settlement=settlement, product=p, is_total=True)
                    t.storage_fee = fee
                    t.save()
                results.append(obj)
            except Product.DoesNotExist, ex:
                logger.error('cannot find product with ASIN:' + asin)
                total_fee += fee
        # 更新settlement的仓储费
        settlement.storage_fee = total_fee
        settlement.save()
        return results


class AdvertisingDbHandler(object):
    """
    广告处理对象
    """

    def update_to_db(self, settlement, data):
        # 将广告报告数据导入到数据库
        # 先清除原有的记录

        self._clear_product_advertising(settlement)
        # 先按SellerSKU将广告费进行统计
        data_by_sku = dict()
        total_fee = 0
        for item in data:
            sku = item['SellerSKU']
            if sku in data_by_sku:
                data_by_sku[sku] += to_float(item['Fee'])
            else:
                data_by_sku[sku] = to_float(item['Fee'])
            total_fee += to_float(item['Fee'])
        # 将报告中的total_fee与结算报告中实际支持的广告费进行对比，将差额部分按照每个商品的广告费比例进行平均
        tmp = total_fee + settlement.advertising_fee
        tmp_total = 0
        for sku, fee in data_by_sku.items():
            p = get_or_create_product(SellerSKU=sku, MarketplaceId=settlement.MarketplaceId)
            obj, created = ProductSettlement.objects.get_or_create(product=p, settlement=settlement)
            obj.advertising_fee = -fee + fee/total_fee*tmp
            tmp_total += obj.advertising_fee
            obj.save()
        print tmp_total

    def _clear_product_advertising(self, settlement):
        # 先清除商品原有的广告费
        ProductSettlement.objects.filter(settlement=settlement).update(advertising_fee=0)


# 将广告数据在settlement时间范围内的数据，平均成天保存到数据库里，不在settlement时间范围内的不保存
def update_product_advertising_to_db(settlement, data):
    """
    同步广告业绩报告数据到数据库
    :param settlement:
    :param data:
    """
    def _format_datetime(d):
        if d.endswith('PDT'):
            return d[0: len(d)-4]
        return d
    items = list()
    settlement_start = settlement.StartDate.date()
    settlement_end = settlement.EndDate.date()
    for item in data:
        item['MarketplaceId'] = settlement.MarketplaceId
        item['settlement'] = settlement
        item['StartDate'] = _format_datetime(item['StartDate'])
        item['EndDate'] = _format_datetime(item['EndDate'])
        product = get_or_create_product(MarketplaceId=settlement.MarketplaceId, SellerSKU=item['SellerSKU'])
        item['product'] = product

        start = datetime.datetime.strptime(item['StartDate'], DB_DT_FORMAT).date()
        end = datetime.datetime.strptime(item['EndDate'], DB_DT_FORMAT).date()
        day_len = (end-start).days
        item['TotalSpend'] = to_float(item.get('TotalSpend', 0)) / float(day_len)
        item['cost'] = -item['TotalSpend']
        # 广告以周报告形式返回，按天保存到数据库中
        for i in range(0, day_len):
            d = start + datetime.timedelta(days=i)
            if d < settlement_start or d >= settlement_end:
                continue
            item['StartDate'] = d.strftime(DB_DT_FORMAT)
            item['EndDate'] = d.strftime(DB_DT_FORMAT)
            try:
                AdvertisingProductItems.objects.get(settlement=settlement, product=product, StartDate=d).delete()
            except AdvertisingProductItems.DoesNotExist, ex:
                pass
            AdvertisingProductItems.objects.create(**item)
    return True


#################  成本计算 ####################
class CostCalculate(object):

    def __init__(self):
        pass

    @classmethod
    def calc_current_cost(cls, product):
        """
        计算商品的当前成本
        """
        cost1 = cls._calc_supply_cost(product)
        cost2 = cls._calc_shipment_cost(product)
        product.supply_cost = cost1
        product.shipment_cost = cost2
        product.cost = cost1 + cost2
        product.save()
        return product.cost

    @classmethod
    def _calc_supply_cost(cls, product):
        """
        计算国内运费单价成本
        """
        supplies = InboundShipment.objects.filter(product=product, inventory__gt=0)
        quantity = 0    # 总数量
        amount = 0      # 总成本
        for supply in supplies:
            quantity += supply.inventory
            amount += supply.inventory * supply.unit_cost
        return amount/quantity if quantity else 0

    @classmethod
    def _calc_shipment_cost(self, product):
        """
        计算当前移库单位成本
        """
        shipments = OutboundShipmentItem.objects.filter(product=product, inventory__gt=0)
        quantity = 0
        amount = 0
        for s in shipments:
            quantity += s.inventory
            amount += s.inventory * s.unit_cost
        return amount/quantity if quantity else 0


#################  Settlement ####################
class ProductIncomeCalc(object):
    # 计算商品的销售部分数据

    def __init__(self, product):
        self.product = product

    def calc_income(self, settlement):
        self.quantity = 0
        self.sales = 0
        self.refund = 0
        self.other_fee = 0
        self.other_trade = 0
        self.subscription_fee = 0
        self._calc_order(settlement)
        self._calc_removals(settlement)
        self._calc_with_refunds(settlement)
        self._calc_lost(settlement)
        total, created = ProductSettlement.objects.get_or_create(settlement=settlement, product=self.product)
        total.Quantity = self.quantity
        total.sales = self.sales
        total.refund = self.refund
        total.other_fee = self.other_fee
        total.other_trade = self.other_trade
        total.income = self.sales + self.refund + self.other_trade + self.other_fee
        total.subscription_fee = self.subscription_fee
        total.save()

    def _calc_order(self, settlement):
        """
        计算每个订单的成本
        :return:
        """
        orders = SettleOrderItem.objects.filter(settlement=settlement, product=self.product, is_total=False)
        if not orders.exists():
            return
        total, created = SettleOrderItem.objects.get_or_create(settlement=settlement, product=self.product, is_total=True)
        fields = ['Quantity', 'Principal', 'Promotion', 'Fee', 'OtherPrice', 'income', 'subscription_fee']
        sum_fields(orders, fields, total)
        self.quantity += total.Quantity
        self.sales = total.income
        self.subscription_fee = total.subscription_fee

    def _calc_with_refunds(self, settlement):
        """
        计算退货的收入支出
        :param product:
        """
        refunds = RefundItem.objects.filter(settlement=settlement, product=self.product, is_total=False)
        if not refunds.exists():
            return
        total, created = RefundItem.objects.get_or_create(settlement=settlement, product=self.product, is_total=True)
        fields = ['Quantity', 'Principal', 'Promotion', 'Fee', 'OtherPrice', 'income']
        sum_fields(refunds, fields, total)
        self.refund = total.income
        self.quantity += total.Quantity

    def _calc_removals(self, settlement):
        """
        计算弃置/移除的商品，相当于销售出去
        """
        items = ProductRemovalItem.objects.filter(settlement=settlement, product=self.product, is_total=False)
        if not items.exists():
            return
        total, created = ProductRemovalItem.objects.get_or_create(settlement=settlement, product=self.product, is_total=True)
        fields = ['Fee', 'Quantity']
        sum_fields(items, fields, total)
        self.other_fee = total.Fee
        self.quantity += total.Quantity

    def _calc_lost(self, settlement):
        """
        计算丢失赔偿的订单，相当于销售出去
        :param product:
        :return: 总成本
        """
        items = OtherTransactionItem.objects.filter(settlement=settlement, product=self.product, is_total=False)
        if not items.exists():
            return
        total, created = OtherTransactionItem.objects.get_or_create(settlement=settlement, product=self.product, is_total=True)
        fields = ['Amount', 'Quantity']
        sum_fields(items, fields, total)
        self.other_trade = total.Amount
        self.quantity += total.Quantity


class SettlementIncomeCalc(object):
    # 计算某个结算周期的亚马逊部分

    def __init__(self, settlement):
        self.settlement = settlement

    def calc(self):
        # 在计算前先将订阅费平均到每个订单上
        self._calc_subscription_fee()
        # 先计算所有产品的销售部分
        self.calc_all_products()
        # 在计算结算周期的销售收入
        products = ProductSettlement.objects.filter(settlement=self.settlement)
        self.settlement.sales = sum_queryset(products, 'sales')
        self.settlement.refund = sum_queryset(products, 'refund')
        self.settlement.other_fee = self._calc_other_fee()
        self.settlement.other_trade = sum_queryset(products, 'other_trade')
        self.settlement.income = self.settlement.sales + self.settlement.refund + self.settlement.other_fee + self.settlement.other_trade
        self.settlement.advertising_fee = self._calc_advertising_fee()
        self.settlement.storage_fee = self._calc_storage_fee()
        self.settlement.Quantity = sum_queryset(products, 'Quantity', is_integer=True)
        self.settlement.save()

    def calc_all_products(self):
        products = Product.objects.all()
        for p in products:
            calc_obj = ProductIncomeCalc(p)
            calc_obj.calc_income(self.settlement)

    def _calc_subscription_fee(self):
        # 计算订阅费
        subscription_fee = sum_queryset(OtherTransaction.objects.filter(settlement=self.settlement,
                                                                        TransactionType='Subscription Fee'), 'Amount')
        self.settlement.subscription_fee = subscription_fee
        # 平均到每个订单上
        orders = SettleOrderItem.objects.filter(settlement=self.settlement, is_total=False)
        orders_count = orders.count()
        avg_fee = (subscription_fee / float(orders_count)) if orders_count else 0
        orders.update(subscription_fee=avg_fee)

    def _calc_other_fee(self):
        deal_fee = sum_queryset(SellerDealPayment.objects.filter(settlement=self.settlement), 'DealFeeAmount')      # 促销费用
        # 移除、弃置或其他。除掉赔偿、仓储费的部分，赔偿的部分会在OtherTransactionItem中计算
        removal = sum_queryset(OtherTransaction.objects.filter(settlement=self.settlement)
                               .exclude(TransactionType__in=['REVERSAL_REIMBURSEMENT', 'WAREHOUSE_DAMAGE',
                                                             'Storage Fee', 'FBACustomerReturn', 'DisposalComplete']), 'Amount')
        coupon = sum_queryset(SellerCouponPayment.objects.filter(settlement=self.settlement), 'Amount')
        return deal_fee + removal + coupon

    def _calc_advertising_fee(self):
        # 计算广告费，如果广告报告未导入，那么直接读取AdvertisingTransactionDetails的广告费。
        # 如果广告报告已导入，那么从商品中的订单中求和
        return sum_queryset(AdvertisingTransactionDetails.objects.filter(settlement=self.settlement), 'TransactionAmount')   # 广告费

    def _calc_storage_fee(self):
        # 计算仓储费，如果月度仓储报告未导入，那么直接读取 OtherTransaction.TransactionType=Storage Fee部分
        # 如果月度仓储报告已导入，那么从商品中的订单中求和
        # 仓储费平均到每个订单上
        return sum_queryset(OtherTransaction.objects.filter(settlement=self.settlement, TransactionType = 'Storage Fee'), 'Amount')

    def calc_removals(self, by_product=True):
        # 计算所有产品的移除费用
        # by_product： True： 从ProductRemovalItem读取。 False：从OtherTransaction.TransactionType=['DisposalComplete', 'RemovalComplete']读取
        if by_product:
            return sum_queryset(ProductRemovalItem.objects.filter(settlement=self.settlement, is_total=False), 'Fee')
        else:
            queryset = OtherTransaction.objects.filter(settlement=self.settlement, TransactionType__in=['DisposalComplete', 'RemovalComplete'])
            return sum_queryset(queryset, 'Amount')


class ProductProfitCalc(object):

    def __init__(self, settlement):
        self.settlement = settlement
        self.sale_quantity = 0
        self.unfound_refund_quantity = 0

    def _clear(self, product):
        """
        清除，主要是恢复库存，不影响时间成本的计算
        :param product:
        :return:
        """
        """
        清除计算的结果
        :return:
        """
        try:
            ps = ProductSettlement.objects.get(settlement=self.settlement, product=product)
            if ps.Quantity:
                # 先将自动生成的去掉
                quantity = ps.Quantity
                quantity -= self._remove_inventory_auto_created(product)
                self._update_inventory(product, -quantity)        # 先将库存补充上
        except ProductSettlement.DoesNotExist, ex:
            return

    def _remove_inventory_auto_created(self, product):
        settlement = self.settlement
        try:
            supply = InboundShipment.objects.get(product=product, MarketplaceId=settlement.MarketplaceId, settlement_id=self.settlement.pk)
        except InboundShipment.DoesNotExist, ex:
            return 0
        try:
            shipment = OutboundShipment.objects.get(MarketplaceId=settlement.MarketplaceId, settlement_id=self.settlement.pk)
            shipment_item = OutboundShipmentItem.objects.get(shipment=shipment, product=product,
                                                                       MarketplaceId=settlement.MarketplaceId)
        except BaseException, ex:
            return 0
        quantity = shipment_item.QuantityShipped
        shipment_item.delete()
        supply.delete()
        product.amazon_inventory -= quantity
        product.domestic_inventory -= quantity
        product.save()
        return quantity

    def _create_refund_inventory(self, product):
        """
        如果退货记录找不到相应的订单，则需要在国内、国际库存中增加这部分库存
        :param product:
        """
        items = RefundItem.objects.filter(product=product, order_item__isnull=True, is_total=False, settlement=self.settlement)
        quantity = items.aggregate(total=Sum('Quantity')).get('total')
        if not quantity:
            return
        logger.info('there has %d refunds cannot find order, product: %s', quantity, product.SellerSKU)
        settlement = self.settlement
        name = '%s ~ %s' % (self.settlement.StartDate.strftime('%Y-%m-%d'), self.settlement.EndDate.strftime('%Y-%m-%d'))
        # 添加到国内库存
        supply, created = InboundShipment.objects.get_or_create(product=product, ShipmentName=name,
                                                                MarketplaceId=settlement.MarketplaceId, settlement_id=self.settlement.pk)
        if created:
            supply.ship_date = self.settlement.StartDate.date()
        tmp = quantity - (supply.count if supply.count else 0)
        product.domestic_inventory += tmp
        supply.ship_date = settlement.StartDate.date()
        supply.count = quantity
        supply.insert_time = datetime.datetime.now()
        supply.unit_cost = product.supply_cost
        supply.inventory = tmp + (supply.inventory if supply.inventory else 0)
        supply.real_inventory = tmp + (supply.real_inventory if supply.real_inventory else 0)
        supply.save()

        # 添加到国际物流
        shipment, created = OutboundShipment.objects.get_or_create(ShipmentId=name, MarketplaceId=settlement.MarketplaceId, settlement_id=self.settlement.pk)
        if created:
            shipment.ship_date = self.settlement.StartDate.date()
            shipment.ShipmentName = 'auto created'
            shipment.save()
        # 添加国际物流的子项
        item, created = OutboundShipmentItem.objects.get_or_create(shipment=shipment, product=product,
                                                                   MarketplaceId=settlement.MarketplaceId)
        tmp = quantity - (item.QuantityShipped if item.QuantityShipped else 0)
        product.amazon_inventory += tmp
        item.SellerSKU = product.SellerSKU
        item.ShipmentId = shipment.ShipmentId
        item.ship_date = shipment.ship_date
        item.QuantityShipped = tmp + (item.QuantityShipped if item.QuantityShipped else 0)
        item.inventory = tmp + (item.inventory if item.inventory else 0)
        item.unit_cost = product.shipment_cost
        item.save()
        product.save()

    def calc_product_cost(self, product):
        # 计算成本，计算完成后会自动计算利润
        # 首先更新商品当前单位成本
        try:
            self.sale_quantity = 0       # 每个商品计算时都先清零
            self.unfound_refund_quantity = 0
            self._clear(product)    # 先恢复库存
            CostCalculate.calc_current_cost(product)
            self._calc_order_profit(product)
            self._calc_with_refunds(product)
            self._calc_removals(product)
            self._calc_lost(product)
            # 更新库存
            self._update_inventory(product, self.sale_quantity)
            # 计算利润
            self.calc_product_profit(product)
            self._create_refund_inventory(product)
        except BaseException, ex:
            logger.error(traceback.format_exc())

    def calc_product_profit(self, product):
        # 首先更新商品当前单位成本
        try:
            # self._update_inventory(product, self.sale_quantity)
            ps, created = ProductSettlement.objects.get_or_create(settlement=self.settlement, product=product)

            # 退货服务费
            ps.custom_return_fee = sum_queryset(OtherTransaction.objects.filter(TransactionType='FBACustomerReturn',
                                                settlement=self.settlement, SellerSKU=product.SellerSKU,
                                                refund_item__isnull=True), 'Amount')
            # 统计
            total_cost = 0
            profit = 0
            # 统计订单的成本、利润
            try:
                order_total = SettleOrderItem.objects.get(settlement=self.settlement, product=product, is_total=True)
                ps.advertising_fee = order_total.advertising_fee        # 广告费、仓储费、订阅费只有订单里有
                ps.storage_fee = order_total.storage_fee
                ps.subscription_fee = order_total.subscription_fee
                total_cost += order_total.total_cost
                profit += order_total.profit
            except SettleOrderItem.DoesNotExist, ex:
                pass
            # 从退货里统计
            try:
                refund_total = RefundItem.objects.get(settlement=self.settlement, product=product, is_total=True)
                total_cost += refund_total.total_cost
                profit += refund_total.profit
            except RefundItem.DoesNotExist, ex:
                pass
            # 从移除、弃置里统计
            try:
                removal_total = ProductRemovalItem.objects.get(settlement=self.settlement, product=product, is_total=True)
                total_cost += removal_total.total_cost
                profit += removal_total.profit
            except ProductRemovalItem.DoesNotExist, ex:
                pass
            # 从赔偿里统计
            try:
                lost_total = OtherTransactionItem.objects.get(settlement=self.settlement, product=product, is_total=True)
                total_cost += lost_total.total_cost
                profit += lost_total.profit
            except OtherTransactionItem.DoesNotExist, ex:
                pass
            ps.total_cost = total_cost
            ps.profit = profit
            ps.profit_rate = ps.profit / ps.income if ps.income else 0
            ps.is_calculated = True
            ps.save()
            self._create_refund_inventory(product)
        except BaseException, ex:
            logger.error(traceback.format_exc())

    def _calc_order_profit(self, product):
        """
        计算订单的收入支出
        :param product:
        :return: 数量、实收、成本
        """
        orders = SettleOrderItem.objects.filter(product=product, settlement=self.settlement, is_total=False)
        if not orders.exists():
            return
        for order in orders:
            self._calc_order_cost(product, order)

        # 计算汇总信息并记录
        total_item, created = SettleOrderItem.objects.get_or_create(settlement=self.settlement, product=product,
                                                                    is_total=True)
        query_set = SettleOrderItem.objects.filter(settlement=self.settlement, product=product, is_total=False)
        # 求和
        total_item.AmazonOrderId = 'Total'
        total_item.total_cost = sum_queryset(query_set, 'total_cost')
        total_item.profit = sum_queryset(query_set, 'profit')
        # 计算利润
        total_item.profit_rate = total_item.profit/total_item.income if total_item.income else 0
        total_item.save()

    def _calc_order_cost(self, product, order):
        """
        计算每个订单的成本
        :return:
        """
        order.supply_cost = -product.supply_cost
        order.shipment_cost = -product.shipment_cost
        order.cost = -product.cost
        order.total_cost = (order.supply_cost + order.shipment_cost) * order.Quantity + to_float(order.subscription_fee) + \
                           to_float(order.advertising_fee) + to_float(order.storage_fee)
        order.profit = order.income + order.total_cost
        order.profit_rate = order.profit / order.income if order.income else 0
        order.save()
        self.sale_quantity += order.Quantity
        return order.cost

    def _calc_with_refunds(self, product):
        """
        计算退货的收入支出
        :param product:
        """
        refunds = RefundItem.objects.filter(product=product, settlement=self.settlement, is_total=False)
        if not refunds.exists():
            return
        for refund in refunds:
            if refund.order_item:
                refund.cost = -refund.order_item.cost
                self.sale_quantity += refund.Quantity
            else:
                refund.cost = product.cost
            refund.total_cost = -refund.cost * refund.Quantity
            refund.profit = refund.total_cost + refund.income
            refund.profit_rate = refund.profit / refund.income if refund.income else 0
            refund.save()

        # 计算汇总信息并记录
        total_item, created = RefundItem.objects.get_or_create(settlement=self.settlement, product=product,
                                                               is_total=True)
        query_set = RefundItem.objects.filter(settlement=self.settlement, product=product, is_total=False)
        total_item.AmazonOrderId = 'Total'
        total_item.total_cost = sum_queryset(query_set, 'total_cost')
        total_item.profit = sum_queryset(query_set, 'profit')
        total_item.profit_rate = total_item.profit/total_item.income if total_item.income else 0
        total_item.save()

    def _calc_removals(self, product):
        """
        计算弃置/移除的商品，相当于销售出去
        """
        items = ProductRemovalItem.objects.select_related('product').filter(settlement=self.settlement, product=product,
                                                                            is_total=False)
        if not items.exists():
            return
        for item in items:
            item.cost = -product.cost
            item.total_cost = item.cost * item.Quantity
            item.profit = item.total_cost + item.Fee
            item.save()
            self.sale_quantity += item.Quantity

        # 计算汇总信息并记录
        total_item, created = ProductRemovalItem.objects.get_or_create(settlement=self.settlement, product=product,
                                                                       is_total=True)
        query_set = ProductRemovalItem.objects.filter(settlement=self.settlement, product=product, is_total=False)
        fields = ['Quantity', 'Fee', 'total_cost', 'profit']
        total_item.OrderId = 'Total'
        sum_fields(query_set, fields, total_item)

    def _calc_lost(self, product):
        """
        计算丢失赔偿的订单，相当于销售出去
        :param product:
        :return: 总成本
        """
        items = OtherTransactionItem.objects.filter(settlement=self.settlement, product=product, is_total=False)
        if not items.exists():
            return
        for item in items:
            if item.TransactionType == 'INCORRECT_FEES_ITEMS':  # 费用更正无需处理商品成本
                item.cost = 0
            else:
                item.cost = -product.cost
                self.sale_quantity += item.Quantity
            item.total_cost = item.Quantity * item.cost
            item.profit = item.total_cost + item.Amount
            item.profit_rate = item.profit/item.Amount if item.Amount else 0
            item.save()

        # 计算汇总信息并记录
        total_item, created = OtherTransactionItem.objects.get_or_create(settlement=self.settlement, product=product,
                                                                         is_total=True)
        query_set = OtherTransactionItem.objects.filter(settlement=self.settlement, product=product, is_total=False)
        fields = ['Quantity', 'Amount', 'profit', 'total_cost']
        sum_fields(query_set, fields, total_item)
        total_item.AmazonOrderId = 'Total'
        total_item.profit_rate = total_item.profit/total_item.Amount if total_item.Amount else 0
        total_item.save()

    def _update_inventory(self, product, count):
        """
        更新国内、亚马逊库存
        :param product:
        :param count: 如果为正数，表示销售的商品数，如果为负数，表示退货的数量
        """
        class_list = [InboundShipment, OutboundShipmentItem]
        order_list = ['ship_date', 'shipment__ship_date']
        quantity_key = ['count', 'QuantityShipped']
        if count == 0:
            return
        if count > 0:
            for i in [0, 1]:
                items = class_list[i].objects.filter(product=product, inventory__gt=0).order_by(order_list[i])
                tmp_count = count
                for supply in items:
                    if supply.inventory > tmp_count:
                        supply.inventory -= tmp_count
                        supply.save()
                        break
                    tmp_count -= supply.inventory
                    supply.inventory = 0
                    supply.save()
            product.amazon_inventory -= count
            product.save()
        else:
            count = -count
            for i in [0, 1]:
                items = class_list[i].objects.filter(product=product, inventory__lte=F(quantity_key[i])).order_by('-'+order_list[i])
                tmp = count
                for item in items:
                    if tmp <= getattr(item, quantity_key[i]) - item.inventory:
                        item.inventory += tmp
                        item.save()
                        break
                    tmp -= getattr(item, quantity_key[i]) - item.inventory
                    item.inventory = getattr(item, quantity_key[i])
                    item.save()
            product.amazon_inventory += count
            product.save()


class SettlementCalc(object):
    """
    结算利润计算
    """

    def __init__(self, settlement):
        self.settlement = settlement
        self.product_calc = ProductProfitCalc(settlement)

    def _aggregate_orders(self):
        total_item, created = SettleOrderItem.objects.get_or_create(settlement=self.settlement, product=None, is_total=True)
        query_set = SettleOrderItem.objects.filter(settlement=self.settlement, product__isnull=False, is_total=True)
        fields = ['Quantity', 'Principal', 'Promotion', 'Fee', 'OtherPrice', 'income',
                  'advertising', 'storage_fee', 'subscription_fee', 'total_cost', 'profit']
        sum_fields(query_set, fields, total_item)

    def _aggregate_refunds(self):
        total_item, created = RefundItem.objects.get_or_create(settlement=self.settlement, product=None,
                                                               is_total=True)
        total_item.AmazonOrderId = 'Total'
        query_set = RefundItem.objects.filter(settlement=self.settlement, product__isnull=False, is_total=True)
        fields = ['Quantity', 'Principal', 'Promotion', 'Fee', 'OtherPrice', 'income', 'total_cost', 'profit']
        sum_fields(query_set, fields, total_item)

    def _aggregate_removals(self):
        total_item, created = ProductRemovalItem.objects.get_or_create(settlement=self.settlement, product=None,
                                                                       is_total=True)
        total_item.OrderId = 'Total'
        query_set = ProductRemovalItem.objects.filter(settlement=self.settlement, product__isnull=False, is_total=True)
        fields = ['Quantity', 'Fee', 'total_cost', 'profit']
        sum_fields(query_set, fields, total_item)

    def _aggregate_losts(self):
        total_item, created = OtherTransactionItem.objects.get_or_create(settlement=self.settlement, product=None,
                                                                         is_total=True)
        total_item.AmazonOrderId = 'Total'
        query_set = OtherTransactionItem.objects.filter(settlement=self.settlement, product__isnull=False, is_total=True)
        fields = ['Quantity', 'Amount', 'total_cost', 'profit']
        sum_fields(query_set, fields, total_item)

    def _aggregate_product(self):
        query_set = ProductSettlement.objects.filter(settlement=self.settlement, product__isnull=False)
        settlement = self.settlement
        fields = ['subscription_fee', 'advertising_fee', 'storage_fee', 'total_cost', 'profit']
        sum_fields(query_set, settlement, fields)
        settlement.profit_rate = settlement.profit / settlement.income if settlement.income else 0
        settlement.save()

    def _aggregate(self):
        self._aggregate_orders()
        self._aggregate_refunds()
        self._aggregate_removals()
        self._aggregate_losts()
        self._aggregate_product()

    def calc_settlement(self, recalc_product=True):
        """
        计算结算周期内所有商品的总收入、总成本、总利润
        :param recalc_product: 是否重新计算商品利润
        :return:
        """
        settlement = self.settlement
        logger.info('settlement(%s ~ %s) start calculating', settlement.StartDate, settlement.EndDate)
        if settlement.calc_status == Error.RUNNING:
            logger.info('settlement(%s ~ %s) is calculating, cannot calculate again', settlement.StartDate, settlement.EndDate)
            return Error.RUNNING
        settlement.calc_status = Error.RUNNING
        settlement.save()
        try:
            self._calculate(recalc_product=recalc_product)
            # time.sleep(15)
        except BaseException, ex:
            logger.error(traceback)
            settlement.calc_status = Error.FAIL
            settlement.save()
            return Error.FAIL
        settlement.calc_status = Error.SUCCESS
        settlement.save()
        logger.info('settlement(%s ~ %s) end calculating', settlement.StartDate, settlement.EndDate)
        return Error.SUCCESS

    def _calculate(self, recalc_product=True):
        settlement = self.settlement
        # 先计算所有商品的利润
        if recalc_product:
            product_calc = ProductProfitCalc(settlement)
            for product in Product.objects.all():
                product_calc.calc_product_profit(product)
        self._aggregate()
        # end calc products
        settlement.subscription_fee_adjust = sum_queryset(OtherTransaction.objects.filter(settlement=settlement,
                                                                                          TransactionType='NonSubscriptionFeeAdj'), 'Amount')
        settlement.balanced_adjust = sum_queryset(OtherTransaction.objects.filter(settlement=settlement,
                                                                                  TransactionType='BalanceAdjustment'), 'Amount')

        settlement.profit_rate = settlement.profit / settlement.income if settlement.income else 0
        settlement.save()

    def _handle_returns(self, product):
        """
        处理退货
        :param product:
        """
        # 计算顾客退货且可销售的商品数量
        values = ProductReturn.objects.filter(product=product, settlement=self.settlement, type='CustomerReturns',
                                              disposition='SELLABLE').values_list('quantity', flat=True)
        total = sum(list(values))
        product.custom_return_quantity = total
        # 计算顾客退货且损坏的商品数量
        values = ProductReturn.objects.filter(product=product, settlement=self.settlement, type='CustomerReturns',
                                              disposition='CUSTOMER_DAMAGED').values_list('quantity', flat=True)
        total = sum(list(values))
        product.custom_damage_quantity = total
        # 计算顾客退货且可销售的商品数量
        values = ProductReturn.objects.filter(product=product, settlement=self.settlement, type='Adjustments')\
            .values_list('quantity', flat=True)
        total = sum(list(values))
        product.return_quantity = total
        # # 将退货数量补充到国内库存、国外库存
        # self._update_inventory(product, total)


##################  退货 ####################
def update_returns_to_db(settlement, item):
    product = get_or_create_product(MarketplaceId=settlement.MarketplaceId, SellerSKU=item['SellerSKU'])
    ProductReturn.objects.create(settlement=settlement, product=product, **item)


##################  文件导入 ####################
class FileImporter(object):

    @classmethod
    def import_removals(cls, text, settlement=None):
        """
        导入移除报告并保存到数据库
        :param text:
        """
        from amazon_services.text_parser import ProductRemovalParser
        from amazon_services.exception import TextParseException
        parser = ProductRemovalParser(text)
        items = parser.get_items()
        removals = RemovalDbHandler().update_to_db(settlement=settlement, data=items)
        # removals = RemovalDbHandler().upload_by_day(market_id=settlement.MarketplaceId, data=items)
        return removals

    @classmethod
    def import_storage(cls, text, settlement):
        """
        导入月度仓储费
        :param text:
        :param settlement:
        """
        from amazon_services.text_parser import MonthlyStorageFeeParser
        parser = MonthlyStorageFeeParser(text)
        items = parser.get_items()
        removals = StorageDbHandler().update_to_db(settlement=settlement, data=items)
        return removals

    @classmethod
    def import_advertising(cls, text, settlement):
        from amazon_services.text_parser import AdvertisingReportParser
        parser = AdvertisingReportParser(text)
        items = parser.get_items()
        AdvertisingDbHandler().update_to_db(settlement=settlement, data=items)