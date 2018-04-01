#-*- coding:utf-8 -*-
from django.db import models

# Create your models here.


class Product(models.Model):
    MarketplaceId = models.CharField(max_length=30, db_index=True, null=True, blank=True)     # 市场Id
    SellerSKU = models.CharField(max_length=50, verbose_name='SKU', db_index=True)
    ASIN = models.CharField(max_length=20, null=True, blank=True, verbose_name='Asin', db_index=True)
    FNSKU = models.CharField(max_length=20, null=True, blank=True, verbose_name='FNSKU')
    Brand = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'品牌')
    Color = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'颜色')
    Amount = models.FloatField(null=True, blank=True, verbose_name=u'售价')   # 售价
    CurrencyCode = models.CharField(max_length=10, null=True, blank=True, verbose_name=u'货币单位')      # 货币代码：USD-美元
    Image = models.CharField(max_length=255, null=True, blank=True, verbose_name=u'图标')      # 图标
    TotalSupplyQuantity = models.IntegerField(null=True, blank=True)        #  亚马逊库存
    Title = models.TextField(null=True, blank=True, verbose_name=u'亚马逊描述')             # 商城描述
    TitleCn = models.TextField(null=True, blank=True, verbose_name=u'中文描述')           # 中文描述，手动输入
    Binding = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'类型')
    ProductGroup = models.CharField(max_length=50, null=True, blank=True)   # 商品分组
    ProductTypeName = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'商品所在分组')    # 商品分组名称
    width = models.FloatField(null=True, blank=True, verbose_name=u'宽度')    # 商品本身高度，单位cm
    height = models.FloatField(null=True, blank=True, verbose_name=u'高度')   # 商品本身高度，单位cm
    length = models.FloatField(null=True, blank=True, verbose_name=u'长度')   # 商品本身程度，单位cm
    weight = models.FloatField(null=True, blank=True, verbose_name=u'重量')   # 商品本身重量，单位kg
    package_width = models.FloatField(null=True, blank=True, verbose_name=u'包装宽度')  # 单位cm
    package_height = models.FloatField(null=True, blank=True, verbose_name=u'包装高度') # 单位cm
    package_length = models.FloatField(null=True, blank=True, verbose_name=u'包装长度') # 单位cm
    package_weight = models.FloatField(null=True, blank=True, verbose_name=u'包装重量') # 单位kg
    volume_weight = models.FloatField(null=True, blank=True, verbose_name=u'体积重')        # 体积重，height*width*length/5000
    domestic_inventory = models.IntegerField(default=0, verbose_name=u'国内库存')          # 商品剩余数量
    amazon_inventory = models.IntegerField(default=0, verbose_name=u'亚马逊库存')
    supply_cost = models.FloatField(null=True, blank=True)    # 国内成本：包括商品单价和运费
    shipment_cost = models.FloatField(null=True, blank=True)     # 国外成本：国内至亚马逊的运费
    cost = models.FloatField(default=0, verbose_name=u'成本')     # 当前商品成本
    last_supply = models.DateField(null=True, blank=True, verbose_name=u'上一次入库日期')
    last_oversea = models.DateField(null=True, blank=True, verbose_name=u'上一次移库日期')
    sold_count = models.IntegerField(default=0, verbose_name=u'已销售数量')
    gifts = models.CharField(max_length=255, null=True, blank=True)     # 赠品商品SKU

    class Meta:
        unique_together = (('MarketplaceId', 'SellerSKU',),)
        ordering = ['SellerSKU']

    def get_gifts(self):
        if not self.gifts:
            return None
        gifts = Product.objects.filter(SellerSKU__in=self.gifts.split(','))
        return gifts


