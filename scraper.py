#!/usr/bin/env python3

from scrapy import Item, Field, signals, Request, Selector
from scrapy.http import response
from scrapy.spiders import Spider
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from twisted.internet import reactor
from datetime import date
from enum import Enum
import csv, json, sys

class LegoItem(Item):
    set_num = Field()
    set_name = Field()
    new_value = Field()
    used_value = Field()
    used_range = Field()
    retail_price = Field()


class LegoPipeline:
    def process_item(self, item: dict, spider: Spider):
        set_details = list(item.keys())[0].split(' ')
        set_values = list(item.values())[0]
        set_num = set_details[0]
        set_name = set_details[1].replace('-', ' ')
        used_value = set_values[7]
        used_range = set_values[8]
        retail_price = set_values[1]
        clean_item = {
                'set_num': set_num,
                'set_name': set_name,
                'used_value': used_value,
                'used_range': used_range,
                'retail_price': retail_price,
        }
        return clean_item

class CSVWriterPipeline:
    def __init__(self):
        self.fieldnames = [
                'Set Number', 'Set Name', 'Used Value',
                'Used Price Range', 'Retail Price']

        with open('Lego-Values.csv', 'w+') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()

    def process_item(self, item: dict, spider: Spider):
        with open('Lego-Values.csv', 'a') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerow(item)
        return item

class LegoSpider(Spider):
    name = "lego"
    root_url = 'https://www.brickeconomy.com'

    def __init__(self, *args, **kwargs):
        super(LegoSpider, self).__init__(*args, **kwargs)
        if not set_list:
            raise ValueError("You must supply an input file")
        self.set_list=set_list

    def start_requests(self):
        search_url = self.root_url+'/search?query='
        set_nums = [item.split(' ')[0] for item in set_list]
        urls = [search_url+str(set_num) for set_num in set_nums]

        for url in urls:
            yield Request(url=url,
                          callback=self.crawl_table,
                          cb_kwargs={
                              'set_num': url.split('=')[1]})

    def crawl_table(self, response: response.html.HtmlResponse, set_num: str):
        possible_links = Selector(text=response.body).xpath('//table[@id="ContentPlaceHolder1_ctlSetsOverview_GridViewSets"]/tr/td[@class="hidden-xs ctlsets-image"]/a/@href').getall()
        for link in possible_links:
            test_num = link.split('/')[2].split('-')[0]
            if test_num == set_num:
                set_details = link.split('/')[2:4]
                yield Request(url=self.root_url+link,
                              callback=self.parse_set,
                              cb_kwargs={'set_details': set_details})

    def parse_set(self, response: response.html.HtmlResponse, set_details: list):
        main_div = Selector(text=response.body).xpath('//div[@id="ContentPlaceHolder1_PanelSetPricing"]').get()
        price_list = Selector(text=main_div).xpath('//div[@class="row rowlist"]/div/text()').getall()

        item_details = {' '.join(set_details): price_list}

        return item_details

def callback(spider: Spider, reason: str):
    stats = spider.crawler.stats.get_stats()
    reactor.stop()

if __name__=='__main__':
    settings = Settings()
    settings.set('ITEM_PIPELINES', {
        '__main__.LegoPipeline': 0,
        '__main__.CSVWriterPipeline': 1,
    })

    try:
        in_file = sys.argv[1]
        with open(in_file, 'r') as f:
            set_list = [line.rstrip() for line in f.readlines()]
    except Exception as e:
        print("Error opening input file")
        raise e

    crawler = CrawlerProcess(settings)

    crawler.crawl(LegoSpider, set_list=set_list)
    crawler.start()
