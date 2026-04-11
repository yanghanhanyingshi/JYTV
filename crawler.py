# crawler.py
import requests
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import pytz
import os
import json

class LiveCrawler:
    def __init__(self, base_url, login_url, username, password):
        self.base_url = base_url
        self.login_url = login_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_beijing_time(self):
        beijing_tz = pytz.timezone('Asia/Shanghai')
        return datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

    def login(self):
        print(f"[{self.get_beijing_time()}] 正在登录...")
        login_payload = {
            'username': self.username,
            'password': self.password
            # 如果网站有 csrf token，需要先 GET 登录页提取并加入
        }
        try:
            response = self.session.post(self.login_url, data=login_payload, allow_redirects=True, timeout=10)
            response.raise_for_status()
            if self.username in response.text or "登录成功" in response.text:
                print(f"[{self.get_beijing_time()}] 登录成功！")
                return True
            else:
                print(f"[{self.get_beijing_time()}] 登录失败，请检查账号或页面结构。")
                return False
        except Exception as e:
            print(f"[{self.get_beijing_time()}] 登录异常: {e}")
            return False

    def get_categories(self):
        print(f"[{self.get_beijing_time()}] 正在获取分类列表...")
        categories = []
        try:
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            # TODO: 根据实际页面结构调整选择器
            category_elements = soup.find_all('a', href=re.compile(r'/zhubo/.*'))
            for elem in category_elements[:5]:  # 测试时限制数量
                name = elem.text.strip()
                url = urljoin(self.base_url, elem['href'])
                if name:
                    categories.append({'name': name, 'url': url})
            print(f"[{self.get_beijing_time()}] 获取到 {len(categories)} 个分类。")
            return categories
        except Exception as e:
            print(f"[{self.get_beijing_time()}] 获取分类失败: {e}")
            return []

    def scrape_channels(self, category):
        print(f"[{self.get_beijing_time()}] 正在采集分类: {category['name']}")
        channels = []
        try:
            response = self.session.get(category['url'], timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            # TODO: 根据实际页面结构调整选择器
            items = soup.find_all('div', class_='channel-item')
            for item in items[:3]:  # 测试时限制
                name_tag = item.find('a')
                if name_tag:
                    channel_name = name_tag.text.strip()
                    stream_url = name_tag.get('href')
                    channels.append({
                        'category': category['name'],
                        'channel_name': channel_name,
                        'stream_url': stream_url,
                        'speed': None,
                        'update_time': self.get_beijing_time()
                    })
            return channels
        except Exception as e:
            print(f"[{self.get_beijing_time()}] 采集出错: {e}")
            return []

    def test_speed(self, channel):
        try:
            start = time.time()
            resp = self.session.get(channel['stream_url'], stream=True, timeout=5)
            resp.raise_for_status()
            elapsed = (time.time() - start) * 1000
            channel['speed'] = f"{elapsed:.2f} ms"
        except Exception as e:
            channel['speed'] = f"失败: {e}"
        return channel

    def run(self):
        if not self.login():
            return []
        categories = self.get_categories()
        all_data = []
        for cat in categories:
            channels = self.scrape_channels(cat)
            for ch in channels:
                ch = self.test_speed(ch)
                all_data.append(ch)
            time.sleep(1)
        return all_data

if __name__ == "__main__":
    BASE_URL = "http://zhibo.aisimu.cn/zhubo/"
    LOGIN_URL = "http://zhibo.aisimu.cn/index.php"
    USERNAME = os.environ.get("CRAWLER_USERNAME", "")
    PASSWORD = os.environ.get("CRAWLER_PASSWORD", "")

    if not USERNAME or not PASSWORD:
        print("错误：请设置环境变量 CRAWLER_USERNAME 和 CRAWLER_PASSWORD")
        exit(1)

    crawler = LiveCrawler(BASE_URL, LOGIN_URL, USERNAME, PASSWORD)
    data = crawler.run()

    # 输出 JSON 结果，方便 Actions 日志查看或后续处理
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"\n采集完成，共 {len(data)} 条数据，时间：{crawler.get_beijing_time()}")
