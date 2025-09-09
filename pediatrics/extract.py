from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import re
import csv
import time

BASE_URL = "https://pediatrics.or.kr"

def scrape_data(pages_to_scrape):
    """대한소아청소년과학회 육아 정보 페이지에서 데이터 스크래핑"""
    all_data = []
    
    base_url = f"{BASE_URL}/bbs?code=infantcare&category=A&page="

    for page_num in range(1, pages_to_scrape + 1):
        page_url = f"{base_url}{page_num}"
        print("page_url >>>>>>", page_url)

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
                }
            response = requests.get(page_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            article_items = soup.find_all('dl', class_='infoItem')
            print(f"{page_num}페이지: 총 {len(article_items)}개의 게시글 항목 발견")

            if article_items is None:
                print(f"{page_num}페이지에 게시글 항목이 없습니다. 다음 페이지로 넘어갑니다.")
                continue

            for item in article_items:
                link_tag = item.select_one('dt a')
                relative_link = link_tag.get('href')
                full_link = urljoin(BASE_URL, relative_link)

                title_tag = item.select_one('dt a strong')
                title = title_tag.get_text(strip=True) if title_tag else "No Title"
                
                content = scrape_article_content(full_link, headers)
                all_data.append({'site': "대한소아청소년과학회", 'title': title, 'content': content, 'full_link': full_link, 'main_url': BASE_URL, 'relative_link': relative_link})
                time.sleep(5)

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while scraping {page_url}: {e}")
            break
        
    return all_data


def scrape_article_content(link, headers):
    """개별 기사 페이지에서 내용 스크래핑"""
    try:
        response = requests.get(link, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')

        content_title = soup.find('span', class_='tit').get_text(strip=True)

        bbs_con = soup.select_one(".bbsCon")
        content = bbs_con.get_text(separator=" ", strip=True)
        
        # 1. 불필요한 공백을 하나로 줄입니다.
        content = re.sub(r'\s+', ' ', content).strip()

        # 2. 괄호 주변의 공백을 제거합니다. 예: "( 내용 )" -> "(내용)"
        content = re.sub(r'\s*(\(|\))\s*', r'\1', content)

        # 3. 콤마(,)와 마침표(.) 주변의 공백을 제거합니다.
        content = re.sub(r'\s*([.,?!])\s*', r'\1', content)

        # 4. 리스트를 나타내는 하이픈(-) 앞에 줄바꿈을 추가합니다.
        content = re.sub(r'([^\n])\s*-\s*', r'\1\n- ', content)

        # 5. 최종적으로 연속된 줄바꿈을 하나로 줄입니다.
        content = re.sub(r'\n{2,}', '\n', content)

        print(">>>", content)
        return content

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while scraping {link}: {e}")
        return ""

def save_to_csv(data, filename):
    keys = data[0].keys() if data else []
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"Saved {len(data)} items to {filename}")

if __name__ == "__main__":
    results = []
    data_list = scrape_data(5)
    results.extend(data_list)
    save_to_csv(data_list, "육아_정보.csv")


