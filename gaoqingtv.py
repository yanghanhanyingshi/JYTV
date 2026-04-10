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
REQUEST_TIMEOUT = 15
SPEED_TEST_TIMEOUT = 3
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
# -------------------------

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    beijing_now = utc_now.astimezone(timezone(timedelta(hours=8)))
    return beijing_now.strftime("%Y%m%d %H:%M")

def fetch_content(url):
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
    解析 M3U 内容，提取频道名称和 URL。
    兼容多种写法：
      - #EXTINF:-1 tvg-name="CCTV1" group-title="央视",CCTV1
      - #EXTINF:-1 ,CCTV1
      - #EXTINF:-1,CCTV1
      - 无逗号的 #EXTINF 行，尝试从属性中提取 tvg-name
    """
    lines = content.splitlines()
    channels = []
    current_name = None
    current_group = GROUP_NAME  # 默认分组

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#EXTM3U"):
            continue

        if line.startswith("#EXTINF"):
            # 提取属性部分（逗号前的内容）
            if ',' in line:
                attr_part, name_part = line.split(',', 1)
                name = name_part.strip()
            else:
                attr_part = line
                name = ""

            # 尝试从属性中提取 tvg-name
            tvg_match = re.search(r'tvg-name="([^"]*)"', attr_part, re.I)
            if tvg_match:
                name = tvg_match.group(1).strip()

            # 尝试提取 group-title
            group_match = re.search(r'group-title="([^"]*)"', attr_part, re.I)
            if group_match:
                current_group = group_match.group(1).strip()

            # 如果名称仍为空，使用默认
            if not name:
                name = "未命名频道"

            current_name = name

        elif line and not line.startswith("#"):
            # 这是一个 URL 行
            if current_name is not None:
                channels.append((current_name, line, current_group))
                current_name = None
                # 注意：分组可能保持上一个有效 group，若没有 group 则用默认
            else:
                # 没有 EXTINF 直接出现的 URL，分配默认名称
                channels.append(("未知频道", line, GROUP_NAME))

    print(f"🔍 解析到原始频道数: {len(channels)}")
    return channels

def test_url_speed(url, timeout=SPEED_TEST_TIMEOUT):
    """通过 TCP 连接测试连通性，失败则降级为 HEAD 请求"""
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return False
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        try:
            headers = {"User-Agent": USER_AGENT}
            r = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            return r.status_code < 400
        except:
            return False

def deduplicate_channels(channels):
    """按 URL 去重，保留首次出现的名称与分组"""
    seen = set()
    unique = []
    for name, url, group in channels:
        if url not in seen:
            seen.add(url)
            unique.append((name, url, group))
    return unique

def main():
    print("🚀 开始执行直播源采集...")
    content = fetch_content(SOURCE_URL)
    if not content:
        print("❌ 未获取到内容，退出。")
        return

    # 打印前500字符供调试
    print("📄 源内容预览:\n" + content[:500] + "\n...")

    channels = parse_m3u(content)
    if not channels:
        print("⚠️ 未解析到任何频道，请检查 M3U 格式。")
        return

    channels = deduplicate_channels(channels)
    print(f"🧹 去重后频道数: {len(channels)}")

    update_time = get_beijing_time()
    print(f"⏰ 北京时间: {update_time}")

    # 测速过滤
    valid_channels = []
    total = len(channels)
    for idx, (name, url, group) in enumerate(channels, 1):
        print(f"🔍 测速 ({idx}/{total}): {name[:30]}... ", end="")
        if test_url_speed(url):
            print("✅ 可用")
            valid_channels.append((name, url, group))
        else:
            print("❌ 不可达")

    print(f"📊 有效频道数: {len(valid_channels)}")

    # 生成输出：每行 "北京时间,URL" （不包含频道名，因为用户示例格式如此）
    header = f"{GROUP_NAME},#genre#\n"
    lines = [f"{update_time},{url}" for _, url, _ in valid_channels]

    for filename in OUTPUT_FILES:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n".join(lines))
        print(f"💾 已生成文件: {filename}")

if __name__ == "__main__":
    main()
