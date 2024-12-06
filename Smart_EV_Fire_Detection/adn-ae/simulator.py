import asyncio
from IMU_Data_Generator import IMUSimulator
from IR_Data_Generator import IRSimulator
from GPS_Data_Generator import GPSSimulator

async def main():
    IMU_S = IMUSimulator()
    IR_S = IRSimulator()
    GPS_S = GPSSimulator(latitude=36.4803, longitude=127.4305, speed_kmph=60, road_direction=0)

    imu_task = asyncio.create_task(IMU_S.simulate_IMU_data())
    ir_task = asyncio.create_task(IR_S.simulate_IR_data())
    gps_task = asyncio.create_task(GPS_S.simulate_GPS_data())

    await asyncio.gather(imu_task, ir_task, gps_task)

asyncio.run(main())