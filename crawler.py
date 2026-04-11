import json
import time
import datetime
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# 时区：北京时间
BEIJING_TZ = datetime.timezone(datetime.timedelta(hours=8))


def login(session, login_url, username, password):
    data = {
        "username": username,
        "password": password,
        "action": "login"
    }
    try:
        resp = session.post(login_url, data=data, timeout=15)
        print(f"登录状态码: {resp.status_code}")
        return resp.status_code == 200
    except Exception as e:
        print(f"登录失败: {e}")
        return False


def speed_test(url, timeout=5):
    try:
        st = time.time()
        # 用 HEAD 请求测速，减少流量
        requests.head(url, timeout=timeout, allow_redirects=True)
        return round((time.time() - st) * 1000, 2)
    except:
        return None


def crawl():
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    print("=== 开始登录 ===")
    if not login(s, cfg["login_url"], cfg["username"], cfg["password"]):
        print("登录失败，退出")
        return

    print("=== 开始抓取首页 ===")
    resp = s.get(cfg["base_url"], timeout=15)
    print(f"首页状态码: {resp.status_code}")
    print(f"首页内容长度: {len(resp.text)}")

    soup = BeautifulSoup(resp.text, "lxml")

    # 修复1：先打印所有链接，看看网站实际结构
    print("\n=== 首页所有链接预览 ===")
    all_links = soup.find_all("a", href=True)
    for link in all_links[:20]:  # 只打印前20条，避免刷屏
        print(f"- {link.get_text(strip=True)} -> {link['href']}")

    # 修复2：适配常见直播站的分类结构
    categories = []
    # 优先找包含"list"、"type"、"class"、"category"的链接
    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(strip=True)
        if not text or not href:
            continue
        # 过滤掉非分类链接（比如登录、注册、外部链接）
        if any(kw in href for kw in ["login", "register", "http://", "https://", "#"]):
            continue
        # 只保留站内的、可能是分类的链接
        cat_url = urljoin(cfg["base_url"], href)
        categories.append({
            "name": text,
            "url": cat_url
        })

    print(f"\n=== 找到 {len(categories)} 个分类 ===")

    result = {
        "updated_at_beijing": datetime.datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "update_timestamp": int(time.time()),
        "categories": []
    }

    # 修复3：适配常见的直播源链接（m3u8/rtmp/ts）
    for cat in categories:
        print(f"\n=== 正在抓取分类: {cat['name']} ===")
        try:
            r = s.get(cat["url"], timeout=15)
            soup2 = BeautifulSoup(r.text, "lxml")
            channels = []

            # 找所有包含直播源的链接
            for a in soup2.find_all("a", href=True):
                href = a["href"]
                name = a.get_text(strip=True)
                if not name or not href:
                    continue
                # 只保留常见直播协议的链接
                if any(kw in href for kw in [".m3u8", ".ts", "rtmp://", "http://", "https://"]):
                    stream_url = urljoin(cat["url"], href)
                    print(f"找到频道: {name} -> {stream_url}")
                    ms = speed_test(stream_url)
                    channels.append({
                        "name": name,
                        "url": stream_url,
                        "speed_ms": ms
                    })

            if channels:
                result["categories"].append({
                    "category": cat["name"],
                    "channels": channels
                })
                print(f"分类 {cat['name']} 找到 {len(channels)} 个频道")
            else:
                print(f"分类 {cat['name']} 未找到任何频道")

        except Exception as e:
            print(f"分类 {cat['name']} 抓取失败: {e}")
            continue

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n=== 抓取完成 ===")
    print(f"更新时间: {result['updated_at_beijing']}")
    print(f"有效分类数: {len(result['categories'])}")
    total_channels = sum(len(c["channels"]) for c in result["categories"])
    print(f"总频道数: {total_channels}")


if __name__ == "__main__":
    crawl()

