import requests
from bs4 import BeautifulSoup
import markdownify
import re
import os

class KaoyanDataScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }

    def _clean_filename(self, title: str) -> str:
        clean_title = re.sub(r'[\\/:*?"<>|]', '_', title)
        return clean_title.strip() if clean_title else "未命名考研文档"

    def fetch_and_save(self, url: str, output_dir: str = ".") -> str:
        try:
            print(f"🚀 正在抓取: {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = response.apparent_encoding 
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 1. 精准提取网页标题 (适配研招网 <div class="title-box"><h2>)
                title_box = soup.find('div', class_='title-box')
                if title_box and title_box.find('h2'):
                    page_title = title_box.find('h2').text
                else:
                    page_title = soup.title.string if soup.title else "scraped_doc"
                
                safe_filename = self._clean_filename(page_title)
                file_path = os.path.join(output_dir, f"{safe_filename}.md")
                
                # 2. 精准提取核心正文区域 (适配研招网 <div class="detail">)
                article_div = soup.find('div', class_='detail')
                # 增加一个容错保底机制
                if not article_div:
                    article_div = soup.find('div', class_=re.compile(r'article|content-l', re.I))
                
                target_html = str(article_div) if article_div else str(soup.body)
                
                # 3. 转换为纯净的 Markdown
                md_text = markdownify.markdownify(target_html, heading_style="ATX", default_title=True)
                clean_md = "\n".join([line for line in md_text.splitlines() if line.strip() != ""])
                
                # 4. 直接保存到当下指定的目录中
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(clean_md)
                    
                print(f"✅ 抓取成功！已保存至: {file_path}")
                return file_path
            else:
                print(f"❌ 抓取失败，状态码: {response.status_code}")
                return ""
                
        except Exception as e:
            print(f"❌ 网络请求或解析出错: {e}")
            return ""