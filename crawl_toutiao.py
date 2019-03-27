import os
from hashlib import md5
import pymongo
import re
import json
import requests
from urllib.parse import urlencode
from multiprocessing import Pool
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
}

client = pymongo.MongoClient('localhost')
db = client['toutiao']

def get_index(offset, keyword):
    data = {
        'aid': 24,
        'app_name': 'web_search',
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': 20,
        'en_qc': 1,
        'cur_tab': 1,
        'from': 'search_tab',
        'pd': 'synthesis',
        'timestamp': 1553651194243
    }
    url = 'https://www.toutiao.com/api/search/content/?' + urlencode(data)

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except RequestException:
        print('索引接口请求失败')
        return None

def parse_index(html):
    data = json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            if item.get('article_url'):
                yield item.get('article_url')

def get_detail(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except RequestException:
        print('索引接口请求失败', url)
        return None

def parse_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    result = soup.select('title')
    title = result[0].get_text() if result else ''
    images_pattern = re.compile('gallery: JSON.parse\("(.*)"\)', re.S)
    result = re.search(images_pattern, html)
    if result:
        data = json.loads(result.group(1).replace('\\', ''))
        if data and 'sub_images' in data.keys():
            images = [image.get('url') for image in data.get('sub_images')]
            for image in images:
                download_images(image)
            return {
                'title': title,
                'url': url,
                'images': images
            }

def save_to_mongo(data):
    if db['jiepai'].insert(data):
        print('存储成功', data['title'])
        return True
    return None

def download_images(url):
    print('正在下载图片:', url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_images(response.content)
        else:
            return None
    except RequestException:
        print('图片请求失败', url)
        return None

def save_images(content):
    file_path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)

def main(i):
    html = get_index(i*20, '街拍图集')
    if html:
        urls = parse_index(html)
        for url in urls:
            html = get_detail(url)
            if html:
                data = parse_detail(html, url)
                if data:
                    save_to_mongo(data)


if __name__ == '__main__':
    pool =Pool()
    group = (i for i in range(20))
    pool.map(main, group)
    pool.close()
    pool.join()