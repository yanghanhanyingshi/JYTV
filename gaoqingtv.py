import requests
import re
import time
import socket
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

# ---------- 配置 ----------
SOURCE_URL = "https://proxy.api.030101.xyz/linglu.814555752.workers.dev/"
OUTPUT_FILES = ["gaoqingtv.txt", "gaoqing.txt"]
GROUP_NAME = "灵鹿整合"
REQUEST_TIMEOUT = 10
SPEED_TEST_TIMEOUT = 3          # 单个源测速超时（秒）
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
# -------------------------

def get_beijing_time():
    """返回北京时间字符串，格式：YYYYMMDD HH:MM"""
    utc_now = datetime.now(timezone.utc)
    beijing_now = utc_now.astimezone(timezone(timedelta(hours=8)))
    return beijing_now.strftime("%Y%m%d %H:%M")

def fetch_content(url):
    """获取源地址内容"""
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        print(f"❌ 获取源失败: {e}")
        return None

def parse_m3u(content):
    """
    解析 M3U 格式，提取频道名和 URL。
    返回列表，每项为 (channel_name, url)
    """
    lines = content.splitlines()
    channels = []
    current_name = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#EXTM3U"):
            continue
        if line.startswith("#EXTINF"):
            # 尝试提取频道名（逗号后面的部分）
            if ',' in line:
                current_name = line.split(',', 1)[1].strip()
            else:
                # 若无逗号，取整个属性部分
                current_name = line.replace("#EXTINF:", "").strip()
        elif line and not line.startswith("#"):
            if current_name is not None:
                channels.append((current_name, line))
                current_name = None
            else:
                # 没有 EXTINF 信息的直接 URL，给个默认名称
                channels.append(("未知频道", line))
    return channels

def test_url_speed(url, timeout=SPEED_TEST_TIMEOUT):
    """
    简单测速：尝试建立 TCP 连接（80/443端口）或发送 HEAD 请求。
    返回是否可达。
    """
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        # 如果 socket 测试失败，尝试 requests 短请求
        try:
            headers = {"User-Agent": USER_AGENT}
            r = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            return r.status_code < 400
        except:
            return False

def deduplicate_channels(channels):
    """按 URL 去重，保留首次出现的频道名"""
    seen = set()
    unique = []
    for name, url in channels:
        if url not in seen:
            seen.add(url)
            unique.append((name, url))
    return unique

def main():
    print("🚀 开始执行直播源采集...")
    content = fetch_content(SOURCE_URL)
    if not content:
        print("❌ 未获取到内容，退出。")
        return

    # 解析频道列表
    channels = parse_m3u(content)
    print(f"📡 解析到 {len(channels)} 个原始频道。")

    # 去重
    channels = deduplicate_channels(channels)
    print(f"🧹 去重后剩余 {len(channels)} 个频道。")

    # 获取北京时间
    update_time = get_beijing_time()
    print(f"⏰ 当前北京时间：{update_time}")

    # 测速并过滤不可达源
    valid_channels = []
    total = len(channels)
    for idx, (name, url) in enumerate(channels, 1):
        print(f"🔍 测速 ({idx}/{total}): {name[:20]}... ", end="")
        if test_url_speed(url):
            print("✅ 可用")
            valid_channels.append((name, url))
        else:
            print("❌ 超时/不可达，跳过")
    print(f"📊 最终有效频道数：{len(valid_channels)}")

    # 生成输出内容
    header = f"{GROUP_NAME},#genre#\n"
    lines = [f"{update_time},{url}" for _, url in valid_channels]

    # 写入两个文件（内容相同，可根据需要修改分类逻辑）
    for filename in OUTPUT_FILES:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n".join(lines))
        print(f"💾 已生成文件：{filename}")

if __name__ == "__main__":
    main()
