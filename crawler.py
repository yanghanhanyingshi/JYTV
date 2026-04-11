if __name__ == "__main__":
    BASE_URL = "http://zhibo.aisimu.cn/zhubo/"
    LOGIN_URL = "http://zhibo.aisimu.cn/index.php"
    # 临时硬编码用于调试
    USERNAME = "xyzvip"
    PASSWORD = "qq123456"
    
    # 注释掉环境变量读取
    # USERNAME = os.environ.get("CRAWLER_USERNAME", "")
    # PASSWORD = os.environ.get("CRAWLER_PASSWORD", "")

    if not USERNAME or not PASSWORD:
        print("错误：请设置环境变量 CRAWLER_USERNAME 和 CRAWLER_PASSWORD")
        exit(1)

    crawler = LiveCrawler(BASE_URL, LOGIN_URL, USERNAME, PASSWORD)
    data = crawler.run()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"\n采集完成，共 {len(data)} 条数据，时间：{crawler.get_beijing_time()}")
