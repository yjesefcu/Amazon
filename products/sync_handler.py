#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import datetime, logging, json
import dateutil.parser
from django.utils.timezone import utc
from amazon_services.service import *
from amazon_services.models import MarketAccount
from api import *


logger = logging.getLogger('product')


DT_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def update_product(market=None):
    """
    完善商品信息
    :param market:
    """
    market_id = market.MarketplaceId if market else 'ATVPDKIKX0DER'
    products = Product.objects.filter(MarketplaceId=market_id, ASIN__isnull=True)
    # 5个一组
    length = 5
    for group in [products[i:i+length] for i in xrange(0, len(products), length)]:
        sku_list = [p.SellerSKU for p in group]
        products = ProductService(market).get_products(sku_list)
        if products:
            for product in products:
                update_product_to_db(product)


def update_settlement(market=None):
    """
    同步结算结果
    :param market:
    """
    service = SettlementReportService(market)
    if not market:
        market = MarketAccount()
        market.MarketplaceId = Marketplace_EN
    # 检查当前settlement是否已经都同步了
    period_start = market.period_start
    # end_date_list = list(Settlement.objects.all().values_list('EndDate', flat=True))
    # count = len(end_date_list)
    # for i in range(0, count):
    #     end_date_list[i] = end_date_list[i].date()
    # all_synced = True
    # if count:
    #     if (datetime.date.today() - end_date_list[0]).days >= 14:
    #         all_synced = False
    #     else:
    #         for i in range(1, count):
    #             if (end_date_list[i-1] - end_date_list[i]).days != 14:
    #                 all_synced = False
    #                 break
    #             if len(end_date_list) == count - 1:
    #                 if (end_date_list[i] - period_start).days >= 28:
    #                     all_synced = False
    # else:
    #     all_synced = False
    # if all_synced:
    #     logger.info('Settlement all synced, return')
    #     return
    reports = service.get_list()
    report_id_list = list(Settlement.objects.all().values_list('report_id', flat=True))
    if not reports:
        print 'Settlement Report is None'
        return
    reports.reverse()
    for report in reports:
        available_date = dateutil.parser.parse(report['AvailableDate']).replace(tzinfo=None).date()
        if available_date < period_start:
            continue
        report_id = report['ReportId']
        if report_id in report_id_list:
            continue
        logger.info('get settlement data of report: %s', report_id)
        settlement_data = service.get_one(report_id)
        # 确认是否是一个市场的
        if settlement_data['SettlementData']['currency'] != market.currency_code:
            continue
        start_date = dateutil.parser.parse(settlement_data['SettlementData']['StartDate']).replace(tzinfo=None)
        end_date = dateutil.parser.parse(settlement_data['SettlementData']['EndDate']).replace(tzinfo=None)
        # 如果EndDate与StartDate不是相差14天，则不计算
        if (end_date.date() - start_date.date()).days != 14:
            continue
        try:
            SettlementDataRecord.objects.get(data_type=SettlementDataRecord.SETTLEMENT, start_time=start_date)
            logger.info('Settlement already updated: %s ~ %s', start_date, end_date)
            continue
        except SettlementDataRecord.DoesNotExist, ex:
            pass
        logger.info('start update Settlement : %s ~ %s', start_date, end_date)
        handler = SettlementDbHandler(market)
        settlement = handler.update_settlement_to_db(settlement_data)
        settlement.report_id = report_id
        settlement.save()
        # 结算总收入
        SettlementIncomeCalc(settlement).calc()
        SettlementDataRecord.objects.create(data_type=SettlementDataRecord.SETTLEMENT, start_time=settlement.StartDate,
                                         end_time=settlement.EndDate, settlement=settlement)


