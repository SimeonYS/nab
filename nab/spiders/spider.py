import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import NabItem
from itemloaders.processors import TakeFirst

pattern = r'(\xa0)?'

class NabSpider(scrapy.Spider):
	name = 'nab'
	start_urls = ['https://news.nab.com.au/']

	def parse(self, response):
		categories = response.xpath('//div[@class="col6 hidden-mobile visible-desktop"]/ul/li[position()>1]/a')
		for category in categories:
			category_name = category.xpath('.//text()').get()
			yield response.follow(category, self.parse_links, cb_kwargs=dict(category=category_name))

	def parse_links(self, response, category):
		post_links = response.xpath('//h3/a/@href').getall()
		for link in post_links:
			yield response.follow(link, self.parse_post, cb_kwargs=dict(category=category))

		next_page = response.xpath('//a[@class="next page-numbers"]/@href').get()
		if next_page:
			yield response.follow(next_page, self.parse_links, cb_kwargs=dict(category=category))

	def parse_post(self, response, category):
		date = response.xpath('//b[@class="text-red"]/text()').get()
		title = response.xpath('//h1/text()').get()
		content = response.xpath('//div[@class="main-content"]//text()[not (ancestor::p[@class="wp-caption-text"])]').getall()
		content = [p.strip() for p in content if p.strip()]
		content = re.sub(pattern, "",' '.join(content))

		item = ItemLoader(item=NabItem(), response=response)
		item.default_output_processor = TakeFirst()

		item.add_value('title', title)
		item.add_value('link', response.url)
		item.add_value('content', content)
		item.add_value('date', date)
		item.add_value('category', category)

		yield item.load_item()