class InboundShipment(models.Model):
    """
    发往国内的商品信息，以商品为维度
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    product = models.ForeignKey(Product, related_name='supplies')
    count = models.IntegerField(verbose_name=u'数量', null=True, blank=True)       # 商品数量
    inventory = models.IntegerField(verbose_name=u'库存', default=0, null=True, blank=True)      # 用于计算成本，在计算完订单后扣除
    real_inventory = models.IntegerField(null=True, blank=True)            # 实际库存
    # remain_count = models.IntegerField(verbose_name=u'剩余数量', default=0)    # count-发往国外的数量
    unit_price = models.FloatField(verbose_name=u'商品单价', null=True, blank=True)
    total_freight = models.FloatField(verbose_name=u'总运费', null=True, blank=True)
    charges = models.FloatField(null=True, blank=True, verbose_name=u'杂费')
    charges_comment = models.TextField(null=True, blank=True, verbose_name=u'杂费备注')
    ship_date = models.DateField(null=True, blank=True, verbose_name=u'到货日期')
    insert_time = models.DateTimeField(null=True, blank=True)   # 添加至数据库的时间
    unit_cost = models.FloatField(null=True, blank=True, verbose_name=u'单位成本')  # 包括单价与运费
    ShipmentName = models.CharField(max_length=50, null=True, blank=True)      # 是否是自动生成的，如果退货记录找不到对应的订单，则会生成该记录
    settlement_id = models.IntegerField(default=0)      # 0表示手动创建，>0表示settlement计算生成

    class Meta:
        ordering = ('-ship_date', )

    # def save(self, force_insert=False, force_update=False, using=None,
    #          update_fields=None):
    #     super(InboundShipment, self).save(force_insert, force_update, using, update_fields)
    #     # 更新Product.domestic_inventory
    #     self.product.domestic_inventory += self.count
    #     self.product.save()


class OutboundShipment(models.Model):
    """
    发往国外的货件，以货件为维度
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    ShipmentId = models.CharField(max_length=50)
    ShipmentName = models.CharField(max_length=255, null=True, blank=True)      # 您为入库货件提供的唯一名称。
    LabelPrepType = models.CharField(max_length=100, null=True, blank=True)     # 入库货件必需的标签准备的类型。
    ShipmentStatus = models.CharField(max_length=30, null=True, blank=True)
    ShipFromCity = models.CharField(max_length=50, null=True, blank=True)
    logistics_company = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'物流公司名称')
    logistics_id = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'物流运单号')
    ship_date = models.DateField(null=True, blank=True, verbose_name=u'发货时间')     # 发货时间
    total_freight = models.FloatField(null=True, blank=True, verbose_name=u'总运费')        # 总运费
    duty = models.FloatField(null=True, blank=True, verbose_name=u'总关税')
    comment = models.CharField(max_length=255, null=True, blank=True)
    settlement_id = models.IntegerField(default=0)      # 0表示手动创建，>0表示settlement计算生成

    class Meta:
        ordering = ['-ship_date']


