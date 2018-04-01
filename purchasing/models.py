#-*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from products.models import Product
# Create your models here.


class OrderStatus(models.Model):
    WaitForDepositPayed = 1     # 等待预付款付清
    WaitForProducing = 2        # 等待采购员填写生产完成信息
    WaitForPaying = 3           # 等待财务尾款打款
    WaitForTraffic = 4          # 等待采购员补充物流信息
    TrafficConfirm = 5          # 等待到货
    WaitForInbound = 6          # 等待仓库入库
    TrafficReceived = 7         # 入库
    WaitForCheck = 8            # 等待采购确认
    WaitForPayment = 9  # 等待物流费打款
    FINISH = 10                # 完成
    WaitForPack = 100           # 移库：等待打包
    WaitForSettle = 101         # 移库：等待结账
    ShipmentFinish = 102        # 移库：已关闭

    code = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    next_status = models.IntegerField(null=True, blank=True)
    role = models.CharField(max_length=50, null=True, blank=True)       # 当处于这个状态时，可操作的角色是什么
    permissions = models.CharField(max_length=100, null=True, blank=True)  # 当处于这个状态时，需要的权限是什么


class PurchasingOrder(models.Model):
    # 采购单中每个商品的详情
    # order = models.ForeignKey(PurchasingOrder, related_name='items')
    MarketplaceId = models.CharField(max_length=50)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')       # 如果parent不为空，说明是子采购单
    # 采购单合同
    contract_number = models.CharField(max_length=100)    # 合同号
    supplier = models.CharField(max_length=255)           # 供应商
    contact_person = models.CharField(max_length=50, null=True, blank=True)     # 联系人
    contact_phone = models.CharField(max_length=50, null=True, blank=True)
    traffic_comment = models.CharField(max_length=255, null=True, blank=True)   # 物流说明
    operator = models.CharField(max_length=100, null=True, blank=True)          # 经办人

    # 订单信息
    creator = models.ForeignKey(User, null=True, blank=True)                   # 采购单创建人
    create_time = models.DateTimeField(null=True, blank=True)   # 采购单创建时间
    status = models.ForeignKey(OrderStatus)      # 采购单状态
    total_price = models.FloatField(null=True, blank=True)  # 商品总价
    expect_date = models.DateField(null=True, blank=True)   # 交期

    # 数量相关
    count = models.IntegerField(null=True, blank=True, default=0)       # 采购数量
    expect_count = models.IntegerField(null=True, blank=True, default=0)    # 已发货数量
    received_count = models.IntegerField(null=True, blank=True, default=0)    # 已到货数量
    damage_count = models.IntegerField(null=True, blank=True, default=0)    # 损坏数量

    # 费用相关
    deposit = models.FloatField(null=True, blank=True)      # 预付款
    deposit_payed = models.FloatField(null=True, blank=True)    # 已缴纳的预付款
    traffic_fee = models.FloatField(null=True, blank=True)  # 物流费
    traffic_fee_payed = models.FloatField(null=True, blank=True)    # 已缴纳的物流费
    final_payment = models.FloatField(null=True, blank=True)    # 尾款
    final_payment_payed = models.FloatField(null=True, blank=True)  # 已交尾款
    other_fee = models.FloatField(null=True, blank=True)    # 杂费
    other_fee_payed = models.FloatField(null=True, blank=True)      # 已缴纳的杂费
    total_payed = models.FloatField(null=True, blank=True)      # 总支付的数额
    # next_to_pay = models.FloatField(null=True, blank=True)      # 下一步需要支付的数额
    # next_payment_comment = models.TextField(max_length=255, null=True, blank=True)  # 支付说明


class PurchasingOrderItems(models.Model):
    order = models.ForeignKey(PurchasingOrder, related_name='items')
    product = models.ForeignKey(Product, related_name='purchasing_orders')
    SellerSKU = models.CharField(max_length=50)
    name = models.CharField(max_length=255, null=True, blank=True)      # 商品名称
    # 采购信息
    total_price = models.FloatField(null=True, blank=True)  # 商品总价
    count = models.IntegerField(null=True, blank=True)      # 数量
    price = models.FloatField(null=True, blank=True)   # 采购单价
    expect_count = models.IntegerField(null=True, blank=True, default=0)    # 已发货数量
    received_count = models.IntegerField(null=True, blank=True, default=0)    # 已到货数量
    damage_count = models.IntegerField(null=True, blank=True, default=0)    # 损坏数量
    # 费用
    total_fee = models.FloatField(null=True, blank=True)    # 总费用
    traffic_fee = models.FloatField(null=True, blank=True)  # 物流费
    other_fee = models.FloatField(null=True, blank=True)    # 杂费
    unit_price = models.FloatField(null=True, blank=True)   # 最终单价=（数量*单价+物流费+杂费）/数量


class OrderFee(models.Model):
    # 订单付款记录
    order = models.ForeignKey(PurchasingOrder, related_name='fee_records')
    fee = models.FloatField()
    create_time = models.DateTimeField()
    comment = models.CharField(max_length=255, null=True, blank=True)


class TrackingOrder(models.Model):
    # 物流单
    purchasing_order = models.ForeignKey(PurchasingOrder, related_name='inbounds')
    shipping_date = models.DateField()      # 发货时间
    input_date = models.DateField(null=True, blank=True)   # 到货日期
    tracking_company = models.CharField(max_length=255, null=True, blank=True)      # 物流公司
    tracking_number = models.CharField(max_length=255, null=True, blank=True)      # 物流单号
    final_payment = models.FloatField(null=True, blank=True)        # 尾款
    traffic_fee = models.FloatField(null=True, blank=True)          # 物流费
    traffic_fee_payed = models.FloatField(null=True, blank=True)    # 已缴纳的物流费
    status = models.ForeignKey(OrderStatus)
    expect_count = models.IntegerField(null=True, blank=True)    # 已发货数量
    received_count = models.IntegerField(null=True, blank=True)    # 已到货数量
    damage_count = models.IntegerField(null=True, blank=True)    # 损坏数量


class TrackingOrderItems(models.Model):
    purchasing_order = models.ForeignKey(PurchasingOrder)
    traffic_order = models.ForeignKey(TrackingOrder, related_name='items')
    shipping_date = models.DateField(null=True, blank=True)      # 发货时间
    input_date = models.DateField(null=True, blank=True)   # 到货日期
    product = models.ForeignKey(Product)
    expect_count = models.IntegerField(null=True, blank=True)       # 发货数量
    received_count = models.IntegerField(null=True, blank=True, default=0)    # 实际到货数据
    damage_count = models.IntegerField(null=True, blank=True, default=0)    # 损坏数量


class PaymentRecord(models.Model):
    # 费用缴纳记录
    order = models.ForeignKey(PurchasingOrder, related_name='payments')
    traffic_order = models.ForeignKey(TrackingOrder, null=True, blank=True)
    need_payed = models.FloatField(null=True, blank=True)        # 需付款数
    payed = models.FloatField()             # 实际付款数
    pay_time = models.DateTimeField()       # 付款时间
    creator = models.ForeignKey(User, null=True, blank=True)       # 付款人
    fee_comment = models.CharField(max_length=100, null=True, blank=True)   # 款项说明
    payment_comment = models.CharField(max_length=255, null=True, blank=True)   # 支付说明