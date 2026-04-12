import requests
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------- 核心配置 -------------------
TIMEOUT = 2
MAX_WORKERS = 50
OUTPUT_FILE = "proxies.txt"
MAX_DELAY_MS = 300  # 只保留300ms以内

# momoproxy 分页
MOMOPROXY_PAGE_START = 0
MOMOPROXY_PAGE_END = 12
MOMOPROXY_PAGE_SIZE = 50

# smartproxy 分页
SMARTPROXY_PAGE_START = 1
SMARTPROXY_PAGE_END = 5
SMARTPROXY_PAGE_SIZE = 50

# ==================================================

def fetch_momoproxy():
    proxies = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
    }
    for page in range(MOMOPROXY_PAGE_START, MOMOPROXY_PAGE_END + 1):
        url = f"https://free.momoproxy.com/data?pageIndex={page}&pageSize={MOMOPROXY_PAGE_SIZE}"
        try:
            r = requests.get(url, headers=headers, timeout=8)
            data = r.json()
            for item in data.get("data", []):
                ip = item.get("ip")
                port = item.get("port")
                if ip and port:
                    proxies.add(f"{ip}:{port}")
            print(f"✅ momoproxy 第{page}页 完成")
        except Exception:
            continue
    return proxies

def fetch_smartproxy():
    proxies = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://www.smartproxy.org/free-proxy-list"
    }
    for page in range(SMARTPROXY_PAGE_START, SMARTPROXY_PAGE_END + 1):
        url = "https://www.smartproxy.org/web_v1/free-proxy/list"
        params = {
            "country_code": "",
            "protocol": "",
            "port": "",
            "uptime": "",
            "anonymity": "",
            "speed": "",
            "google_passed": "",
            "asn": "",
            "page_size": SMARTPROXY_PAGE_SIZE,
            "page": page
        }
        try:
            r = requests.get(url, params=params, headers=headers, timeout=8)
            data = r.json()
            items = data.get("data", {}).get("list", [])
            for item in items:
                ip = item.get("ip")
                port = item.get("port")
                if ip and port:
                    proxies.add(f"{ip}:{port}")
            print(f"✅ smartproxy 第{page}页 完成")
        except Exception:
            continue
    return proxies

def check_delay(proxy):
    try:
        ip, port = proxy.split(":", 1)
        port = int(port)
        st = time.perf_counter()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((ip, port))
        ms = (time.perf_counter() - st) * 1000
        if ms <= MAX_DELAY_MS:
            return proxy
    except:
        return None

def main():
    print("=" * 60)
    print("🚀 开始多源采集代理")

    proxy_set = set()
    proxy_set.update(fetch_momoproxy())
    proxy_set.update(fetch_smartproxy())

    print(f"\n📦 原始去重后总数：{len(proxy_set)}")
    print(f"\n⏱ 筛选延迟 ≤ {MAX_DELAY_MS}ms")

    good_proxies = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tasks = [executor.submit(check_delay, p) for p in proxy_set]
        for t in as_completed(tasks):
            res = t.result()
            if res:
                good_proxies.append(res)

    print(f"\n✅ 最终可用低延迟代理：{len(good_proxies)} 个")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(good_proxies)))
    print("💾 已保存到 proxies.txt")
    print("=" * 60)

if __name__ == "__main__":
    main()