class OutboundShipmentItem(models.Model):
    """
    每个货件里的商品信息
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    shipment = models.ForeignKey(OutboundShipment, related_name='products')
    ShipmentId = models.CharField(max_length=50, null=True, blank=True)
    ship_date = models.DateField(null=True, blank=True, verbose_name=u'发货时间')     # 发货时间
    product = models.ForeignKey(Product, related_name='shipsOversea')
    SellerSKU = models.CharField(max_length=50, null=True, blank=True)
    FulfillmentNetworkSKU = models.CharField(max_length=50, null=True, blank=True)      # 商品的亚马逊配送网络 SKU
    QuantityShipped = models.IntegerField(null=True, blank=True, default=0)     # 要配送的商品数量。
    unit_price = models.FloatField(null=True, blank=True, verbose_name=u'商品单价')     # 手动输入
    unit_freight = models.FloatField(null=True, blank=True, default=0, verbose_name=u'运费单价')       # 单位：kg
    fuel_tax = models.FloatField(null=True, blank=True, default=0, verbose_name=u'燃油附加税')       # 百分比
    duty = models.FloatField(null=True, blank=True, default=0, verbose_name=u'关税')
    width = models.FloatField(null=True, blank=True, verbose_name=u'商品宽度')      # cm
    height = models.FloatField(null=True, blank=True, verbose_name=u'商品高度')     # cm
    length = models.FloatField(null=True, blank=True, verbose_name=u'商品长度')     # cm
    weight = models.FloatField(null=True, blank=True, verbose_name=u'商品重量')     # kg
    volume_weight = models.FloatField(null=True, blank=True, verbose_name=u'体积重')   # kg
    unit_weight = models.FloatField(null=True, blank=True, verbose_name=u'体积参数')    # max(weight, volume_weight)

    total_freight = models.FloatField(null=True, blank=True, verbose_name=u'总运费')    # 通过计算获得：max(外箱体积重,外箱实际重)*运费单价*（1+燃油附加税） = 总运费
    inventory = models.IntegerField(null=True, blank=True, default=0, verbose_name=u'库存')
    unit_cost = models.FloatField(null=True, blank=True, verbose_name=u'移库单位成本')

    class Meta:
        ordering = ['SellerSKU', '-shipment__ship_date']


class Settlement(models.Model):
    """
    一次结算记录
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    report_id = models.CharField(max_length=50, null=True, blank=True)      # 读取报告的report_id
    AmazonSettlementID = models.CharField(max_length=100)
    TotalAmount = models.FloatField(null=True, blank=True)
    StartDate = models.DateTimeField(null=True, blank=True, verbose_name=u'结算开始日期')
    EndDate = models.DateTimeField(null=True, blank=True, verbose_name=u'结算结束日期')

    # 销售
    # subscription_fee_adjust = models.FloatField(null=True, blank=True, verbose_name=u'补偿金额')    # OtherTransaction.SubscriptionFeeAdj的总和
    custom_return_fee = models.FloatField(null=True, blank=True)    # 退货服务费，如果退货服务费的OtherTransaction没找到对应的RefundItem记录，则会记录在这里

    Quantity = models.IntegerField(null=True, blank=True, verbose_name=u'销售数量')           # 销售数量
    # 亚马逊部分
    sales = models.FloatField(default=0, verbose_name=u'订单')
    refund = models.FloatField(default=0, verbose_name=u'退货')
    other_fee = models.FloatField(default=0, verbose_name=u'其他服务费')     # 包括移除、弃置
    other_trade = models.FloatField(default=0, verbose_name=u'其他交易')     # 包括交易
    income = models.FloatField(null=True, blank=True, verbose_name=u'总收入')   # 计算

    # 成本
    advertising_fee = models.FloatField(null=True, blank=True)       # 广告费，需以负数保存
    advertising_fee_adjust = models.FloatField(null=True, blank=True, verbose_name=u'实际支付的总广告费')   # 如果advertising_fee<advertising_fee_adjust，那么需要将多余的平均到商品中
    storage_fee = models.FloatField(null=True, blank=True)           # 仓储费，需以负数保存
    subscription_fee = models.FloatField(null=True, blank=True, verbose_name=u'订阅费') # 手动
    cost = models.FloatField(null=True, blank=True, verbose_name=u'成本')
    total_cost = models.FloatField(null=True, blank=True, verbose_name=u'总成本')      # 总成本， cost+adverising_fee+storage_fee+subscription_fee

    profit = models.FloatField(null=True, blank=True, verbose_name=u'利润')           # 计算
    profit_rate = models.FloatField(null=True, blank=True, verbose_name=u'利润率')     # 计算

    # 数据和计算状态
    calc_status = models.IntegerField(default=0)        # 0：成功，1：失败，10：正在计算
    is_downloading = models.BooleanField(default=False)
    storage_imported = models.BooleanField(default=False)       # 月度仓储费是否已导入
    removal_imported = models.BooleanField(default=False)       # 移除报告是否已导入
    advertising_imported = models.BooleanField(default=False)   # 广告报告是否已导入

    class Meta:
        ordering = ['-EndDate']

    def update_cost(self, cost_diff):
        # 更新利润， cost指增加或减少的部分
        self.total_cost += cost_diff
        self.profit -= cost_diff
        self.profit_rate = self.profit/self.income if self.income else 0
        self.save()


