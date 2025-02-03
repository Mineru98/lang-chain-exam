import math
from datetime import datetime
from pprint import pprint

import requests
from geopy.geocoders import Nominatim


def geocoding(address):
    app = Nominatim(user_agent="South Korea")
    location = app.geocode(address)
    lat, lon = location.latitude, location.longitude
    location2 = app.reverse(f"{lat} {lon}")
    # 주어진 주소에서 필요한 주소 정보만 모아 주소 리턴
    data_list = ["province", "city", "county", "borough", "town"]
    ad = []
    for n in data_list:
        try:
            ad.append(location2.raw["address"][n])
        except:
            pass
    return location.latitude, location.longitude, " ".join(ad)


def mapToGrid(lat, lon, code=0):
    Re = 6371.00877  ##  지도반경
    grid = 5.0  ##  격자간격 (km)
    slat1 = 30.0  ##  표준위도 1
    slat2 = 60.0  ##  표준위도 2
    olon = 126.0  ##  기준점 경도
    olat = 38.0  ##  기준점 위도
    xo = 210 / grid  ##  기준점 X좌표
    yo = 675 / grid  ##  기준점 Y좌표
    first = 0

    if first == 0:
        PI = math.asin(1.0) * 2.0
        DEGRAD = PI / 180.0

        re = Re / grid
        slat1 = slat1 * DEGRAD
        slat2 = slat2 * DEGRAD
        olon = olon * DEGRAD
        olat = olat * DEGRAD

        sn = math.tan(PI * 0.25 + slat2 * 0.5) / math.tan(PI * 0.25 + slat1 * 0.5)
        sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
        sf = math.tan(PI * 0.25 + slat1 * 0.5)
        sf = math.pow(sf, sn) * math.cos(slat1) / sn
        ro = math.tan(PI * 0.25 + olat * 0.5)
        ro = re * sf / math.pow(ro, sn)
        first = 1
    ra = math.tan(PI * 0.25 + lat * DEGRAD * 0.5)
    ra = re * sf / pow(ra, sn)
    theta = lon * DEGRAD - olon
    if theta > PI:
        theta -= 2.0 * PI
    if theta < -PI:
        theta += 2.0 * PI
    theta *= sn
    x = (ra * math.sin(theta)) + xo
    y = (ro - ra * math.cos(theta)) + yo
    x = int(x + 1.5)
    y = int(y + 1.5)
    return x, y


def xy_geocoding(address):
    lat, lon, ad = geocoding(address)
    x, y = mapToGrid(lat, lon)
    return x, y, ad


input_addr = input("어느 지역의 날씨를 알고 싶어?\n>>> ")
nx, ny, ad = xy_geocoding(str(input_addr))
print(ad)

# 현재 날짜와 시간을 가져오고 분을 00으로 고정
now = datetime.now()
current_date = now.strftime("%Y%m%d")
current_hour = now.strftime("%H") + "00"

url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
params = {
    "serviceKey": "ABCRAVZMTztrgH7Tmx57gbZDppMsydsvmYGSB+L/kdeUogGc27e5pUf59dhduarPy3EpLPseeM9OVmvmslPX4w==",
    "pageNo": "1",
    "numOfRows": "1000",
    "dataType": "JSON",
    "base_date": current_date,  # 현재 날짜로 변경
    "base_time": "1200",  # 현재 시간으로 변경 (분은 00으로 고정)
    "nx": nx,
    "ny": ny,
}

response = requests.get(url, params=params, verify=False)

rows = response.json()
if rows["response"]["header"]["resultCode"] == "00":
    rows = rows["response"]["body"]["items"]["item"]
    weather_data = {}
    print(rows)
    for item in rows:
        # 기온
        if item["category"] == "T1H":
            weather_data["tmp"] = item["fcstValue"]
        # 습도
        if item["category"] == "REH":
            weather_data["hum"] = item["fcstValue"]
        # 하늘상태: 맑음(1) 구름많은(3) 흐림(4)
        if item["category"] == "SKY":
            weather_data["sky"] = item["fcstValue"]
        # 1시간 동안 강수량
        if item["category"] == "RN1":
            weather_data["rain"] = item["fcstValue"]

    pprint(weather_data)
