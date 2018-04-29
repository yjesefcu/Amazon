#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import os, datetime, chardet, threading, pytz
from django.conf import settings
from rest_framework_extensions.mixins import NestedViewSetMixin
from rest_framework.viewsets import ModelViewSet
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F
from amazon_services.exception import TextParseException
from amazon_services.models import MarketAccount
from models import *
from serializer import *
from api import FileImporter, to_float, get_float, ValidationChecker, ProductIncomeCalc, SettlementIncomeCalc
from errors import Error
from data_export import DataExport

TZ_ASIA = pytz.timezone('Asia/Shanghai')


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class SettlementViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = Settlement.objects.all()
    serializer_class = SettlementSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('MarketplaceId',)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    @detail_route(methods=['get'])
    def check(self, request, pk):
        """
        计算前检查数据的有效性
        """
        instance = self.get_object()
        # 数据是否有效，主要是广告数据
        if not instance.advertising_report_valid:
            return Response({'data_sync_valid': False})
        invalid_products = ValidationChecker(instance).check()
        sku_list = [p.SellerSKU for p in invalid_products]
        advertising_valid = True if instance.advertising_fee_adjust else False
        return Response({'products': ',  '.join(sku_list), 'storage_imported': instance.storage_imported,
                         'removal_imported': instance.removal_imported, 'advertising_valid': advertising_valid,
                         'data_sync_valid': True})

    @detail_route(methods=['get'])
    def calc_income(self, request, pk):
        # 计算销售总收入
        settlement = Settlement.objects.get(pk=pk)
        SettlementIncomeCalc(settlement).calc()
        return Response('success')

    @detail_route(methods=['get'])
    def calc(self, request, pk):
        from api import SettlementCalc, ProductProfitCalc
        instance = self.get_object()
        recalc_product = request.query_params.get('withProduct', True)
        if instance.calc_status == Error.RUNNING:
            return Response({'errno': Error.RUNNING})
        threading.Thread(target=SettlementCalc(settlement=instance).calc_settlement, args=[recalc_product, ]).start()
        return Response({'errno': Error.SUCCESS})

    @detail_route(methods=['get'])
    def calc_cost(self, request, pk):
        # 计算多个商品的成本，计算完后会自动计算利润
        from api import ProductProfitCalc
        settlement = self.get_object()
        ids = request.query_params.get('products', None)
        if ids:
            # 计算一个或多个商品的利润
            id_list = ids.split(',')
            products = Product.objects.filter(id__in=id_list)
            for p in products:
                isvalid = ValidationChecker(settlement).check_product(p)      # 先检查商品数据是否合法，主要对比实际库存是否大于订单数量
                if not isvalid:
                    return Response({'response': "error", 'errno': Error.INVALID_DATA,
                                     'message': '%s的亚马逊库存小与订单的数量，无法计算' % p.SellerSKU})
            calculator = ProductProfitCalc(settlement)
            for p in products:
                calculator.calc_product_cost(p)
        return Response({'result': 'success', 'errno': Error.SUCCESS})

    @detail_route(methods=['get'])
    def calc_profit(self, request, pk):
        # 只计算利润，不重新计算成本
        from api import ProductProfitCalc
        settlement = self.get_object()
        ids = request.query_params.get('products', None)
        if ids:
            # 计算一个或多个商品的利润
            id_list = ids.split(',')
            products = Product.objects.filter(id__in=id_list)
            calculator = ProductProfitCalc(settlement)
            for p in products:
                calculator.calc_product_profit(p)
        return Response({'result': 'success', 'errno': Error.SUCCESS})

    @detail_route(methods=['get'])
    def calcStatus(self, request, pk):
        instance = self.get_object()
        return Response({'errno': instance.calc_status})

    @list_route(methods=['get'])
    def sync(self, request):
        # 同步数据
        from sync_handler import update_all
        market_place_id = request.query_params.get('MarketplaceId')
        market = MarketAccount.objects.get(MarketplaceId=market_place_id)
        if market.sync_report_status == 10:
            return Response({'errno': Error.RUNNING})
        threading.Thread(target=update_all, args=[market, ]).start()
        return Response({'errno', Error.RUNNING})

    @list_route(methods=['get'])
    def syncStatus(self, request):
        # 查询同步数据的状态
        market_place_id = request.query_params.get('MarketplaceId')
        market = MarketAccount.objects.get(MarketplaceId=market_place_id)
        return Response({'errno': market.sync_report_status})

    @detail_route(methods=['post'])
    def storage_upload(self, request, pk):
        instance = self.get_object()
        my_file = request.FILES.get("file", None)    # 获取上传的文件，如果没有文件，则默认为None
        if not my_file:
            return Response({'errno': -1})
        text = ''
        for chunk in my_file.chunks():      # 分块写入文件
            text += unicode(chunk, chardet.detect(chunk)['encoding'])
        try:
            items = FileImporter().import_storage(text, instance)
        except TextParseException, ex:
            return Response({'errno': 1})
        instance.storage_imported = True
        instance.save()
        return Response({'error': 0, 'data': ProductRemovalItemSerializer(items, many=True).data})

    @detail_route(methods=['patch'])
    def advertising(self, request, pk):
        instance = self.get_object()
        serializer_class = self.get_serializer_class()
        fee = to_float(request.data.get('advertising_fee_adjust'))

        if abs(fee - to_float(instance.advertising_fee_adjust)) > 0.1:
            products = ProductSettlement.objects.filter(settlement=instance, advertising_fee__isnull=False, is_total=False)
            count = products.count()
            diff = fee - to_float(instance.advertising_fee)
            if count > 0:
                avg = diff / count
                # 将每个商品的广告费加上avg
                products.update(advertising_fee=F('advertising_fee') + avg)
            else:   # 如果没有商品有广告费，那么平均到有订单的商品上
                product_id_list = set(SettleOrderItem.objects.filter(settlement=instance, is_total=False).values_list('product', flat=True))
                products = ProductSettlement.objects.filter(settlement=instance, is_total=False, product__id__in=product_id_list)
                avg = fee / products.count()
                products.update(advertising_fee=avg)

            # 平均到有广告费的商品上
            instance.advertising_fee = fee
            instance.advertising_fee_adjust = fee
            instance.save()
        return Response(serializer_class(instance).data)

    @detail_route(methods=['post'])
    def advertising_upload(self, request, pk):
        # 上传广告报告
        instance = self.get_object()
        my_file = request.FILES.get("file", None)    # 获取上传的文件，如果没有文件，则默认为None
        if not my_file:
            return Response({'errno': -1})
        text = ''
        for chunk in my_file.chunks():      # 分块写入文件
            text += unicode(chunk, chardet.detect(chunk)['encoding'])
        try:
            FileImporter().import_advertising(text, instance)
        except TextParseException, ex:
            return Response({'errno': 1})
        instance.advertising_imported = True
        instance.save()
        return Response({'error': 0})

    @detail_route(methods=['get'])
    def download(self, request, pk):
        instance = self.get_object()
        filename = DataExport(instance).export()
        return Response({'path': filename})


class ProductViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductWithGigftsSeriazlier
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('MarketplaceId',)

    def create(self, request, *args, **kwargs):
        product = Product.objects.create(**request.data)
        serializer = self.get_serializer(product)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data
        for field in request.data:
            setattr(instance, field, data.get(field))
        instance.save()

        # 同时更新市场商品
        market_products = Product.objects.filter(SellerSKU=instance.SellerSKU).exclude(MarketplaceId='public')
        fields = ['SellerSKU', 'ASIN', 'FNSKU', 'Brand', 'Color', 'Image', 'Title', 'TitleCn', 'ProductGroup',
                  'width', 'height', 'length', 'weight', 'package_width', 'package_height', 'package_length', 'package_weight',
                  'volume_weight', 'gifts']
        for field in fields:
            if field in data:
                for p in market_products:
                    setattr(p, field, data.get(field))
        for p in market_products:
            p.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def settlements(self, request, pk):
        product = self.get_object()
        settlements = ProductSettlement.objects.filter(product=product)
        serializer = ProductSettlementSerializer(settlements, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def sync(self, request):
        from sync_handler import update_product
        update_product()

    @detail_route(methods=['get'])
    def calc(self, request, pk):
        # 计算某个产品的成本
        product = Product.objects.get(pk=pk)

    @list_route(methods=['get'], url_path='gifts')
    def get_all_gifts(self, request):
        products = Product.objects.filter(MarketplaceId="public", gifts__isnull=False)
        return Response(ProductWithGigftsSeriazlier(products, many=True).data)

    @detail_route(methods=['get', 'post'], url_path='gifts')
    def get_or_add_gifts(self, request, pk):
        product = self.get_object()
        if request.method == 'POST':
            gifts = request.data.get("gifts")
            product.gifts = gifts if gifts else None
            product.save()
            return Response()
        else:
            if not product.gifts:
                return Response([])
            else:
                gifts_sku_list = product.gifts.split(',')
                gifts = Product.objects.filter(MarketplaceId="public", SellerSKU__in=gifts_sku_list)
                return Response(self.get_serializer(gifts, many=True).data)


class GiftPackingViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = GiftPacking.objects.all()
    serializer_class = GiftPackingSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def create(self, request, *args, **kwargs):
        items = request.data.get('items')
        now = datetime.datetime.now()
        for item in items:
            product = Product.objects.get(MarketplaceId="public", SellerSKU=item['product'].get('SellerSKU'))
            count = int(item.get('count'))
            GiftPacking.objects.create(product=product, count=count,
                                       create_time=now)
            # 从各自商品的库存中减去，并将所有成本相加
            gifts = Product.objects.filter(SellerSKU__in=product.gifts.split(','))
            cost = 0
            for p in gifts:
                p.domestic_inventory = (p.domestic_inventory - count) if p.domestic_inventory else -count
                p.save()
                cost += int(p.supply_cost) if p.supply_cost else 0
            # 计算最终商品的成本，增加库存
            if product.domestic_inventory and product.supply_cost:
                product.supply_cost = (product.supply_cost * product.domestic_inventory + cost * count) / (product.domestic_inventory + count)
            else:
                product.supply_cost = cost
            product.domestic_inventory = (product.domestic_inventory + count) if product.domestic_inventory else count
            product.save()
        return Response()


class SupplyViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = InboundShipment.objects.select_related('product').all()
    serializer_class = InboundShipmentSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    # filter_backends = (DjangoFilterBackend,)
    # filter_fields = ('product',)

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        # 计算单位成本
        instance.inventory = instance.count
        instance.real_inventory = instance.count
        instance.unit_cost = to_float(instance.unit_price) + (to_float(instance.total_freight)+to_float(instance.charges)) / instance.count
        instance.save()
        # 更新product的库存
        _query_dict = self.get_parents_query_dict()
        product = Product.objects.get(MarketplaceId="public", pk=_query_dict['product'])
        product.domestic_inventory += instance.inventory
        product.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.real_inventory < instance.count:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # 更新商品库存信息
        instance.product.domestic_inventory -= instance.count
        instance.product.save()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductShipmentItemViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = OutboundShipmentItem.objects.all()
    serializer_class = OutboundShipmentItemSerializer


class ProfitProductFilter(object):

    def filter_queryset(self, request, queryset, view):
        data = request.query_params
        if 'product' in data:
            product = data.get('product')
            if not product:
                queryset = queryset.filter(product__isnull=True)
            else:
                queryset = queryset.filter(product__pk=product)
        queryset = queryset.filter(is_total=data.get('is_total', False))
        return queryset


class ProductSettlementFilter(object):

    def filter_queryset(self, request, queryset, view):
        data = request.query_params
        if 'product' in data:
            product = data.get('product')
            if not product:
                queryset = queryset.filter(product__isnull=True)
            else:
                queryset = queryset.filter(product__pk=product)
        return queryset


class SettlementProductViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = ProductSettlement.objects.select_related('product').all()
    serializer_class = ProductSettlementSerializer
    filter_backends = (DjangoFilterBackend, ProductSettlementFilter,)
    filter_fields = ('settlement', 'product')


class OrderViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = SettleOrderItem.objects.select_related('product').all()
    serializer_class = SimpleOrderItemSerializer
    filter_backends = (DjangoFilterBackend, ProfitProductFilter,)
    # filter_fields = ('settlement', 'product', 'is_total')

    @detail_route(methods=['patch'])
    def cost(self, request, pk):
        # 更新成本
        instance = self.get_object()
        instance.update_unit_cost(request.data.get('cost'))
        return Response(self.get_serializer_class()(instance).data)


class OutboundShipmentItemViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = OutboundShipmentItem.objects.all()
    serializer_class = OutboundShipmentItemSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.inventory < instance.QuantityShipped:   # 如果库存<原始数量，说明已经计算过成本，则无法删除
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # 补充到Supply中
        supplies = InboundShipment.objects.filter(product=instance.product, real_inventory__lt=F('count'))
        diff = instance.QuantityShipped
        for supply in supplies:
            tmp = supply.count - supply.real_inventory
            if tmp >= diff:
                supply.real_inventory += diff
                supply.save()
                break
            supply.real_inventory = supply.count
            supply.save()
            diff -= tmp
        # 补充supply end
        # 更新商品库存
        instance.product.amazon_inventory -= instance.QuantityShipped
        instance.product.domestic_inventory += instance.QuantityShipped
        instance.product.save()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OutboundShipmentViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = OutboundShipment.objects.all()
    serializer_class = OutboundShipmentSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('MarketplaceId',)

    def create(self, request, *args, **kwargs):
        # 先检查商品SKU是否都存在
        data = request.data
        not_exists = self._check_product(data)
        if not_exists:
            return Response({
                'result': 'fail',
                'msg': not_exists
            }, status=status.HTTP_400_BAD_REQUEST)
            del data['products']
        products = data.get('products', [])
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        items = self._create_or_update_items(serializer.instance, products)
        return_data = serializer.data
        return_data['products'] = OutboundShipmentItemSerializer(items, many=True).data
        return Response(return_data, status=status.HTTP_201_CREATED, headers=headers)

    def _check_product(self, data):
        """
        检查商品是否存在，或数量是否合理
        :param data:
        :return:
        """
        if 'products' not in data:
            return None
        products_data = data['products']
        existed = list(Product.objects.all().values_list('SellerSKU', flat=True))
        not_exist = list()
        for p in products_data:
            if p['SellerSKU'] not in existed:
                not_exist.append(p['SellerSKU'])
        if not_exist:
            return u', '.join(not_exist) + u': 商品不存在，请先创建商品'

        # 计算配送数量是否合理
        sku_list = [p['SellerSKU'] for p in products_data]
        inventory = dict(Product.objects.filter(SellerSKU__in=sku_list).values_list('SellerSKU', 'domestic_inventory'))
        count_exceed = list()
        for p in products_data:
            if 'id' in p:
                item = OutboundShipmentItem.objects.get(pk=p['id'])
                count = int(p['QuantityShipped']) - item.QuantityShipped
            else:
                count = int(p['QuantityShipped'])
            if count > inventory[p['SellerSKU']]:
                count_exceed.append(p['SellerSKU'])
        if count_exceed:
            return u', '.join(count_exceed) + u': 数量超过国内库存数量，请确认数量是否正确。或先添加入库货件信息。'

    def update(self, request, *args, **kwargs):
        # 先检查商品SKU是否都存在
        data = request.data
        not_exists = self._check_product(data)
        if not_exists:
            return Response({
                'result': 'fail',
                'msg': not_exists
            }, status=status.HTTP_400_BAD_REQUEST)
            del data['products']
        # 更新shipment信息
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # 更新items
        self._create_or_update_items(instance, data.get('products'))
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def _create_or_update_items(self, shipment, data):
        if not data:
            return []
        items = list()
        for item in data:
            product = Product.objects.get(MarketplaceId="public", SellerSKU=item['SellerSKU'])
            # 计算体积重
            s, created = OutboundShipmentItem.objects.get_or_create(shipment=shipment, MarketplaceId=shipment.MarketplaceId, product=product)
            # 商品库存信息修改
            if int(item['QuantityShipped']) != s.QuantityShipped:
                self._update_inventory(s, int(item['QuantityShipped']) - s.QuantityShipped)
            s.inventory += int(item['QuantityShipped']) - s.QuantityShipped
            for key, value in item.items():
                setattr(s, key, value)
            s.unit_cost = (get_float(item, 'total_freight')+get_float(item, 'duty')) / int(item['QuantityShipped'])
            s.ShipmentId = shipment.ShipmentId
            s.ship_date = shipment.ship_date
            s.save()

            # 如果商品本身长宽高为空，则补充长宽高
            if not product.width or not product.height or not product.length:
                product.width = item['width']
                product.height = item['height']
                product.length = item['length']
                product.save()
            items.append(s)
        return items

    def _calc_supply_cost(self, product):
        # 计算商品当前的国内平均入库成本
        inbounds = InboundShipment.objects.filter(product=product, inventory__gt=0)
        amount = 0
        quantity = 0
        for inbound in inbounds:
            quantity += inbound.inventory
            amount += inbound.inventory * inbound.unit_cost
        return amount / quantity if quantity else 0

    def _update_inventory(self, shipment_item, count):
        # 更新商品库存
        product = shipment_item.product
        product.domestic_inventory -= count   # 如果数量变更，需要相应的更改商品的库存信息
        product.amazon_inventory += count
        product.save()
        # 更新InboundShipment的库存
        inbounds = InboundShipment.objects.filter(product=product, real_inventory__gt=0)
        tmp_count = count
        for inbound in inbounds:
            if tmp_count <= inbound.real_inventory:
                inbound.real_inventory -= tmp_count
                inbound.save()
                break
            tmp_count -= inbound.real_inventory
            inbound.real_inventory = 0
            inbound.save()

    def destroy(self, request, *args, **kwargs):        # 删除
        instance = self.get_object()
        # 需要将子项全部删除后才可删除这条记录
        if instance.products.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RefundViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = RefundItem.objects.select_related('product').all()
    serializer_class = SimpleRefundItemSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend, ProfitProductFilter,)
    # filter_fields = ('settlement', 'product', 'is_total')

    @detail_route(methods=['patch'])
    def cost(self, request, pk):
        # 更新成本
        instance = self.get_object()
        instance.update_unit_cost(request.data.get('cost'))
        return Response(self.get_serializer_class()(instance).data)


