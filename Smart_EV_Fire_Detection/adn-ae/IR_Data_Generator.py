import time
import aiohttp
import asyncio
import base64
import requests as req

MN_CSE_URL = "http://127.0.0.1:7580/Mobius-MN"

class IRSimulator:
    def __init__(self):
        self.start_time = time.time()
        self.temperature = 45  # Initial temperature before accident (°C)
        self.accident_time = 15  # Time when accident occurs (in seconds)
        self.temperature_rise_time = 10  # Time it takes for temperature to rise to 380°C after the accident
        self.register()

    def calculate_temperature(self, current_time):
        if current_time - self.start_time > self.accident_time:
            time_since_accident = current_time - self.accident_time
            if time_since_accident <= self.temperature_rise_time:
                self.temperature = 45 + (380 - 45) * (time_since_accident / self.temperature_rise_time)
            else:
                self.temperature += 60
                if self.temperature >= 380:
                    self.temperature = 380
        return self.temperature

    async def send_data_to_server(self, temperature, timestamp):
        url = "http://127.0.0.1:5555/IR_Data"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data={
                'temperature': temperature,
                'timestamp': timestamp
            }) as res:
                if res.status == 200:
                    print("IR Data :", temperature, timestamp)
                else:
                    print("Error")

    async def simulate_IR_data(self, interval_seconds=0.5):
        while True:
            current_time = time.time()
            temperature = self.calculate_temperature(current_time)

            timestamp = int(time.time() * 1000) & 0xFFFFFFFF
            await self.send_data_to_server(temperature, timestamp)

            await asyncio.sleep(interval_seconds)

    def register(self):
        sensor_id = "car1_ir"

        Origin = base64.b64encode((sensor_id).encode('UTF-8')).decode('ascii')

        header = {
            "X-M2M-RI": "req_adn_ir1",
            "X-M2M-Origin": Origin,
            "Content-Type": "application/json;ty=2"
        }

        json_data = {
                "m2m:ae": {
                "rn": "ADN-AE-car1_ir1",
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