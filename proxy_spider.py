import requests
import os

def main():
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
        "page_size": 100,
        "page": 1
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.smartproxy.org/free-proxy-list"
    }

    proxies = []
    try:
        # 增加超时和重试
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        print(f"接口返回成功，数据量: {len(data.get('data', []))}")

        for item in data.get("data", []):
            ip = item.get("ip")
            port = item.get("port")
            if ip and port:
                proxies.append(f"{ip}:{port}")

    except Exception as e:
        print(f"接口请求失败: {e}")

    # 不管成功失败，都要写入文件，防止后续步骤报错
    with open("proxies.txt", "w", encoding="utf-8") as f:
        if proxies:
            f.write("\n".join(proxies))
            print(f"成功写入 {len(proxies)} 个代理到 proxies.txt")
        else:
            # 接口失败时，写入空内容，保证文件存在
            f.write("")
            print("未获取到有效代理，写入空文件，保证流程不中断")

if __name__ == "__main__":
    main()