class RemovalViewSet(NestedViewSetMixin, ModelViewSet):

    queryset = ProductRemovalItem.objects.select_related('product').all()
    serializer_class = SimpleProductRemovalItemSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend, ProfitProductFilter,)
    # filter_fields = ('settlement', 'product', 'is_total')

    @detail_route(methods=['patch'])
    def cost(self, request, pk):
        # 更新成本
        instance = self.get_object()
        instance.update_unit_cost(request.data.get('cost'))
        return Response(self.get_serializer_class()(instance).data)

    @list_route(methods=['post'])
    def upload(self, request, *args, **kwargs):

        my_file = request.FILES.get("file", None)    # 获取上传的文件，如果没有文件，则默认为None
        if not my_file:
            return Response({'errno': -1})
        text = ''
        for chunk in my_file.chunks():      # 分块写入文件
            text += unicode(chunk, chardet.detect(chunk)['encoding'])
        try:
            _query_dict = self.get_parents_query_dict()
            settlement = Settlement.objects.get(pk=_query_dict['settlement'])
            items = FileImporter().import_removals(text, settlement)
            settlement.removal_imported = True
            settlement.save()
        except TextParseException, ex:
            return Response({'errno': 1})
        items = ProductRemovalItem.objects.filter(settlement=settlement, is_total=False)
        return Response({'error': 0, 'data': ProductRemovalItemSerializer(items, many=True).data})


class ProductLostViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = OtherTransactionItem.objects.select_related('product').all()
    serializer_class = SimpleProductLostSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    filter_backends = (DjangoFilterBackend, ProfitProductFilter,)
    # filter_fields = ('settlement', 'product', 'is_total')

    @detail_route(methods=['patch'])
    def cost(self, request, pk):
        # 更新成本
        instance = self.get_object()
        instance.update_unit_cost(request.data.get('cost'))
        return Response(self.get_serializer_class()(instance).data)


class AdvertisingViewSet(NestedViewSetMixin, ModelViewSet):
    queryset = AdvertisingProductItems.objects.select_related('product').all()
    serializer_class = AdvertisingItemSerializer
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)