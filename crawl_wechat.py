import requests
import pymongo
from urllib.parse import urlencode
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq

base_url = 'https://weixin.sogou.com/weixin?'

headers = {
    'Cookie': 'CXID=496CF669A42ED74FAEE9B5FE754F31CA; SUID=0DC806713565860A5BE418B600082E3E; SUV=00AC256E7A9F73CB5BEAD207DB0DD108; wuid=AAEsJ6/XIwAAAAqLFD16QgMAGwY=; GOTO=Af211047; usid=4bhhDdKZAx5ycTQ9; sw_uuid=1219840127; ssuid=9600502744; LSTMV=365%2C144; LCLKINT=2679; ad=7m9hSkllll2bixALlllllVedl$DllllltybwRyllllUlllllxllll5@@@@@@@@@@; IPLOC=CN4403; ABTEST=5|1553477938|v1; weixinIndexVisited=1; ppinf=5|1553477987|1554687587|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZTozOkpvY3xjcnQ6MTA6MTU1MzQ3Nzk4N3xyZWZuaWNrOjM6Sm9jfHVzZXJpZDo0NDpvOXQybHVPUnptaWdWcmhsYW5ZY1I3Wmh4cmtFQHdlaXhpbi5zb2h1LmNvbXw; pprdig=BW0xbFJa9K0mUl2EOzk-sKC_KGruMvxyF5L1ayqfsGOuKHrk2A8W6L28opTYTc879v5lNaWAfJjSv2gZz6N9G0KqlxWlgRidAmEU3I-HeWnr5Q5xt3xY6dKfiqIE0gN83qSoraY-1myXIvPv6bgUK2zvQulNA_mXWSX-FqIK3vI; sgid=21-39825017-AVyYMWNl0XdtV90UZFCjYKY; SMYUV=1553591399502726; UM_distinctid=169b9437453c0-02d8217d030474-b79183d-100200-169b9437455eaa; JSESSIONID=aaao1E4jR7K-r8yvHKLMw; PHPSESSID=i7vaaap0vmd34tpj2kk7bct5m3; SNUID=B3ADD8F18184057C17DCA87C81DB0EE7; ppmdig=1553598306000000f2d12ade0f38998f2b94cc419be87e25; sct=3',
    'Host': 'weixin.sogou.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
}

keyword = '美联储'
proxy = None

client = pymongo.MongoClient('localhost')
db = client['wechat']

def get_proxy():
    try:
        response = requests.get('http://localhost:5555/random')
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None

def get_index(keyword, page):
    query = {
        'query': keyword,
        'type': 2,
        'page': page
    }
    queries = urlencode(query)
    url = base_url + queries
    html = get_html(url)
    return html

def get_html(url, count=1):
    print('尝试次数:', count)
    global proxy
    if count >= 5:
        print('重试次数过多')
        return None
    try:
        if proxy:
            proxies = {
                'http': 'http://' + proxy
            }
            response = requests.get(url, allow_redirects=False,
                                    headers=headers, proxies=proxies)
        else:
            response = requests.get(url, allow_redirects=False, headers=headers)
        if response.status_code == 200:
            return response.text
        elif response.status_code == 302:
            proxy =get_proxy()
            if proxy:
                print('使用代理:', proxy)
                get_html(url)
            else:
                print('获取代理失败')
                return None
    except ConnectionError as e:
        print('连接错误', e.args)
        proxy = get_proxy()
        count += 1
        return get_html(url, count)

def parse_index(html):
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items()
    for item in items:
        yield item.attr('href')
def get_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None

def parse_detail(html):
    doc = pq(html)
    title = doc('.rich_media_title').text()
    content = doc('.rich_media_content ').text()
    date = doc('#publish_time').text()
    name = doc('.profile_nickname').text()
    wechat = doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
    return {
        'title': title,
        'content': content,
        'date': date,
        'name': name,
        'wechat': wechat
    }

def save_to_mongo(data):
    if db['articles'].update({'title': data['title']}, {'$set': data}, True):
        print('存储成功:', data['title'])
    else:
        print('存储失败:', data['title'])
def main():
    for page in range(1, 101):
        html = get_index(keyword=keyword, page=page)
        if html:
            urls = parse_index(html)
            for url in urls:
                html = get_detail(url)
                if html:
                    items = parse_detail(html)
                    if items:
                        save_to_mongo(items)

if __name__ == '__main__':
    main()
