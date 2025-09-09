import requests
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

load_dotenv()
DATA_SECRET_KEY = os.getenv("DATA_SECRET_KEY")

SERVICE_KEY = DATA_SECRET_KEY
URL = "http://apis.data.go.kr/B552657/ErmctInfoInqireService/getEmrrmRltmUsefulSckbdInfoInqire"
params = {
    "serviceKey": SERVICE_KEY,
    "numOfRows": 1000,
    "pageNo": 1
}

response = requests.get(URL, params=params)
root = ET.fromstring(response.content)

for item in root.iter("item"):
    duty_name = item.find("dutyName").text
    dept_info = item.find("dutyInf").text
    if "산부인과" in dept_info:
        print(duty_name, dept_info)

if __name__ == "__main__":
    results = []
    data_list = scrape_data(5)
    results.extend(data_list)
    save_to_csv(data_list, "육아_정보.csv")