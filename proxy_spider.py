import requests

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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        lines = []
        for item in data.get("data", []):
            ip = item.get("ip")
            port = item.get("port")
            if ip and port:
                lines.append(f"{ip}:{port}")

        with open("proxies.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"成功采集 {len(lines)} 个代理，已保存到 proxies.txt")

    except Exception as e:
        print("采集失败:", e)

if __name__ == "__main__":
    main()

