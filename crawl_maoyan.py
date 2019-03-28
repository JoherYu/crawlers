import json
from multiprocessing.pool import Pool

import requests
from requests.exceptions import RequestException
import re

base_url = 'https://maoyan.com/board/4?offset='

def get_page(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return None

def parse_page(html):
    pattern = re.compile('<dd>.*?board-index-.*?">(\d+)</i>.*?title="(.*?)"'
                         '.*?board-img.*?src="(.*?)".*?class="movie-item-info"'
                         '.*?star">(.*?)</p>.*?time">(.*?)</p>.*?integer"'
                         '>(.*?)</i>.*?tion">(.*?)</i>.*?</dd>', re.S)
    items = re.findall(pattern, html)
    for item in items:
        yield {
            'index': item[0],
            'title': item[1],
            'image': item[2],
            'stars': item[3].strip()[3:],
            'time': item[4].strip()[5:],
            'score': item[5] + item[6]
        }

def write(data):
    with open('maoyan.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')

def main(offset):
    url = base_url + str(offset)
    html = get_page(url)
    if html:
        datas = parse_page(html)
        for data in datas:
            write(data)

if __name__ == '__main__':
    pool = Pool()
    pool.map(main, [x*10 for x in range(10)])
    pool.close()
    pool.join()