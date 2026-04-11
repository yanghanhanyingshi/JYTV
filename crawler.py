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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': base_url
        })

    def get_beijing_time(self):
        beijing_tz = pytz.timezone('Asia/Shanghai')
        return datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

    def login(self):
        """登录，并尝试提取隐藏字段"""
        print(f"[{self.get_beijing_time()}] 正在访问登录页...")
        try:
            # 先 GET 登录页，获取 Cookie 和可能的隐藏字段
            login_page = self.session.get(self.login_url, timeout=10)
            soup = BeautifulSoup(login_page.text, 'html.parser')
            
            # 构造登录 payload
            payload = {
                'username': self.username,
                'password': self.password
            }
            
            # 查找所有隐藏的 input 字段并加入 payload
            hidden_inputs = soup.find_all('input', type='hidden')
            for inp in hidden_inputs:
                name = inp.get('name')
                value = inp.get('value', '')
                if name:
                    payload[name] = value
                    print(f"  发现隐藏字段: {name} = {value[:20]}...")
            
            print(f"[{self.get_beijing_time()}] 正在提交登录...")
            response = self.session.post(
                self.login_url, 
                data=payload, 
                allow_redirects=True,
                timeout=10
            )
            
            # 检查是否登录成功
            if self.username in response.text or '退出' in response.text or '会员中心' in response.text:
                print(f"[{self.get_beijing_time()}] ✅ 登录成功！")
                return True
            else:
                print(f"[{self.get_beijing_time()}] ❌ 登录失败，页面片段：")
                print(response.text[:500])
                return False
                
        except Exception as e:
            print(f"[{self.get_beijing_time()}] 登录异常: {e}")
            return False

    def get_categories(self):
        """获取分类列表，并打印调试信息"""
        print(f"[{self.get_beijing_time()}] 正在获取分类页面: {self.base_url}")
        categories = []
        try:
            response = self.session.get(self.base_url, timeout=10)
            print(f"  状态码: {response.status_code}")
            print(f"  页面长度: {len(response.text)}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 打印页面标题和前800字符，帮助调试
            title = soup.title.string if soup.title else "无标题"
            print(f"  页面标题: {title}")
            print(f"  页面内容片段:\n{response.text[:800]}\n")
            
            # 尝试多种常见的选择器查找分类链接
            # 你可以根据打印出的 HTML 片段调整下面的选择器
            possible_selectors = [
                'a[href*="category"]',
                'a[href*="type"]',
                '.nav a',
                '.menu a',
                '.category a',
                'ul li a',
            ]
            
            category_links = []
            for selector in possible_selectors:
                links = soup.select(selector)
                if links:
                    print(f"  选择器 '{selector}' 找到 {len(links)} 个链接")
                    category_links.extend(links)
                    break  # 如果找到就停止尝试
            
            if not category_links:
                # 如果 CSS 选择器都没找到，用正则找所有包含 zhubo 的链接
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link['href']
                    if re.search(r'(zhubo|category|type|list)', href):
                        category_links.append(link)
            
            # 去重并构造分类数据
            seen = set()
            for link in category_links[:10]:  # 最多取10个，避免太多
                name = link.text.strip()
                href = link['href']
                if not name or href in seen:
                    continue
                seen.add(href)
                url = urljoin(self.base_url, href)
                categories.append({'name': name, 'url': url})
                print(f"  找到分类: {name} -> {url}")
            
            print(f"[{self.get_beijing_time()}] 共获取到 {len(categories)} 个分类。")
            return categories
            
        except Exception as e:
            print(f"[{self.get_beijing_time()}] 获取分类异常: {e}")
            return []

    def scrape_channels(self, category):
        """采集单个分类下的频道"""
        print(f"[{self.get_beijing_time()}] 正在采集分类: {category['name']}")
        channels = []
        try:
            response = self.session.get(category['url'], timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # TODO: 根据实际页面结构调整选择器
            # 打印分类页片段供调试
            print(f"  分类页内容片段:\n{response.text[:500]}")
            
            # 示例：查找所有可能的频道链接
            items = soup.find_all('a', href=re.compile(r'(m3u8|live|stream|play)'))
            for item in items[:5]:
                name = item.text.strip()
                url = item['href']
                if name:
                    channels.append({
                        'category': category['name'],
                        'channel_name': name,
                        'stream_url': url,
                        'speed': None,
                        'update_time': self.get_beijing_time()
                    })
            return channels
        except Exception as e:
            print(f"  采集出错: {e}")
            return []

    def test_speed(self, channel):
        """测速"""
        try:
            start = time.time()
            resp = self.session.get(channel['stream_url'], stream=True, timeout=5)
            resp.raise_for_status()
            elapsed = (time.time() - start) * 1000
            channel['speed'] = f"{elapsed:.2f} ms"
        except Exception as e:
            channel['speed'] = f"失败: {str(e)[:30]}"
        return channel

    def run(self):
        """主流程"""
        print(f"\n{'='*40}")
        print(f"[{self.get_beijing_time()}] 开始执行采集任务")
        print(f"{'='*40}\n")
        
        if not self.login():
            print("登录失败，任务终止")
            return []  # 返回空列表而不是 None
        
        categories = self.get_categories()
        if not categories:
            print("未获取到任何分类，请根据上面的页面片段调整选择器")
            return []  # 返回空列表
        
        all_data = []
        for cat in categories:
            channels = self.scrape_channels(cat)
            print(f"  分类 [{cat['name']}] 获取到 {len(channels)} 个频道")
            for ch in channels:
                ch = self.test_speed(ch)
                all_data.append(ch)
            time.sleep(1)
        
        print(f"\n{'='*40}")
        print(f"[{self.get_beijing_time()}] 采集完成，共 {len(all_data)} 条数据")
        print(f"{'='*40}\n")
        return all_data


if __name__ == "__main__":
    BASE_URL = "http://zhibo.aisimu.cn/zhubo/"
    LOGIN_URL = "http://zhibo.aisimu.cn/index.php"
    
    # 临时硬编码用于调试（之后改回 Secrets）
    USERNAME = "xyzvip"
    PASSWORD = "qq123456"
    
    crawler = LiveCrawler(BASE_URL, LOGIN_URL, USERNAME, PASSWORD)
    data = crawler.run()
    
    # 输出 JSON 结果
    if data:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print("[]")  # 输出空数组，避免后续处理出错
    
    print(f"\n最终执行时间：{crawler.get_beijing_time()}")
