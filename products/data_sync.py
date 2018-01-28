#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'
import threading, traceback, logging
from amazon_services.models import MarketAccount
from sync_handler import update_all
logger = logging.getLogger('product')


class SyncThread(threading):

    def run(self):
        print 'start sync'
        market_place_id = 'ATVPDKIKX0DER'
        market = MarketAccount.objects.get(MarketplaceId=market_place_id)
        # threading.Thread(target=update_all, args=[market, ]).start()
        try:
            update_all(market)
        except BaseException, ex:
            traceback.format_exc()
            logger.error('update all failed:' + traceback.format_exc())

def start_sync():
    print 'start sync thread'
    SyncThread().start()
