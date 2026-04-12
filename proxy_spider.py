import requests
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------- 配置 ----------------
TIMEOUT = 3
MAX_WORKERS = 30
OUTPUT_FILE = "proxies.txt"

# 普通文本代理源
TEXT_PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
]

# momoproxy 分页配置（从第0页爬到第9页，共10页）
MOMOPROXY_PAGE_START = 0
MOMOPROXY_PAGE_END = 9
MOMOPROXY_PAGE_SIZE = 50


def fetch_momoproxy():
    proxies = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
    }
    for page in range(MOMOPROXY_PAGE_START, MOMOPROXY_PAGE_END + 1):
        url = f"https://free.momoproxy.com/data?pageIndex={page}&pageSize={MOMOPROXY_PAGE_SIZE}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            for item in data.get("data", []):
                ip = item.get("ip")
                port = item.get("port")
                if ip and port:
                    proxies.add(f"{ip}:{port}")
            print(f"✅ momoproxy 第{page}页 抓取完成")
        except Exception as e:
            print(f"❌ momoproxy 第{page}页 失败: {e}")
    return proxies


def fetch_text_proxies():
    proxies = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36"
    }
    for url in TEXT_PROXY_SOURCES:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            for line in r.text.splitlines():
                line = line.strip()
                if ":" in line and 7 < len(line) < 30:
                    proxies.add(line)
            print(f"✅ 文本源抓取: {url}")
        except Exception as e:
            print(f"❌ 文本源失败: {url} {e}")
    return proxies


def is_alive(proxy):
    try:
        ip, port = proxy.split(":", 1)
        port = int(port)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(TIMEOUT)
            s.connect((ip, port))
        return proxy
    except:
        return None


def main():
    print("=" * 60)
    print("开始抓取代理…")

    # 抓取所有代理
    proxies = set()
    proxies.update(fetch_momoproxy())
    proxies.update(fetch_text_proxies())

    print(f"\n总共抓取代理数量：{len(proxies)}")

    # 测速过滤
    alive = []
    print("\n开始测速存活检测…")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tasks = [executor.submit(is_alive, p) for p in proxies]
        for t in as_completed(tasks):
            res = t.result()
            if res:
                alive.append(res)

    print(f"\n存活可用代理：{len(alive)} 个")

    # 写入文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(alive)))

    print("已保存到 proxies.txt")
    print("=" * 60)


if __name__ == "__main__":
    main()

