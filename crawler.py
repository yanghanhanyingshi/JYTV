def run(self):
    print("===== 开始执行 =====")
    if not self.login():
        print("登录失败，终止执行")
        return []
    
    print("===== 获取分类 =====")
    categories = self.get_categories()
    if not categories:
        print("未获取到任何分类，尝试打印页面内容用于分析...")
        # 再次请求首页并打印更多内容
        resp = self.session.get(self.base_url)
        print("首页状态码:", resp.status_code)
        print("首页内容长度:", len(resp.text))
        print("首页前2000字符:\n", resp.text[:2000])
        return []
    
    all_data = []
    for cat in categories:
        channels = self.scrape_channels(cat)
        print(f"分类 [{cat['name']}] 获取到 {len(channels)} 个频道")
        for ch in channels:
            ch = self.test_speed(ch)
            all_data.append(ch)
        time.sleep(1)
    
    print(f"===== 采集完成，共 {len(all_data)} 条数据 =====")
    return all_data
