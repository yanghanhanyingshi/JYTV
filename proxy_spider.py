import requests
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------- 核心配置 ----------------
TIMEOUT = 2          # 超时时间(秒)
MAX_WORKERS = 80     # 并发数
OUTPUT_FILE = "proxies.txt"
MAX_DELAY_MS = 300   # 只保留延迟300ms以内

# 稳定的 GitHub 公开代理源（在 Actions 里几乎不会被墙）
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt"
]

def fetch_proxies():
    """从 GitHub 源爬取代理，自动去重"""
    proxies = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }
    for url in PROXY_SOURCES:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            for line in resp.text.splitlines():
                line = line.strip()
                if ":" in line and len(line) > 7 and len(line) < 30:
                    proxies.add(line)
            print(f"✅ 爬取成功: {url}")
        except Exception as e:
            print(f"❌ 爬取失败: {url} ({e})")
    
    # 兜底：如果所有源都失败，写入备用IP
    if not proxies:
        proxies = {
            "103.152.112.154:80",
            "190.61.44.14:8080",
            "103.149.162.194:80",
            "200.10.230.130:80"
        }
        print("⚠️ 所有源爬取失败，使用备用IP")
    return list(proxies)

def check_proxy(proxy):
    """测试代理延迟，只保留300ms以内的"""
    try:
        ip, port = proxy.split(":", 1)
        port = int(port)
        start = time.perf_counter()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((ip, port))
        delay_ms = (time.perf_counter() - start) * 1000
        if delay_ms <= MAX_DELAY_MS:
            return proxy
    except Exception:
        return None

def main():
    print("=" * 60)
    print("🚀 开始多源爬取代理...")
    raw_proxies = fetch_proxies()
    print(f"📦 共爬取到 {len(raw_proxies)} 个代理")

    print(f"\n⏱️ 筛选延迟 ≤ {MAX_DELAY_MS}ms 的代理...")
    alive_proxies = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(check_proxy, p) for p in raw_proxies]
        for future in as_completed(futures):
            result = future.result()
            if result:
                alive_proxies.append(result)

    print(f"✅ 筛选完成，有效低延迟代理: {len(alive_proxies)} 个")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(alive_proxies)))
    print(f"💾 已保存到 {OUTPUT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    main()

