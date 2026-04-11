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
        return resp.status_code == 200
    except:
        return False


def speed_test(url, timeout=5):
    try:
        st = time.time()
        requests.head(url, timeout=timeout, allow_redirects=True)
        return round((time.time() - st) * 1000, 2)
    except:
        return None


def crawl():
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    })

    print("登录中...")
    if not login(s, cfg["login_url"], cfg["username"], cfg["password"]):
        print("登录失败")
        return

    print("抓取分类与直播源...")
    resp = s.get(cfg["base_url"], timeout=15)
    soup = BeautifulSoup(resp.text, "lxml")

    categories = []
    # 根据常见结构采集分类 + 链接
    for cat_item in soup.select(".category,.menu a,.nav a"):
        cat_name = cat_item.get_text(strip=True)
        cat_href = cat_item.get("href")
        if not cat_name or not cat_href:
            continue
        cat_url = urljoin(cfg["base_url"], cat_href)
        categories.append({
            "name": cat_name,
            "url": cat_url
        })

    result = {
        "updated_at_beijing": datetime.datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "update_timestamp": int(time.time()),
        "categories": []
    }

    # 遍历每个分类抓取频道
    for cat in categories:
        try:
            r = s.get(cat["url"], timeout=15)
            soup2 = BeautifulSoup(r.text, "lxml")
            channels = []
            for a in soup2.select("a[href*=live],a[href*=m3u8],a[href*=rtmp]"):
                name = a.get_text(strip=True)
                href = a.get("href")
                if not name or not href:
                    continue
                stream_url = urljoin(cat["url"], href)
                ms = speed_test(stream_url)
                channels.append({
                    "name": name,
                    "url": stream_url,
                    "speed_ms": ms
                })
            result["categories"].append({
                "category": cat["name"],
                "channels": channels
            })
        except Exception as e:
            print(f"{cat['name']} 抓取失败: {e}")
            continue

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"更新完成：{result['updated_at_beijing']}")
    print(f"共 {len(result['categories'])} 个分类")


if __name__ == "__main__":
    crawl()

