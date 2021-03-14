# 几个爬虫
* 微信爬虫：爬取关键字为“美联储”的文章  
    应用pyquery、request库，通过搜狗接口爬取微信文章。维护代理池跳过验证码来应对反爬措施。代理池脚本[地址](https://github.com/Python3WebSpider/ProxyPool)
* 头条爬虫：爬取关键字为“街拍图集”的图集  
    应用beautifulsoup、request库，处理Ajax的多进程爬虫。通过添加headers模拟浏览器应对反爬。
* 猫眼爬虫：爬取Top100电影信息  
    应用re、request库，使用正则表达式爬虫。
* quote_to_scrape爬虫：爬取名言示例    
    应用scrapy爬虫。