class ProductSettlement(models.Model):
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement, related_name='products')
    product = models.ForeignKey(Product, null=True, blank=True)

    Quantity = models.IntegerField(null=True, blank=True)           # 销售数量
    # 销售环节
    custom_return_fee = models.FloatField(null=True, blank=True)    # 退货服务费，如果退货服务费的OtherTransaction没找到对应的RefundItem记录，则会记录在这里

    # 亚马逊
    sales = models.FloatField(default=0, verbose_name=u'销售')
    refund = models.FloatField(default=0, verbose_name=u'退货')
    other_fee = models.FloatField(default=0, verbose_name=u'其他服务费')     # 移除、弃置
    other_trade = models.FloatField(default=0, verbose_name=u'其他交易')     # 赔偿
    income = models.FloatField(null=True, blank=True)         # 总销售

    # 成本
    advertising_fee = models.FloatField(null=True, blank=True)       # 广告费，需以负数保存
    storage_fee = models.FloatField(null=True, blank=True)           # 仓储费，需以负数保存
    subscription_fee = models.FloatField(null=True, blank=True, verbose_name=u'订阅费')
    cost = models.FloatField(null=True, blank=True, verbose_name=u'成本')
    total_cost = models.FloatField(null=True, blank=True)           # 总成本， cost+adverising_fee+storage_fee+subscription_fee

    # 总计
    profit = models.FloatField(null=True, blank=True, verbose_name=u'利润')
    profit_rate = models.FloatField(null=True, blank=True, verbose_name=u'利润率')

    is_calculated = models.BooleanField(default=False)       # 是否计算过

    def update_cost(self, cost_diff):
        # 更新利润， cost指增加或减少的部分
        self.total_cost += cost_diff
        self.profit -= cost_diff
        self.profit_rate = self.profit/self.income if self.income else 0
        self.save()
        # 更新is_total的记录
        if not self.is_total:
            ProductSettlement.objects.get(settlement=self.settlement, is_total=True).update_cost(cost_diff)
        # 更新settlement的记录
        if self.is_total:
            self.settlement.update_cost(cost_diff)


