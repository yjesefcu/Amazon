#-*- coding:utf-8 -*-
"""
将数据格式化成excel需要的格式
"""
__author__ = 'liucaiyun'
import sys, xlwt, os
from xlwt import *
from django.conf import settings
from models import *
from serializer import *
reload(sys)
sys.setdefaultencoding('utf-8')

WIDTH = 256 * 12
HEIGHT = 256 * 15
DEFAULT_ROW_HEIGHT = xlwt.easyxf('font:height 480;')
DEFAULT_IMAGE_HEIGHT = xlwt.easyxf('font:height 1280;')


#styleBlueBkg = xlwt.easyxf('font: color-index red, bold on')
#styleBlueBkg = xlwt.easyxf('font: background-color-index red, bold on')
# bgRed = xlwt.easyxf('pattern: pattern solid, fore_colour red;')
# bgBlue = xlwt.easyxf('pattern: pattern solid, fore_colour blue;')
# bgLightBlue = xlwt.easyxf('pattern: pattern solid, fore_colour light_blue; font: bold on;')
# bgPaleBlue = xlwt.easyxf('pattern: pattern solid, fore_colour pale_blue; font: bold on;')
# bgDarkBlue = xlwt.easyxf('pattern: pattern solid, fore_colour dark_blue; font: bold on;')
# bgDarkBlueEga = xlwt.easyxf('pattern: pattern solid, fore_colour dark_blue_ega; font: bold on;')
# bgOceanBlue = xlwt.easyxf('pattern: pattern solid, fore_colour ocean_blue; font: bold on;') # 80% like
# bgSkyBlue = xlwt.easyxf('pattern: pattern solid, fore_colour sky_blue; font: bold on;')
bgIceBlueBold = xlwt.easyxf('pattern: pattern solid, fore_colour ice_blue; font: bold on;')
bgLightYellowBold = xlwt.easyxf('pattern: pattern solid, fore_colour light_yellow; font: bold on;')
bgLightPinkBold = xlwt.easyxf('pattern: pattern solid, fore_colour pink; font: bold on;')
bgLinkGreyBold = xlwt.easyxf('pattern: pattern solid, fore_colour gray25; font: bold on;')
bgSilverEgaBold = xlwt.easyxf('pattern: pattern solid, fore_colour silver_ega; font: bold on;')

bgIceBlue = xlwt.easyxf('pattern: pattern solid, fore_colour ice_blue;')
bgLightYellow = xlwt.easyxf('pattern: pattern solid, fore_colour light_yellow;')
bgLightPink = xlwt.easyxf('pattern: pattern solid, fore_colour pink;')
bgLinkGrey = xlwt.easyxf('pattern: pattern solid, fore_colour gray25;')
bgSilverEga = xlwt.easyxf('pattern: pattern solid, fore_colour silver_ega;')

current_color = bgIceBlue
current_bold_color = bgIceBlueBold

#blueBkgFontStyle = xlwt.XFStyle()
#blueBkgFontStyle.Pattern = blueBackgroundPattern;
#styleBlueBkg = blueBkgFontStyle;

styleBold = xlwt.easyxf('font: bold on')


def add_product_info_to_fields(index, fields):
    fields.insert(index, u'描述')
    fields.insert(index, u'图片')
    fields.insert(index, u'SKU')


def create_excel_path(settlement):
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    filename = '%s - %s_%s.xls' % (settlement.StartDate.date(), settlement.EndDate.date(), timestamp)
    p = os.path.join(settings.MEDIA_ROOT, 'download')
    if not os.path.exists(p):
        os.mkdir(p)
    return 'download/%s' % filename


