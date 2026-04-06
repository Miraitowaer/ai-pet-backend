import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
import os
from kaoyan_scraper import KaoyanDataScraper

class BatchSpider:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        self.scraper = KaoyanDataScraper()

    def get_article_links(self, list_url: str, max_count: int = 20) -> list:
        print(f"🔍 正在解析研招网列表页: {list_url}")
        try:
            response = requests.get(list_url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"❌ 列表页访问失败，状态码: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            links = []
            
            # 【精准制导】：只找 class 为 news-list 的 ul 标签下的超链接
            news_list_ul = soup.find('ul', class_='news-list')
            
            if news_list_ul:
                # 寻找 ul 下所有的 a 标签
                for a_tag in news_list_ul.find_all('a', href=True):
                    href = a_tag['href']
                    full_url = urljoin(list_url, href)
                    
                    if full_url not in links:
                        links.append(full_url)
                        
                    if len(links) >= max_count:
                        break
            
            print(f"✅ 成功提取到 {len(links)} 个招生简章链接！")
            return links
            
        except Exception as e:
            print(f"❌ 解析列表页出错: {e}")
            return []

    def run_batch_task(self, list_url: str, output_dir: str = "./raw_data"):
        # 获取当前执行目录并创建 raw_data 文件夹
        current_dir = os.getcwd()
        save_path = os.path.join(current_dir, "raw_data")
        os.makedirs(save_path, exist_ok=True)
        
        target_urls = self.get_article_links(list_url, max_count=20)
        
        if not target_urls:
            print("没有找到可抓取的链接，任务结束。")
            return

        print(f"\n🚀 开始批量抓取详情页，文件将保存在: {save_path}")
        for index, url in enumerate(target_urls):
            print(f"\n[{index + 1}/{len(target_urls)}] 处理中...")
            self.scraper.fetch_and_save(url, output_dir=save_path)
            time.sleep(2) # 礼貌休眠
            
        print("\n🎉 20 所高校招生简章批量抓取任务全部完成！")

# ================= 启动批量爬虫 =================
if __name__ == "__main__":
    spider = BatchSpider()
    
    # 使用你刚刚找到的精准专栏入口
    entrance_list_url = "https://yz.chsi.com.cn/kyzx/zsjz/" 
    
    spider.run_batch_task(list_url=entrance_list_url)