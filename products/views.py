#-*- coding:utf-8 -*-
import os, json
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, Http404
from django.conf import settings
from api import create_image_path
from amazon_services.models import MarketAccount
from models import *
from api import *
from serializer import ProductSerializer


def get_product_by_sku(request):
    sku = request.GET.get('SellerSKU')
    try:
        product = Product.objects.get(SellerSKU=sku)
        data = ProductSerializer(product).data
        return HttpResponse(json.dumps(data), content_type='application/json')
    except Product.DoesNotExist, ex:
        raise Http404


def sync_products(request):
    from sync_handler import update_product
    update_product()


def image_upload(request):
    if request.method == 'POST':
        my_file = request.FILES.get("image", None)    # 获取上传的文件，如果没有文件，则默认为None
        if not my_file:
            return HttpResponse("no files for upload!")
        file_path = create_image_path()
        absolute_path = os.path.join(settings.MEDIA_ROOT, file_path)
        destination = open(absolute_path, 'wb+')    # 打开特定的文件进行二进制的写操作
        for chunk in my_file.chunks():      # 分块写入文件
            destination.write(chunk)
        destination.close()
        io = Image.open(absolute_path)
        io.convert('RGB')
        io.save(absolute_path)
        return HttpResponse(settings.MEDIA_URL + file_path)


def sync_orders(request):
    from sync_handler import update_all
    market = MarketAccount.objects.get(MarketplaceId='ATVPDKIKX0DER')
    update_all(market)



def _init_refund_orders():
    from api import SettlementDbHandler
    market = MarketAccount.objects.first()
    handler = SettlementDbHandler(market)
    # for refund in RefundItem.objects.filter(order_item__isnull=True, quantity__isnull=True):
    #     quantity = handler._get_order_item_quantity_from_amazon(refund.OrderItemId, refund.AmazonOrderId)
    #     refund.quantity = quantity
    #     refund.save()

    for refund in RefundItem.objects.filter(order_item__isnull=True):
        try:
            order = SettleOrderItem.objects.get(OrderItemId=refund.OrderItemId)
            print 'found'
            refund.quantity = order.Quantity
            refund.order_item = order
            refund.save()
        except:
            pass


def _init_inbounds():
    import requests
    for product in Product.objects.all().order_by('pk'):
        data = {
            'MarketplaceId': product.MarketplaceId,
            'count': '500',
            'unit_price': '1.58',
            'total_freight': '625',
            'charges': '25',
            'ship_date': '2017-05-23',
            'product': '%d' % product.pk
        }
        url = 'http://127.0.0.1:8000/api/products/%d/supply/' % product.pk
        r = requests.post(url, data=data)
        if r.status_code != 201:
            print r.text
            break


def _init_shipment():
    outbound = None
    products = list()
    import requests
    for product in Product.objects.all().order_by('pk'):
        if not outbound:
            outbound = {
                'MarketplaceId': product.MarketplaceId,
                'ShipmentId': 'abcdefghi',
                'ship_date': '2017-05-03'
            }
        item = {
            'SellerSKU': product.SellerSKU,
            'QuantityShipped': '199',
            'unit_freight': '1.19',
            'fuel_tax': '0.15',
            'duty': '53',
            'package_length': '10.9',
            'package_width': '3.1',
            'package_height': '1.9',
            'package_weight': '1.1'
        }
        products.append(item)
    outbound['products'] = products
    url = 'http://127.0.0.1:8000/api/shipments/'
    import json
    r = requests.post(url, data=json.dumps(outbound), headers={'content-type': 'application/json'})
    print r.status_code


def calc_income(request):
    from amazon_services.service import SettlementReportService
    market = MarketAccount.objects.get(MarketplaceId='ATVPDKIKX0DER')
    pk = request.GET.get('id')
    settlement = Settlement.objects.get(pk=pk)

    service = SettlementReportService(market)
    settlement_data = service.get_one(settlement.report_id)

    SettlementDbHandler(market).update_settlement_to_db(settlement_data)
    SettlementIncomeCalc(settlement).calc()
    return HttpResponse('success')


# def upload_file(request):
#     if request.method == 'POST':
#         form = UploadFileForm(request.POST, request.FILES)
#
#         if form.is_valid():
#             handle_upload_file(request.FILES.get('file', None))
#             ftemp = request.FILES.get('file', None)
#             print('ftemp: ', ftemp)
#             return HttpResponseRedirect('/success/')
#     else:
#         form = UploadFileForm()
#
#     return render(request, 'upload.html', {'form':form})