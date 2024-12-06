import time
import aiohttp
import asyncio
import struct
import math
import base64
import requests as req

MN_CSE_URL = "http://127.0.0.1:7580/Mobius-MN"

class GPSSimulator:
    def __init__(self, latitude=36.4803, longitude=127.4305, speed_kmph=60, road_direction=0):
        self.start_time = time.time()
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = 10
        self.speed_kmph = speed_kmph
        self.road_direction = road_direction
        self.update_interval = 1
        self.speed_per_second = speed_kmph / 3600
        self.stop_time = 17  # 17초부터 정지 상태로 만들기 위한 설정
        self.is_moving = True  # 처음에는 이동 중

        self.register()

    async def send_binary_data_to_server(self):
        url = "http://127.0.0.1:5555/GPS_Data"
        lat = int(self.latitude * 1e6)  # 1e6 배율로 변환
        lon = int(self.longitude * 1e6)  # 1e6 배율로 변환
        alt = int(self.altitude * 1e6)  # 1e6 배율로 변환
        velocity = int(self.speed_per_second)

        # UBX 포맷: B5 62 01 07 (헤더 + 메시지 타입) + 데이터 (위도, 경도, 고도, 속도)
        binary_message = struct.pack('<B B B B I I I H', 
                                     0xB5, 0x62, 0x01, 0x07,  # 메시지 헤더
                                     lat, lon, alt, velocity)  # 위도, 경도, 고도, 속도

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=binary_message) as res:
                if res.status == 200:
                    print("GPS Data:", lat, lon, alt, velocity)
                else:
                    print("Error")

    async def update_gps(self):
        if self.is_moving:
            direction_rad = math.radians(self.road_direction)

            delta_lat = self.speed_per_second * math.cos(direction_rad)
            delta_lon = self.speed_per_second * math.sin(direction_rad)

            self.latitude += delta_lat
            self.longitude += delta_lon

    async def simulate_GPS_data(self):
        while True:
            elapsed_time = time.time() - self.start_time

            if elapsed_time >= self.stop_time:
                self.is_moving = False  # 정지 상태로 변경

            self.update_gps()

            await self.send_binary_data_to_server()

            await asyncio.sleep(self.update_interval)

    def register(self):
        sensor_id = "car1_gps"

        Origin = base64.b64encode((sensor_id).encode('UTF-8')).decode('ascii')

        header = {
            "X-M2M-RI": "req_adn_gps1",
            "X-M2M-Origin": Origin,
            "Content-Type": "application/json;ty=2"
        }

        json_data = {
                "m2m:ae": {
                "rn": "ADN-AE-car1_gps1",
                "api": "0.2.481.2.0001.001."+base64.b64encode(sensor_id.encode('UTF-8')).decode('ascii'),
                "rr": True,
            }
        }

        try:
            res = req.post(MN_CSE_URL, headers=header, json=json_data)
            if "rsc" in res:
                print("[*] Error:", res['msg'])
            else:
                print("[*] Registration Success!!")

        except Exception as e:
            print("[*] Registration Error :", e)