class DataExport(object):

    def __init__(self, settlement):
        self.settlement = settlement
        self.wb = Workbook()

    def _save(self, filename):
        # name = 'd:\\%s - %s.xls' % (self.settlement.StartDate.date(), self.settlement.EndDate.date())
        style = XFStyle()
        font = Font()
        font.name = 'SimSun' # 指定“宋体”
        style.font = font
        self.wb.save(filename)

    def export(self):
        filename = create_excel_path(self.settlement)
        records = ProductSettlement.objects.select_related('product').filter(settlement=self.settlement)\
            .order_by('product__SellerSKU', 'is_total')
        self.format_product_settlement(records)
        self._save_settlement_orders()
        self.add_products()
        self._save(os.path.join(settings.MEDIA_ROOT, filename))
        return '/media/' + filename

    def format_product_settlement(self, records):
        """
        ProductSettlement to excel data
        """
        descriptions = [u'SKU', u'图片', u'描述', u'数量', u'商品价格', u'促销返点', u'亚马逊收取', u'实收', u'仓储费',
                        u'广告费', u'订阅费', u'总成本', u'利润', u'利润率']
        fields = ['product', 'quantity', 'income', 'promotion', 'amazon_cost', 'amount', 'storage_fee', 'advertising_fee',
                  'subscription_fee', 'total_cost', 'profit', 'profit_rate']
        sheet = self.wb.add_sheet(u'总计')
        current_row = 1
        for col in range(0, len(descriptions)):
            set_row_height(sheet, current_row)
            sheet.write(current_row, col+1, descriptions[col])
        items = ProductSettlementSerializer(records, many=True).data
        for item in items:
            current_row += 1
            product = item['product']
            if item['is_total']:
                product = {'SellerSKU': u'商品统计'}
            set_row_height(sheet, current_row)
            # else:
            #     set_image_height(sheet, current_row)
            col = 0
            for field in fields:
                col += 1
                if field == 'product':
                    set_col_width(sheet, col, 256*20)
                    add_to_col(sheet, current_row, col, product.get('SellerSKU', ''), item.get('is_total'))
                    image = product.get('Image', '')
                    set_col_width(sheet, col+1, 256*14)
                    if image:
                        image_path = os.path.join(os.path.dirname(settings.MEDIA_ROOT), image[1:])
                        sheet.insert_bitmap(image_path, current_row, col+1, x=0, y=0)
                    else:
                        add_to_col(sheet, current_row, col+1, '', item.get('is_total'))
                    add_to_col(sheet, current_row, col+2, product.get('TitleCn', ''), item.get('is_total'))
                    col += 2
                else:
                    add_to_col(sheet, current_row, col, item.get(field, ''), item.get('is_total'))

    def _save_settlement_detail(self, settlement):
        """
        将settlement的订单按 订单、退货、移除、弃置等写入表格
        :param product:
        :return:
        """
        pass

    def _save_settlement_orders(self):
        sheet_name = u'订单详细'
        ws = self.wb.add_sheet(sheet_name)
        # 订单
        orders = SettleOrderItem.objects.select_related('product').filter(settlement=self.settlement).exclude(is_total=True, product__isnull=False)\
            .order_by('is_total', 'PostedDate')
        row = self._format_orders(ws, 0, orders, is_product=False)
        # 退货
        refunds = RefundItem.objects.select_related('product').filter(settlement=self.settlement).exclude(is_total=True, product__isnull=False)\
            .order_by('is_total', 'PostedDate')
        row = self._format_refunds(ws, row+1, refunds, is_product=False)
        # 赔偿
        losts = OtherTransactionItem.objects.select_related('product').filter(settlement=self.settlement).exclude(is_total=True, product__isnull=False)\
            .order_by('is_total', 'PostedDate')
        row = self._format_losts(ws, row+1, losts, is_product=False)
        # 弃置
        removals = ProductRemovalItem.objects.select_related('product').filter(settlement=self.settlement).exclude(is_total=True, product__isnull=False)\
            .order_by('is_total', 'UpdateDate')
        row = self._format_removals(ws, row+1, removals, is_product=False)
        # 结算
        settlement = ProductSettlement.objects.get(settlement=self.settlement, product__isnull=True)
        self._format_product_settlement(ws, row+1, settlement, is_product=True)

    def add_products(self):
        for ps in ProductSettlement.objects.filter(settlement=self.settlement, product__isnull=False).select_related('product'):
            product = ps.product
            self._save_orders(product)

    def _save_orders(self, product):
        sheet_name = product.SellerSKU
        ws = self.wb.add_sheet(sheet_name)
        # 订单
        orders = SettleOrderItem.objects.filter(settlement=self.settlement, product=product)\
            .order_by('is_total')
        # orders = SettleOrderItem.objects.select_related('product').filter(settlement=self.settlement)\
        #     .exclude(product__isnull=False, is_total=True).order_by('product__SellerSKU', 'is_total')
        row = self._format_orders(ws, 0, orders, is_product=True)
        # 退货
        refunds = RefundItem.objects.filter(settlement=self.settlement, product=product)\
            .order_by('is_total')
        row = self._format_refunds(ws, row+1, refunds, is_product=True)
        # 赔偿
        losts = OtherTransactionItem.objects.filter(settlement=self.settlement, product=product)\
            .order_by( 'is_total')
        row = self._format_losts(ws, row+1, losts, is_product=True)
        # 弃置
        removals = ProductRemovalItem.objects.filter(settlement=self.settlement, product=product)\
            .order_by('is_total')
        row = self._format_removals(ws, row+1, removals, is_product=True)
        # 结算
        settlement = ProductSettlement.objects.get(settlement=self.settlement, product=product)
        self._format_product_settlement(ws, row+1, settlement, is_product=True)

    def _format_orders(self, sheet, start_row, orders, is_product=False):
        if orders.count() < 2:
            return start_row
        descriptions = [u'日期', u'数量', u'商品价格', u'促销返点', u'亚马逊收取', u'实收',
                        u'订阅费', u'总成本', u'利润', u'利润率']
        fields = ['PostedDate', 'Quantity', 'income', 'promotion', 'amazon_cost', 'amount',
                  'subscription_fee', 'total_cost', 'profit', 'profit_rate']
        serializer_class = SimpleOrderItemSerializer if is_product else OrderItemSerializer
        items = serializer_class(orders, many=True).data
        global current_color, current_bold_color
        current_color = bgIceBlue
        current_bold_color = bgIceBlueBold
        col_len = len(descriptions) if is_product else len(descriptions) + 3
        add_title(sheet, start_row+1, col_len, u'所有订单')
        return self._add_items_to_sheet(sheet, start_row+2, descriptions, fields, is_product, items)

    def _format_refunds(self, sheet, start_row, refunds, is_product=False):
        if refunds.count() < 2:
            return start_row
        descriptions = [u'日期', u'数量', u'商品价格', u'促销返点', u'亚马逊收取', u'实收',
                        u'订阅费', u'总成本', u'利润', u'利润率']
        fields = ['PostedDate', 'Quantity', 'income', 'promotion', 'amazon_cost', 'amount',
                  'subscription_fee', 'total_cost', 'profit', 'profit_rate']
        serializer_class = SimpleRefundItemSerializer if is_product else RefundItemSerializer
        items = serializer_class(refunds, many=True).data
        col_len = len(descriptions) if is_product else len(descriptions) + 3
        global current_color, current_bold_color
        current_color = bgLightYellow
        current_bold_color = bgLightYellowBold
        add_title(sheet, start_row+1, col_len, u'退货')
        return self._add_items_to_sheet(sheet, start_row+2, descriptions, fields, is_product, items)

    def _format_losts(self, sheet, start_row, losts, is_product=False):
        if losts.count() < 2:
            return start_row
        descriptions = [u'日期', u'数量', u'商品价格', u'促销返点', u'亚马逊收取', u'实收',
                        u'订阅费', u'总成本', u'利润', u'利润率']
        fields = ['PostedDate', 'Quantity', 'income', 'promotion', 'amazon_cost', 'amount',
                  'subscription_fee', 'total_cost', 'profit', 'profit_rate']
        serializer_class = SimpleProductLostSerializer if is_product else ProductLostSerializer
        items = serializer_class(losts, many=True).data
        col_len = len(descriptions) if is_product else len(descriptions) + 3
        global current_color, current_bold_color
        current_color = bgSilverEga
        current_bold_color = bgSilverEgaBold
        add_title(sheet, start_row+1, col_len, u'赔偿')
        return self._add_items_to_sheet(sheet, start_row+2, descriptions, fields, is_product, items)

    def _format_removals(self, sheet, start_row, removals, is_product=False):
        if removals.count() < 2:
            return start_row
        descriptions = [u'日期', u'数量', u'商品价格', u'促销返点', u'亚马逊收取', u'实收',
                        u'订阅费', u'总成本', u'利润', u'利润率']
        fields = ['PostedDate', 'Quantity', 'income', 'promotion', 'amazon_cost', 'amount',
                  'subscription_fee', 'total_cost', 'profit', 'profit_rate']
        serializer_class = SimpleProductRemovalItemSerializer if is_product else ProductRemovalItemSerializer
        items = serializer_class(removals, many=True).data
        col_len = len(descriptions) if is_product else len(descriptions) + 3
        global current_color, current_bold_color
        current_color = bgLinkGrey
        current_bold_color = bgLinkGreyBold
        add_title(sheet, start_row+1, col_len, u'弃置')
        return self._add_items_to_sheet(sheet, start_row+2, descriptions, fields, is_product, items)

    def _format_product_settlement(self, sheet, start_row, settlement, is_product=False):
        descriptions = [u'日期', u'数量', u'商品价格', u'促销返点', u'亚马逊收取', u'实收',
                        u'订阅费', u'总成本', u'利润', u'利润率']
        fields = ['PostedDate', 'Quantity', 'income', 'promotion', 'amazon_cost', 'amount',
                  'subscription_fee', 'total_cost', 'profit', 'profit_rate']
        serializer_class = SimpleProductSettlementSerializer if is_product else ProductSettlementSerializer
        items = serializer_class(settlement).data
        col_len = len(descriptions) if is_product else len(descriptions) + 3
        global current_color, current_bold_color
        current_color = bgLightPink
        current_bold_color = bgLightPinkBold
        add_title(sheet, start_row+1, col_len, u'总计')
        return self._add_items_to_sheet(sheet, start_row+2, descriptions, fields, is_product, items)

    @classmethod
    def _add_items_to_sheet(cls, sheet, start_row, descriptions, fields, is_product, items):
        if not is_product:
            add_product_info_to_fields(1, descriptions)
            fields.insert(1, 'product')
        current_row = start_row
        for col in range(0, len(descriptions)):
            set_row_height(sheet, current_row)
            sheet.write(current_row, col, descriptions[col], current_color)
        if not isinstance(items, list):
            items = [items]
        for item in items:
            current_row += 1
            product = item.get('product', {})
            is_total = item['is_total']
            if is_total:
                product = {'SellerSKU': u'总计'}
            col = 0
            row = sheet.row(current_row)
            tall_style = xlwt.easyxf('font:height 360;') # 36pt,类型小初的字号
            row.set_style(tall_style)
            for field in fields:
                if field == 'product':
                    if not is_product:
                        add_to_col(sheet, current_row, col, product.get('SellerSKU', ''), is_total)
                        image = product.get('Image', '')
                        set_col_width(sheet, col+1, 256*14)
                        if image:
                            image_path = os.path.join(os.path.dirname(settings.MEDIA_ROOT), image[1:])
                            sheet.insert_bitmap(image_path, current_row, col+1, x=0, y=0)
                        else:
                            add_to_col(sheet, current_row, col+1, '', item.get('is_total'))
                        add_to_col(sheet, current_row, col+2, product.get('TitleCn', ''), is_total)
                        col += 3
                else:
                    add_to_col(sheet, current_row, col, item.get(field, ''), is_total)
                    col += 1
            # if not is_product:
            #     set_image_height(sheet, current_row)
        return current_row

    def add_sheet(self, sheet_name, data):
        ws = self.wb.add_sheet(sheet_name)
        rows = len(data)
        cols = len(data[0])
        for row in range(0, rows):
            set_row_height(ws, row)
            for col in range(0, cols):
                set_col_width(ws, col)
                ws.write(row + 1, col+1, data[row][col])


def add_to_col(sheet, r, c, value, is_total):
    if is_total:
        sheet.write(r, c, value, current_bold_color)
    else:
        sheet.write(r, c, value, current_color)
    # sheet.write(r, c, value, current_color)


def set_row_height(sheet, row_index):
    row = sheet.row(row_index)
    tall_style = DEFAULT_ROW_HEIGHT # 36pt,类型小初的字号
    row.set_style(tall_style)


def set_col_width(sheet, col_index, width=None):
    col = sheet.col(col_index)
    col.width = width if width else WIDTH


def set_image_height(sheet, row_index):
    row = sheet.row(row_index)
    tall_style = DEFAULT_IMAGE_HEIGHT # 36pt,类型小初的字号
    row.set_style(tall_style)


def add_title(sheet, r, col_len, value):
    bg = current_bold_color
    sheet.write(r, 0, value, bg)
    set_row_height(sheet, r)
    for c in range(1, col_len):
        set_col_width(sheet, c)
        sheet.write(r, c, '', bg)


def add_description(sheet, r, col_len, value):
    bg = current_color
    sheet.write(r, 0, value, bg)
    set_row_height(sheet, r)
    for c in range(1, col_len):
        set_col_width(sheet, c)
        sheet.write(r, c, '', bg)