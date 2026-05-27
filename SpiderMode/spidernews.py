import json
import os

import requests
from datetime import datetime
from lxml import etree
from concurrent.futures import ThreadPoolExecutor



class SpiderNews:
    base_url = 'https://www.people.com.cn/GB/59476/review/{}.html'
    date_str = datetime.now().strftime('%Y%m%d')

    def __init__(self):
        self.today_url = self.base_url.format(self.date_str)

    def fetch_news_item(self):
        response = requests.get(self.today_url)
        response.encoding = 'utf-8'
        html = etree.HTML(response.text)
        news_url_item = html.xpath('//td//li')
        self.news_url_lt = []
        for n in news_url_item:
            link = n.xpath('./a/@href')
            if link:
                self.news_url_lt.append(link[0].strip())

    def fetch_one(self, url):
        try:
            r = requests.get(url, timeout=10)
            r.encoding = 'utf-8'
            d = etree.HTML(r.text)
            title = d.xpath('//h1/text()')
            news_time = d.xpath('string(//*[@id="newstime"])')
            author = d.xpath('//*[@class="col-1-1"]//a/text()')
            content = d.xpath('//div[@id="rm_txt_zw"]//p/text()')
            return {
                "title": title[0].strip() if title else '',
                "news_time": news_time.strip() if news_time else '',
                "author": author[0].strip() if author else '',
                "content": "\n".join(content).strip()
            }
        except Exception as e:
            print(f"抓取失败 {url}: {e}")
            return None

    def fetch_news(self):
        self.fetch_news_item()
        self.news_data_lt = []

        with ThreadPoolExecutor(max_workers=5) as pool:
            results = pool.map(self.fetch_one, self.news_url_lt)

        for r in results:
            if r:
                self.news_data_lt.append(r)

        print(f"成功抓取 {len(self.news_data_lt)} 条新闻")
        return self.news_data_lt


if __name__ == "__main__":
    spider = SpiderNews()
    news = spider.fetch_news()
    with open(f'{os.getcwd()}/news_data_{spider.date_str}.json', 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=4)
