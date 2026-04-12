import requests
import json

def main():
    # 完整请求参数，模拟真实浏览器
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.smartproxy.org/free-proxy-list",
        "Origin": "https://www.smartproxy.org",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    proxies = []
    try:
        # 增加重试和超时
        session = requests.Session()
        session.trust_env = False
        resp = session.get(url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        
        # 调试：打印完整响应，确认接口返回内容
        print("接口响应状态码:", resp.status_code)
        print("接口响应前500字符:", resp.text[:500])
        
        data = resp.json()
        if "data" in data and isinstance(data["data"], list):
            for item in data["data"]:
                ip = item.get("ip")
                port = item.get("port")
                if ip and port:
                    proxies.append(f"{ip}:{port}")
            print(f"成功解析到 {len(proxies)} 个代理IP")
        else:
            print("接口返回格式异常，未找到data字段")

    except Exception as e:
        print(f"请求或解析失败: {str(e)}")

    # 写入文件，强制覆盖
    with open("proxies.txt", "w", encoding="utf-8") as f:
        if proxies:
            f.write("\n".join(proxies))
            print(f"已写入 {len(proxies)} 个代理到 proxies.txt")
        else:
            # 兜底：如果抓不到数据，写入备用代理列表，避免空文件
            backup_proxies = [
                "103.152.112.154:80",
                "190.61.44.14:8080",
                "103.149.162.194:80",
                "200.10.230.130:80"
            ]
            f.write("\n".join(backup_proxies))
            print("⚠️ 未抓到新代理，写入备用列表，避免文件为空")

if __name__ == "__main__":
    main()

