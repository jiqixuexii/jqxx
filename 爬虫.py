import scrapy
import requests
from bs4 import BeautifulSoup
import re
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import jieba
import seaborn as sns

headers = {"User-Agent": "Mozilla/5.0"}
for n in range(0,250,25):
    url = 'https://movie.douban.com/top250?start={}&filter='.format(n)
    html = requests.get(url,headers=headers)
    html.encoding = 'utf-8'
    soup = BeautifulSoup(html.text, 'html.parser')
    for item in soup.find_all('div',"info"):
        title = item.div.a.span.string #获取标题
        yearline = item.find('div','bd').p.contents[2].string #获取年份那一行
        year = yearline.replace(' ','').replace('\n','')[0:4] #
        movie_url = item.div.a['href']  # 获取电影主页的url
        p = re.compile(r'\d+')
        movie_id = p.findall(movie_url)[0]  # 获取电影ID
        with open('./data/MovieTop250.txt','a+',encoding='utf-8') as f:
            print("{0}\t{1}\t{2}".format(movie_id,title,year),file=f)

# 查看前10部电影的ID
with open('./data/MovieTop250.txt', 'r', encoding='utf-8', errors='ignore') as f:
    movie_list = f.readlines()
    id_list = [item.split('\t')[0] for item in movie_list]

print(id_list[:10])


class MoviecommentSpider(scrapy.Spider):
    name = 'movieComment'
    allowed_domains = ['movie.douban.com']
    start_urls = ['http://movie.douban.com/']

    def start_requests(self):
        with open('./MovieTop250.txt', 'r', encoding='utf-8') as f:
            movie_list = f.readlines()
            id_list = [item.split('\t')[0] for item in movie_list]
        for movie_id in id_list:
            for page in range(0, 220, 20):
                meta = {'sentiment': '好评', 'ID': movie_id}
                url = "https://movie.douban.com/subject/{}/comments?start={}&limit=20&sort=new_score&status=P&percent_type=h".format(
                    movie_id, page)
                yield scrapy.Request(url=url, meta=meta)

                meta = {'sentiment': '差评', 'ID': movie_id}
                url = "https://movie.douban.com/subject/{}/comments?start={}&limit=20&sort=new_score&status=P&percent_type=l".format(
                    movie_id, page)
                yield scrapy.Request(url=url, meta=meta)

    def parse(self, response):
        try:
            subSelector = response.xpath('//div[@class="comment"]')
            for item in subSelector:
                # 评分 allstar30 rating, 40, 50, 20, 10
                star_class = item.xpath(
                    './h3/span[@class="comment-info"]/span[2]/@class').extract()[0].strip()
                p = re.compile(r'\d')
                star = p.findall(star_class)[0]
                # 评论内容
                review_content = item.xpath(
                    './p/span[@class="short"]/text()').extract()  # review是长度为1的列表
                review = " ".join(review_content)  # review赋值为字符串
                review = review.strip()
                # \xa0 是不间断空白符
                # \u3000 是全角的空白符
                for remarks in ('\t', '\n', '\xa0', '\ufeff', '\u200b', '\r'):
                    review = review.replace(remarks, '')
                if review:
                    with open('./data/ID_review_p11.csv', 'a+', newline='', encoding='utf-8-sig') as f:
                        csv_write = csv.writer(f)
                        data_row = [response.meta['ID'],
                                    response.meta['sentiment'], review, star]
                        csv_write.writerow(data_row)
        except:
            print("error")