class Refund(models.Model):
    """
    退款
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement, null=True, blank=True, related_name='refunds')   # 关联的结算周期
    AdjustmentID = models.CharField(max_length=100)
    AmazonOrderId = models.CharField(max_length=50, null=True, blank=True)
    MarketplaceName = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'商城名字')     # 如：Amazon.com
    PostedDate = models.DateTimeField(null=True, blank=True, verbose_name=u'提交时间')


class RefundItem(models.Model):
    """
    退款中的商品子项
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement, null=True, blank=True)   # 关联的结算周期
    MerchantAdjustmentItemID = models.CharField(max_length=50, null=True, blank=True)
    refund = models.ForeignKey(Refund, null=True, blank=True, related_name='items')
    AmazonOrderId = models.CharField(max_length=50, null=True, blank=True)
    OrderItemId = models.CharField(max_length=50, null=True, blank=True)
    PostedDate = models.DateTimeField(null=True, blank=True, verbose_name=u'提交时间')
    product = models.ForeignKey(Product, null=True, blank=True, related_name='refunds')     # product为空表示汇总记录
    SellerSKU = models.CharField(max_length=50, null=True, blank=True)
    order_item = models.ForeignKey('SettleOrderItem', null=True, blank=True)        # 退款关联的订单

    Quantity = models.IntegerField(null=True, blank=True)   # 销售的数量，从SettleOrderItem中读取
    # 销售部分
    UnitPrice = models.FloatField(null=True, blank=True, verbose_name=u'销售单价')
    Principal = models.FloatField(null=True, blank=True)        # 商品总价
    OtherPrice = models.FloatField(null=True, blank=True, verbose_name='买家其他退款')
    Fee = models.FloatField(null=True, blank=True, verbose_name='亚马逊费用退款')
    Promotion = models.FloatField(null=True, blank=True, verbose_name='促销返点')
    FBAReturnFee = models.FloatField(null=True, blank=True, verbose_name=u'退货服务费')      # 从OtherTransaction.OtherTransactionType=FBACustomerReturn的记录获取

    # 成本
    cost = models.FloatField(null=True, blank=True, verbose_name=u'单位成本')         # 成本，应该为正数
    # 汇总
    total_cost = models.FloatField(null=True, blank=True, verbose_name=u'总成本')  # subscription_fee + cost
    income = models.FloatField(null=True, blank=True, verbose_name=u'实收') #　= PriceAdjustmentAmount
    profit = models.FloatField(null=True, blank=True, default=0)    # 利润
    profit_rate = models.FloatField(null=True, blank=True)          # 利润率

    is_total = models.BooleanField(default=False)      # 是否是汇总项

    class Meta:
        ordering = ['-PostedDate']

    def update_unit_cost(self, cost):
        # 更新单位成本，cost指修改后单位成本
        diff = (float(cost) - self.cost) * self.quantity
        self.cost = cost
        self.update_cost(diff)
        # 更新total记录的成本
        RefundItem.objects.get(settlement=self.settlement, is_total=True, product=self.product).update_cost(diff)

    def update_cost(self, cost_diff):
        # 更新成本的差值
        self.total_cost += cost_diff
        self.profit -= cost_diff
        self.profit_rate = self.profit / self.income if self.income else 0
        self.save()
        if self.is_total:
            # 更新商品总记录
            ProductSettlement.objects.get(settlement=self.settlement, product=self.product).update_cost(cost_diff)


class OtherTransaction(models.Model):
    """
    其他服务费
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement, null=True, blank=True, related_name='other_transactions')   # 关联的结算周期
    TransactionID = models.CharField(max_length=50)
    AmazonOrderId = models.CharField(max_length=50, null=True, blank=True)
    TransactionType = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'服务费类型') # RemovalComplete:亚马逊物流移除费用，DisposalComplete：弃置服务费
    PostedDate = models.DateTimeField(null=True, blank=True, verbose_name=u'提交时间')
    Amount = models.FloatField(null=True, blank=True, verbose_name=u'总计')
    refund_item = models.ForeignKey('RefundItem', null=True, blank=True)        # AmazonOrderId对应的SettleOrderItem，为空说明没找到对应的订单
    SellerSKU = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['-PostedDate']


class OtherTransactionFee(models.Model):
    # 主要是移除和弃置，需要关联 ProductRemovalItem一起计算
    # 以下数据与关联的OtherTransaction一致
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement, related_name=u'removal_products')
    transaction = models.ForeignKey(OtherTransaction, related_name='fees')
    TransactionID = models.CharField(max_length=50)
    AmazonOrderId = models.CharField(max_length=50, null=True, blank=True)
    TransactionType = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'服务费类型') # RemovalComplete:亚马逊物流移除费用，DisposalComplete：弃置服务费
    PostedDate = models.DateTimeField(null=True, blank=True, verbose_name=u'提交时间')
    # 以下为Fee信息
    Type = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'付款详情')
    Amount = models.FloatField(null=True, blank=True, verbose_name=u'总计')


class ProductRemovalItem(models.Model):
    """
    移除商品信息
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement, related_name='removals')
    RequestDate = models.DateTimeField(null=True, blank=True)
    UpdateDate = models.DateTimeField(null=True, blank=True)
    OrderId = models.CharField(max_length=50, null=True, blank=True)
    OrderType = models.CharField(max_length=20, null=True, blank=True)     # Return/Disposal
    OrderStatus = models.CharField(max_length=20, null=True, blank=True)
    SellerSKU = models.CharField(max_length=50, null=True, blank=True)
    FNSKU = models.CharField(max_length=50, null=True, blank=True)
    Disposition = models.CharField(max_length=20, null=True, blank=True)       # Sellable/Unsellable
    product = models.ForeignKey(Product, related_name='removals', null=True, blank=True)

    Quantity = models.IntegerField(null=True, blank=True)
    # 亚马逊
    Fee = models.FloatField(null=True, blank=True)       # 弃置费用
    # 计算所得
    cost = models.FloatField(null=True, blank=True, verbose_name=u'单位成本')

    # 汇总
    total_cost = models.FloatField(null=True, blank=True, verbose_name=u'总成本')  # subscription_fee + cost
    income = models.FloatField(null=True, blank=True, verbose_name=u'亚马逊实收')     # = Fee
    profit = models.FloatField(null=True, blank=True, default=0)    # 利润
    profit_rate = models.FloatField(null=True, blank=True, default=0)

    is_total = models.BooleanField(default=False)      # 是否是汇总项

    def update_unit_cost(self, cost):
        # 更新单位成本，cost指修改后单位成本
        diff = (float(cost) - self.cost) * self.Quantity
        self.cost = cost
        self.update_cost(diff)
        # 更新total记录的成本
        ProductRemovalItem.objects.get(settlement=self.settlement, is_total=True, product=self.product).update_cost(diff)

    def update_cost(self, cost_diff):
        # 更新成本的差值
        self.total_cost += cost_diff
        self.profit -= cost_diff
        # self.profit_rate = self.profit / self.income if self.income else 0
        self.save()
        if self.is_total:
            # 更新商品总记录
            ProductSettlement.objects.get(settlement=self.settlement, product=self.product).update_cost(cost_diff)


