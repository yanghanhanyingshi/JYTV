import requests
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------- 配置项 ----------------
TIMEOUT = 3  # 测速超时（秒）
MAX_WORKERS = 30  # 并发测速数
OUTPUT_FILE = "proxies.txt"

# 多个稳定的公开代理源
SOURCES = [
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"
]

def fetch_proxies():
    """从多个源爬取代理并去重"""
    proxies = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    for url in SOURCES:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            for line in resp.text.splitlines():
                line = line.strip()
                if ":" in line and len(line) > 7:
                    proxies.add(line)
            print(f"✅ 爬取成功: {url}")
        except Exception as e:
            print(f"❌ 爬取失败: {url} ({e})")

    # 兜底列表
    if not proxies:
        proxies = {
            "103.152.112.154:80",
            "190.61.44.14:8080",
            "103.149.162.194:80",
            "200.10.230.130:80"
        }
        print("⚠️ 所有源爬取失败，使用兜底列表")

    return list(proxies)

def is_proxy_alive(proxy):
    """测试单个代理是否存活"""
    try:
        ip, port = proxy.split(":")
        port = int(port)
        # 建立TCP连接测试（比HTTP测试更快）
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((ip, port))
        return proxy
    except Exception:
        return None

def main():
    print("=" * 50)
    print("🚀 开始爬取代理...")
    raw_proxies = fetch_proxies()
    print(f"📦 共爬取到 {len(raw_proxies)} 个代理")

    print("\n🔍 开始测速过滤（存活代理测试）...")
    alive_proxies = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(is_proxy_alive, p) for p in raw_proxies]
        for future in as_completed(futures):
            result = future.result()
            if result:
                alive_proxies.append(result)

    print(f"✅ 测速完成，存活代理: {len(alive_proxies)} 个")

    # 写入文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(alive_proxies)))

    print(f"📝 已保存存活代理到 {OUTPUT_FILE}")
    print("=" * 50)

if __name__ == "__main__":
    main()

