import requests

def fetch_proxies():
    # 用多个稳定的公开代理源，避免单点失败
    sources = [
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
    ]
    
    proxies = set()  # 用集合自动去重
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    for url in sources:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            text = resp.text.strip()
            for line in text.splitlines():
                line = line.strip()
                if ":" in line and len(line) > 7:  # 简单格式校验
                    proxies.add(line)
            print(f"✅ 从 {url} 成功爬取")
        except Exception as e:
            print(f"❌ 从 {url} 爬取失败: {e}")

    # 如果所有源都失败，写入兜底IP
    if not proxies:
        proxies = {
            "103.152.112.154:80",
            "190.61.44.14:8080",
            "103.149.162.194:80",
            "200.10.230.130:80"
        }
        print("⚠️ 所有源爬取失败，使用兜底列表")

    return sorted(proxies)

if __name__ == "__main__":
    proxy_list = fetch_proxies()
    with open("proxies.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(proxy_list))
    print(f"🎉 成功写入 {len(proxy_list)} 个代理到 proxies.txt")

