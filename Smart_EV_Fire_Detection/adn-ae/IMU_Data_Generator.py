import random
import time
import aiohttp
import asyncio
import base64
import requests as req


MN_CSE_URL = "http://127.0.0.1:7580/Mobius-MN"

class IMUSimulator:
    ACCELERATION_STEP = 1000  # 1 km/s^2 in LSB (equivalent to 1 g = 9.81 m/s^2, but scaled)
    accident_triggered = False
    accident_time = 15  # Time when accident occurs (in seconds)
    
    def __init__(self):
        self.start_time = time.time()
        self.acc_x = 0
        self.acc_y = 0
        self.acc_z = 16000  # 1g gravity effect (Z-axis)
        self.register()

    def generate_steady_state_data(self):
        gyr_x = 0
        gyr_y = 0
        gyr_z = 0

        timestamp = int(time.time() * 1000) & 0xFFFFFFFF  # Current timestamp in milliseconds
        return self.acc_x, self.acc_y, self.acc_z, gyr_x, gyr_y, gyr_z, timestamp

    def generate_accident_data(self):
        acc_x = 20000  # Sudden impact in X-axis
        acc_y = -15000  # Sudden impact in Y-axis
        acc_z = 12000  # Sudden impact in Z-axis

        gyr_x = 500  # High rotation on X-axis
        gyr_y = -500  # High rotation on Y-axis
        gyr_z = 1000  # High rotation on Z-axis

        timestamp = int(time.time() * 1000) & 0xFFFFFFFF  # Current timestamp in milliseconds
        return acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, timestamp

    def generate_post_accident_data(self):
        acc_x = random.randint(-5000, 5000)  # Irregular vibrations
        acc_y = random.randint(-5000, 5000)
        acc_z = random.randint(10000, 20000)  # Z-axis irregularity due to impact

        gyr_x = random.randint(-100, 100)  # Post-accident rotation
        gyr_y = random.randint(-100, 100)
        gyr_z = random.randint(-100, 100)

        timestamp = int(time.time() * 1000) & 0xFFFFFFFF  # Current timestamp in milliseconds
        return acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, timestamp

    async def send_data_to_server(self, acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, timestamp):
        url = "http://localhost:5555/IMU_Data"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data={
                'acc_x': acc_x,
                'acc_y': acc_y,
                'acc_z': acc_z,
                'gyr_x': gyr_x,
                'gyr_y': gyr_y,
                'gyr_z': gyr_z,
                'timestamp': timestamp
            }) as res:
                if res.status == 200:
                    print("IMU Data:", acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, timestamp)
                else:
                    print("Error")

    async def simulate_IMU_data(self, interval_seconds=0.5):
        while True:
            current_time = time.time()

            if not self.accident_triggered:
                # Simulate random acceleration change before the accident
                self.acc_x += random.choice([self.ACCELERATION_STEP, -self.ACCELERATION_STEP])
                self.acc_y += random.choice([self.ACCELERATION_STEP, -self.ACCELERATION_STEP])
                self.acc_z = 16000  # Standard gravity effect on Z-axis

                # Generate steady state data
                acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, timestamp = self.generate_steady_state_data()

                # Check if the accident time has been reached (15 seconds)
                if current_time - self.start_time >= self.accident_time:
                    acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, timestamp = self.generate_accident_data()
                    self.accident_triggered = True
            else:
                # Generate post-accident data
                acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, timestamp = self.generate_post_accident_data()
                if current_time - self.start_time >= self.accident_time + 2:
                    acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, timestamp = 0, 0, 0, 0, 0, 0, int(time.time() * 1000) & 0xFFFFFFFF

            try:
                await self.send_data_to_server(acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, timestamp)
            except Exception as e:
                print(e)

            await asyncio.sleep(interval_seconds)

    def register(self):
        sensor_id = "car1_imu"

        Origin = base64.b64encode((sensor_id).encode('UTF-8')).decode('ascii')

        header = {
            "X-M2M-RI": "req_adn_imu1",
            "X-M2M-Origin": Origin,
            "Content-Type": "application/json;ty=2"
        }

        json_data = {
                "m2m:ae": {
                "rn": "ADN-AE-car1_imu1",
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