class OtherTransactionItem(models.Model):
    # 赔偿
    # 以下数据与关联的OtherTransaction一致
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement)
    transaction = models.ForeignKey(OtherTransaction, related_name='items', null=True, blank=True)
    TransactionID = models.CharField(max_length=50, null=True, blank=True)
    AmazonOrderId = models.CharField(max_length=50, null=True, blank=True)
    TransactionType = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'服务费类型') # INCORRECT_FEES_ITEMS：费用更正，无需计算成本
    PostedDate = models.DateTimeField(null=True, blank=True, verbose_name=u'提交时间')
    product = models.ForeignKey(Product, null=True, blank=True)
    # 赔偿明细
    SellerSKU = models.CharField(max_length=50, null=True, blank=True)
    Quantity = models.IntegerField(null=True, blank=True)
    # 亚马逊
    UnitPrice = models.FloatField(null=True, blank=True, verbose_name=u'商品销售单价')   # Amount/Quantity
    Amount = models.FloatField(null=True, blank=True, verbose_name=u'赔偿价格')

    # 其他
    cost = models.FloatField(null=True, blank=True, verbose_name=u'单位成本')     # 如果是仓库丢失，需要扣除成本

    # 汇总
    income = models.FloatField(null=True, blank=True)       # = Amount
    total_cost = models.FloatField(null=True, blank=True, verbose_name=u'总成本')
    profit = models.FloatField(null=True, blank=True)   # 利润
    profit_rate = models.FloatField(null=True, blank=True)

    is_total = models.BooleanField(default=False)      # 是否是汇总项

    def update_unit_cost(self, cost):
        # 更新单位成本，cost指修改后单位成本
        diff = (float(cost) - self.cost) * self.Quantity
        self.cost = cost
        self.update_cost(diff)
        # 更新total记录的成本
        OtherTransactionItem.objects.get(settlement=self.settlement, is_total=True, product=self.product).update_cost(diff)

    def update_cost(self, cost_diff):
        # 更新成本的差值
        self.total_cost += cost_diff
        self.profit -= cost_diff
        self.profit_rate = self.profit / self.Amount if self.Amount else 0
        self.save()
        if self.is_total:
            # 更新商品总记录
            ProductSettlement.objects.get(settlement=self.settlement, product=self.product).update_cost(cost_diff)


