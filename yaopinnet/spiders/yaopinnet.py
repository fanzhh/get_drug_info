from scrapy.spiders import Spider
from scrapy.selector import Selector
import re
import csv
import scrapy

from yaopinnet.items import YaopinnetItem

class DescriptionSpider(Spider):
    name = "description"

    def __init__(self,approve_number_file='miss5.txt',*args,**kwargs):
        super(DescriptionSpider,self).__init__(*args,**kwargs)
        self.approve_number_file = approve_number_file
        self.aprove_number = ''

    def generate_urls(self,approve_number_file):
        approve_numbers = list(csv.reader(open(approve_number_file,'rt')))
        urls = []
        url_template_h = 'http://www.yaopinnet.com/%s/%s/%s.htm'
        url_template_z = 'http://www.yaopinnet.com/%s/%s.htm'
        for number in approve_numbers:
            tmp = number[0].lower()
            class1 = tmp[4]
            class2 = tmp[4] + tmp[-2:]
            class3 = tmp.upper()[-9:]
            print(tmp,class1,class2,class3)
            if 'z' in tmp:
                urls.append(url_template_z % (class2,class3))
            else:
                urls.append(url_template_h % (class1,class2,class3))
        return [urls,approve_numbers]

    def start_requests(self):
        urls, numbers = self.generate_urls(self.approve_number_file)[0], self.generate_urls(self.approve_number_file)[1]
        for i,url in enumerate(urls):
            yield scrapy.Request(url=url, callback=self.parse, meta={"number":numbers[i]})

    def parse(self, response):
        if response.status != 404:
            shuomingshu_url = response.xpath("//div/a[contains(.//text(),'说明书')]//@href").extract()[0]
            shuomingshu_url = 'http://www.yaopinnet.com' + shuomingshu_url
            # print(response.meta['number'],shuomingshu_url)
            yield scrapy.Request(url=shuomingshu_url,callback=self.parse2, meta={"number":response.meta['number']})

    def parse2(self,response):
        if response.status != 404:
            tmps = response.xpath("//div[@id='sms_content']/text()").extract()
            tmps = [x.replace("\r\n", "").strip() for x in tmps]
            tmps = list(filter(None, tmps))
            if not tmps:
                tmps = response.xpath('//li/text()').extract()
                tmps = [x for x in tmps if x != '\u3000']
            number = response.meta['number']
            dispensatory = '\r\n'.join(tmps)
            item = YaopinnetItem()
            item['approve_code'] = number
            item['description'] = dispensatory
            yield item