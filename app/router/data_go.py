# Third-party Libraries
from fastapi import APIRouter, Depends, Path
from fastapi_pagination import Page, paginate
from sqlalchemy.orm import Session
from typing_extensions import Annotated
import xml.etree.ElementTree as ET
import requests
import xmltodict

# Local Application Modules
from app.utils import get_db
import config

router = APIRouter()

@router.get(
    path="/",
    tags=["공공데이터포털"],
    summary="국립중앙의료원_전국 응급의료기관 정보 조회 서비스",
)
def get_emergency_infos(db: Session = Depends(get_db)):
    url = "http://apis.data.go.kr/B552657/ErmctInfoInqireService/getEgytBassInfoInqire"
    params = {"serviceKey": config.DATA_SECRET_KEY, "numOfRows": 1000, "pageNo": 1}

    response = requests.get(url, params=params)
    data_dict = xmltodict.parse(response.content)

    items = data_dict["response"]["body"]["items"]["item"]

    filtered = []
    # 산부인과 응급 대응 가능 병원을 뽑는 로직
    for item in items:
        # 응급실 여부
        is_hvec = int(item.get("hvec") or 0) > 0
        # 응급실 운영 여부
        is_dutyEryn = item.get("dutyEryn", "0") == "1"
        # 산부인과 여부
        is_OB_GYN = "산부인과" in item.get("dgidIdName", "")
        # 산부인과 응급상황 대응 가능 여부 = 조산 산모 수용 가능
        is_MKioskTy8 = item.get("mkioskTy8", "N") == "Y"
        # 산부인과 응급상황 대응 가능 여부 = 신생아 수용 가능
        is_MKioskTy10 = item.get("mkioskTy10", "N") == "Y"

        if is_hvec and is_dutyEryn and (is_OB_GYN or is_MKioskTy8 or is_MKioskTy10):
            filtered.append({
                "기관명": item.get("dutyName", ""),
                "우편번호": item.get("postCdn1", "") + item.get("postCdn2", ""),
                "주소": item.get("dutyAddr", ""),
                "대표전화": item.get("dutyTel1", ""),
                "응급실전화": item.get("dutyTel3", ""),
            })

    return {"data": filtered}