class SellerDealPayment(models.Model):
    """
    促销费用
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement, null=True, blank=True, related_name='seller_deal_payments')   # 关联的结算周期
    DealID = models.CharField(max_length=255)
    PostedDate = models.DateTimeField(null=True, blank=True, verbose_name=u'提交时间')
    DealDescription = models.CharField(max_length=100, null=True, blank=True)
    MarketplaceName = models.CharField(max_length=100, null=True, blank=True, verbose_name=u'商城名字')     # 如：Amazon.com
    TransactionType = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'服务费类型')     # Lightning Deal Fee：秒杀费
    PaymentReason = models.CharField(max_length=100, null=True, blank=True)
    DealFeeType = models.CharField(max_length=100, null=True, blank=True)      # 促销类型
    DealFeeAmount = models.FloatField(null=True, blank=True)                   # 促销总费用

    class Meta:
        ordering = ['-PostedDate']


class AdvertisingTransactionDetails(models.Model):
    """
    广告费用
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement, null=True, blank=True, related_name='advertising_transactions')   # 关联的结算周期
    InvoiceId = models.CharField(max_length=100, verbose_name=u'发票ID')
    TransactionType = models.CharField(max_length=50, null=True, blank=True, verbose_name=u'服务费类型')
    PostedDate = models.DateTimeField(null=True, blank=True, verbose_name=u'提交时间')
    BaseAmount = models.FloatField(null=True, blank=True)
    TransactionAmount = models.FloatField(null=True, blank=True)


class AdvertisingProductItems(models.Model):
    """
    广告业绩报告的数据
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement, null=True, blank=True, related_name='advertising_products')   # 关联的结算周期
    StartDate = models.DateTimeField(null=True, blank=True)
    EndDate = models.DateTimeField(null=True, blank=True)
    SellerSKU = models.CharField(max_length=50, null=True, blank=True)
    TotalSpend = models.FloatField(null=True, blank=True)
    product = models.ForeignKey(Product, related_name='advertising_fees')
    cost = models.FloatField(null=True, blank=True)     # cost为TotalSpend+校正费用（实际支出-所有商品综合)/商品数


class SellerCouponPayment(models.Model):
    """
    优惠券返还
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement, null=True, blank=True, related_name='coupons')   # 关联的结算周期
    PostedDate = models.DateTimeField(null=True, blank=True)
    Amount = models.FloatField(default=0, null=True)    # 总额
    Count = models.IntegerField(default=0)      # 数量
    cost = models.FloatField(null=True, blank=True)     # cost = Amount


class SettleOrder(models.Model):
    """
    销售记录
    """
    MarketplaceId = models.CharField(max_length=30, db_index=True)     # 市场Id
    settlement = models.ForeignKey(Settlement, null=True, blank=True, related_name='orders')   # 关联的结算周期
    MarketplaceId = models.CharField(max_length=30, db_index=True)
    MarketplaceName = models.CharField(max_length=100, null=True, blank=True)
    AmazonOrderId = models.CharField(max_length=50, verbose_name=u'订单编号')
    ShipmentID = models.CharField(null=True, blank=True, max_length=50, verbose_name=u'物流ID')
    PostedDate = models.DateTimeField(null=True, blank=True, verbose_name=u'提交时间')   # USD

    class Meta:
        ordering = ['-PostedDate']


