import requests
import re
import json
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
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://proxy.api.030101.xyz/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        # 尝试自动检测编码
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text
    except Exception as e:
        print(f"❌ 获取源失败: {e}")
        return None

def parse_auto(content):
    """
    自适应解析：
    1. 尝试 JSON 格式
    2. 尝试 M3U 格式
    3. 尝试每行 URL 格式
    4. 尝试带 #genre# 的分组格式
    返回列表 [(name, url, group)]
    """
    channels = []
    content = content.strip()
    
    # 1. JSON 尝试
    if content.startswith('{') or content.startswith('['):
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                # 假设常见结构: {"channels": [...]} 或 {"data": [...]}
                items = data.get('channels') or data.get('data') or data.get('list') or []
            elif isinstance(data, list):
                items = data
            else:
                items = []
            for item in items:
                if isinstance(item, dict):
                    name = item.get('name') or item.get('title') or item.get('channel') or '未知频道'
                    url = item.get('url') or item.get('link') or item.get('source') or ''
                    group = item.get('group') or item.get('category') or GROUP_NAME
                    if url:
                        channels.append((str(name), str(url), str(group)))
            if channels:
                print(f"✅ 通过 JSON 解析到 {len(channels)} 个频道")
                return channels
        except:
            pass

    # 2. M3U 格式
    if '#EXTM3U' in content or '#EXTINF' in content:
        lines = content.splitlines()
        current_name = None
        current_group = GROUP_NAME
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#EXTM3U"):
                continue
            if line.startswith("#EXTINF"):
                # 提取属性
                if ',' in line:
                    attr_part, name_part = line.split(',', 1)
                    name = name_part.strip()
                else:
                    attr_part = line
                    name = ""
                tvg_match = re.search(r'tvg-name="([^"]*)"', attr_part, re.I)
                if tvg_match:
                    name = tvg_match.group(1).strip()
                group_match = re.search(r'group-title="([^"]*)"', attr_part, re.I)
                if group_match:
                    current_group = group_match.group(1).strip()
                if not name:
                    name = "未命名频道"
                current_name = name
            elif line and not line.startswith("#"):
                if current_name:
                    channels.append((current_name, line, current_group))
                    current_name = None
                else:
                    channels.append(("未知频道", line, GROUP_NAME))
        if channels:
            print(f"✅ 通过 M3U 解析到 {len(channels)} 个频道")
            return channels

    # 3. 纯 URL 列表（每行一个 http/https 链接）
    url_pattern = re.compile(r'^(https?://[^\s]+)$', re.I)
    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if url_pattern.match(line):
            channels.append(("直播源", line, GROUP_NAME))
    if channels:
        print(f"✅ 通过 URL 列表解析到 {len(channels)} 个频道")
        return channels

    # 4. 带 #genre# 的分组格式 (用户示例格式)
    current_group = GROUP_NAME
    for line in lines:
        if ',' in line and '#genre#' in line:
            # 分组头
            parts = line.split(',')
            if len(parts) >= 2 and parts[1].strip() == '#genre#':
                current_group = parts[0].strip()
        elif ',' in line and not line.startswith('#'):
            # 格式: 时间,URL  或者 频道名,URL
            parts = line.split(',')
            if len(parts) >= 2:
                name = parts[0].strip()
                url = parts[1].strip()
                if url.startswith('http'):
                    channels.append((name, url, current_group))
    if channels:
        print(f"✅ 通过 #genre# 格式解析到 {len(channels)} 个频道")
        return channels

    print("⚠️ 无法识别任何格式，返回空列表")
    return []

def test_url_speed(url, timeout=SPEED_TEST_TIMEOUT):
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

    print("📄 源内容预览 (前1000字符):\n" + content[:1000] + "\n...")

    channels = parse_auto(content)
    if not channels:
        print("❌ 未能解析到任何频道，请检查预览内容并调整解析逻辑。")
        return

    channels = deduplicate_channels(channels)
    print(f"🧹 去重后频道数: {len(channels)}")

    update_time = get_beijing_time()
    print(f"⏰ 北京时间: {update_time}")

    # 测速过滤（可选关闭以加速）
    print("⏳ 开始测速（若频道过多可能较慢）...")
    valid_channels = []
    total = len(channels)
    for idx, (name, url, group) in enumerate(channels, 1):
        if idx % 10 == 0:
            print(f"  进度: {idx}/{total}")
        if test_url_speed(url):
            valid_channels.append((name, url, group))
    print(f"📊 有效频道数: {len(valid_channels)}")

    # 生成输出：按照用户要求的格式 "北京时间,URL"
    header = f"{GROUP_NAME},#genre#\n"
    lines = [f"{update_time},{url}" for _, url, _ in valid_channels]

    for filename in OUTPUT_FILES:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n".join(lines))
        print(f"💾 已生成文件: {filename}")

if __name__ == "__main__":
    main()