def update_advertising_report(market, settlement):

    def _update_to_db(ads):
        if ads is None:
            logger.info('get weekday advertising fail')
            return False

        if len(ads) == 0:
            return True
        else:
            return update_product_advertising_to_db(settlement, ads)
        # end _update_to_db

    logger.info('start update advertising of settlement: %s ~ %s', settlement.StartDate, settlement.EndDate)
    service = AdvertiseReportService(market)
    start = settlement.StartDate.replace(hour=0, minute=0, second=0)
    end = settlement.EndDate.replace(hour=0, minute=0, second=0)
    SUNDAY = 6
    tmp_start = start
    weekly_report_type = '_GET_PADS_PRODUCT_PERFORMANCE_OVER_TIME_WEEKLY_DATA_TSV_'
    data_valid = True
    while tmp_start < end:
        #  读取数据
        if tmp_start.weekday() != SUNDAY:
            weekday_start = tmp_start - datetime.timedelta(days=(tmp_start.weekday()+1))     # 取最近的一个周日
        else:
            weekday_start = tmp_start
        # 如果SettlementDataRecord中存在记录，说明数据已读取并保存
        if SettlementDataRecord.objects.filter(settlement=settlement, start_time=tmp_start, data_type=SettlementDataRecord.ADVERTISE).exists():
            tmp_start = weekday_start + datetime.timedelta(days=7)
            continue

        try:
            request_record = ReportRequestRecord.objects.get(report_type=weekly_report_type, start_time=weekday_start)
        except ReportRequestRecord.DoesNotExist, ex:
            request_record = None

        if request_record:
            if request_record.report_id:
                items = service.get_items_by_report_id(request_record.report_id)
            else:
                # 如果之前请求过，但是未生成报告，则重新生成
                request_record.delete()
                items = service.get_by_week(weekday_start)
        else:   # 之前没请求过，重新请求
            items = service.get_by_week(weekday_start)
        update_success = _update_to_db(items)
        if not update_success:
            data_valid = False
        else:
            SettlementDataRecord.objects.get_or_create(settlement=settlement, start_time=tmp_start,
                                                     data_type=SettlementDataRecord.ADVERTISE)
        tmp_start = weekday_start + datetime.timedelta(days=7)  # 取最近的一个周日

    if data_valid:
        logger.info('success update advertising of settlement: %s ~ %s', settlement.StartDate, settlement.EndDate)
        settlement.advertising_report_valid = True
        # 更新每个产品的广告费
        product_id_list = set(AdvertisingProductItems.objects.filter(settlement=settlement).values_list('product__id', flat=True))
        for product_id in product_id_list:
            try:
                product_settlement = ProductSettlement.objects.get(product__id=product_id, settlement=settlement, is_total=False)
                advertising_fee = sum_queryset(AdvertisingProductItems.objects.filter(settlement=settlement, product__id=product_id), 'cost')
                product_settlement.advertising_fee = advertising_fee
                product_settlement.save()
            except ProductSettlement.DoesNotExist, ex:
                pass
        advertising_fee = sum_queryset(ProductSettlement.objects.filter(settlement=settlement, is_total=False,
                                                                        product__isnull=False), 'advertising_fee')
        settlement.advertising_fee = advertising_fee
    else:
        logger.info('failed update advertising of settlement: %s ~ %s', settlement.StartDate, settlement.EndDate)
        settlement.advertising_report_valid = False
    settlement.save()
    return settlement.advertising_report_valid


def update_all(market):
    # 总的更新入口
    # if market.sync_report_status == 10:
    #     return
    market.sync_report_status = 10
    market.save()
    exception = False
    try:
        update_settlement(market)

        # settlements = Settlement.objects.filter(advertising_report_valid=False).order_by('StartDate')
        # for settlement in settlements:
        #     try:
        #         valid = update_advertising_report(market, settlement)
        #         if valid:
        #             ProductIncomeCalc().calc_income(settlement)
        #     except BaseException, ex:
        #         exception = True
        #         logger.error('update_advertising eception, settlement: %s ~ %s, exception:%s',
        #                      settlement.StartDate, settlement.EndDate, traceback.format_exc())
        update_product(market)
        market.sync_report_status = 0
    except BaseException, ex:
        exception = True
        logger.error(traceback.format_exc())
    if exception:
        market.sync_report_status = 1
    market.save()