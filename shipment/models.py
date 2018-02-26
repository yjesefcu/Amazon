#-*- coding:utf-8 -*-


from django.db import models
from products.models import Product
from purchasing.models import OrderStatus

# Create your models here.


class ShipmentOrder(models.Model):
    MarketplaceId = models.CharField(max_length=50)
    create_time = models.DateTimeField()
    count = models.IntegerField(null=True, blank=True)       # 发货总数量
    product_count = models.IntegerField(null=True, blank=True)   # 商品类型总数
    company = models.CharField(max_length=100, null=True, blank=True)       # 物流公司
    tracking_number = models.CharField(max_length=100, null=True, blank=True)   # 快递单号
    code = models.CharField(max_length=100, null=True, blank=True)      # 货件号
    ship_type = models.CharField(max_length=10, default='sea')                   # 货运类型，sea：海运，air：空运
    volume_args = models.IntegerField(default=5000)                 # 体积参数：5000/6000
    boxed_count = models.IntegerField(default=0)        # 已装箱商品数量
    box_count = models.IntegerField(default=0)          # 箱子数
    total_weight = models.FloatField(default=0)         # 实际总重量 kg
    total_itn_weight = models.FloatField(default=0)     # 实际总重量 ib. 英镑
    status = models.ForeignKey(OrderStatus, null=True, blank=True)   # 订单状态
    traffic_fee = models.FloatField(null=True, blank=True)      # 总运费
    tax_fee = models.FloatField(null=True, blank=True)          # 关税


class ShipmentOrderItem(models.Model):
    order = models.ForeignKey(ShipmentOrder, related_name='items')
    SellerSKU = models.CharField(max_length=50)
    product = models.ForeignKey(Product, related_name='shipments')
    count = models.IntegerField()       # 发货数量
    boxed_count = models.IntegerField(default=0)        # 已装箱数
    volume_weight = models.FloatField(null=True, blank=True)        # 体积重
    unit_weight = models.FloatField(null=True, blank=True)      # 单位重量，取体积重与重量重较大的那一个
    traffic_fee = models.FloatField(null=True, blank=True)
    tax_fee = models.FloatField(null=True, blank=True)


class ShipmentBox(models.Model):
    order = models.ForeignKey(ShipmentOrder, related_name='boxs')
    count = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)       # 包装重量 kg
    height = models.FloatField(null=True, blank=True)       # 包装高度 cm
    length = models.FloatField(null=True, blank=True)       # 包装长度 cm
    width = models.FloatField(null=True, blank=True)       # 包装宽度 cm
    itn_weight = models.FloatField(null=True, blank=True)       # 包装重量 ib. 英磅
    itn_height = models.FloatField(null=True, blank=True)       # 包装高度 in. 英寸
    itn_length = models.FloatField(null=True, blank=True)       # 包装长度 in. 英寸
    itn_width = models.FloatField(null=True, blank=True)       # 包装宽度 in. 英寸
    products = models.TextField(null=True, blank=True)



class BoxProductRelations(models.Model):
    # 每个箱子里可能放多个商品
    order = models.ForeignKey(ShipmentOrder)
    box = models.ForeignKey(ShipmentBox)
    order_item = models.ForeignKey(ShipmentOrderItem)
    count = models.IntegerField()