class SettleOrderItem(models.Model):
    settlement = models.ForeignKey(Settlement, null=True, blank=True, related_name='order_items')   # 关联的结算周期
    MarketplaceId = models.CharField(max_length=30, db_index=True, null=True, blank=True)
    # 从Order同步的信息
    order = models.ForeignKey(SettleOrder, related_name='items', null=True, blank=True)
    OrderItemId = models.CharField(max_length=20, null=True, blank=True)
    AmazonOrderId = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    PostedDate = models.DateTimeField(null=True, blank=True, verbose_name=u'提交时间')   # USD
    # 商品信息
    product = models.ForeignKey(Product, related_name='settle_items', null=True, blank=True)
    SellerSKU = models.CharField(max_length=50, null=True, blank=True)

    # 销售环节
    UnitPrice = models.FloatField(null=True, blank=True, verbose_name=u'单价')    # Principal/Quantity
    Quantity = models.IntegerField(null=True, blank=True)
    Principal = models.FloatField(null=True, blank=True, verbose_name=u'订单付款')
    OtherPrice = models.FloatField(null=True, blank=True, verbose_name='其他付款')
    Fee = models.FloatField(null=True, blank=True, verbose_name='亚马逊收取费用')
    Promotion = models.FloatField(null=True, blank=True, verbose_name='促销返款')
    income = models.FloatField(null=True, blank=True, verbose_name=u'销售实收') #　=Principal

    #成本
    advertising_fee = models.FloatField(null=True, blank=True)       # 广告费，需以负数保存
    storage_fee = models.FloatField(null=True, blank=True)           # 仓储费，需以负数保存
    subscription_fee = models.FloatField(null=True, blank=True, verbose_name=u'订阅费')     # 单位：USD，负数
    supply_cost = models.FloatField(null=True, blank=True, verbose_name=u'国内运费')        # 负数， = product.supply_cost
    shipment_cost = models.FloatField(null=True, blank=True, verbose_name=u'国际运费')       # 负数， = product.shipment_cost
    cost = models.FloatField(null=True, blank=True, default=0, verbose_name=u'单位成本')      # = product.cost，USD            # 负数
    total_cost = models.FloatField(null=True, blank=True, verbose_name=u'总成本')  # subscription_fee + cost

    # 汇总
    profit = models.FloatField(null=True, blank=True, default=0)    # 利润
    profit_rate = models.FloatField(null=True, blank=True)

    is_total = models.BooleanField(default=False)      # 是否是汇总项
    refund_order = models.ForeignKey(RefundItem, null=True, blank=True)     # 关联的退款订单

    class Meta:
        ordering = ['-PostedDate']

    def update_unit_cost(self, cost):
        # 更新单位成本，cost指修改后单位成本
        diff = (float(cost) - self.cost) * self.Quantity
        self.cost = cost
        self.update_cost(diff)
        # 更新total记录的成本
        SettleOrderItem.objects.get(settlement=self.settlement, is_total=True, product=self.product).update_cost(diff)

    def update_cost(self, cost_diff):
        # 更新成本的差值
        self.total_cost += cost_diff
        self.profit -= cost_diff
        self.profit_rate = self.profit / self.income if self.income else 0
        self.save()
        if self.is_total:
            # 更新商品总记录
            ProductSettlement.objects.get(settlement=self.settlement, product=self.product).update_cost(cost_diff)


class ProductReturn(models.Model):
    product = models.ForeignKey(Product)
    settlement = models.ForeignKey(Settlement, related_name='returns')
    snapshot_date = models.DateTimeField()
    type = models.CharField(max_length=20)
    SellerSKU = models.CharField(max_length=50)
    quantity = models.IntegerField()
    disposition = models.CharField(max_length=20)


class SettlementDataRecord(models.Model):
    """
    记录settlement相关数据是否已更新到数据库
    """
    SETTLEMENT = 'Settlement'
    REMOVAL = 'Removal'
    ADVERTISE = 'Advertising'

    settlement = models.ForeignKey(Settlement)
    data_type = models.CharField(max_length=20)     # 数据类型
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)


class GiftPacking(models.Model):
    # 赠品打包记录
    product = models.ForeignKey(Product)
    count = models.IntegerField()
    create_time = models.DateTimeField()