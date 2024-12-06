import requests as req
import base64
import os
import aiohttp

MN_CSE_URL = "http://127.0.0.1:7580/Mobius-MN"

request_nr = 1
temp_cin = []
Origin = ""
def init():
    global Origin
    with open("Origin.txt", "r", encoding="utf-8") as f:
        Origin = f.read()

    register()
    print("[*] MN-CSE2 Executed(It retrieves data from MN-CSE).")

def register():
    global request_nr

    if os.path.exists('Origin.txt'):
        with open('Origin.txt', 'r', encoding='UTF-8') as f:
            Origin = f.read()
        print("[*] Already Registered")
        return
    
    car_id_num = "car1" # input("Car ID Number : ")
    username = "car1"   # input("Username : ")
    password = "pwd1"   # input("Password : ")

    Origin = base64.b64encode((username+password).encode('UTF-8')).decode('ascii')
    
    header = {
        "X-M2M-RI": "req"+str(request_nr),
        "X-M2M-Origin": Origin,
        "Content-Type": "application/json;ty=2"
    }

    json_data = {
            "m2m:ae": {
            "rn": "MN-AE2-"+car_id_num,
            "api": "0.2.481.2.0001.001."+base64.b64encode(car_id_num.encode('UTF-8')).decode('ascii')+"2",
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

    request_nr += 1

async def retrieve_temp():
    global temp_cin, request_nr
    url = MN_CSE_URL + "/Sensors/Temperature?fu=1&ty=4"

    header = {
        "X-M2M-RI": "req" + str(request_nr),
        "X-M2M-Origin": Origin,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=header) as res:
                if res.status == 200:
                    data = await res.json()
                    request_nr += 1
                    temp_cin = data["m2m:uril"].extend(temp_cin)
                    temp_cin = list(set(temp_cin))
                else:
                    print(f"Error: {res.status} {await res.text()}")
    except Exception as e:
        print(e)

async def detect_fire():
    global temp_cin, request_nr
    url = "http://localhost:7580/" + temp_cin.pop()

    header = {
        "X-M2M-RI": "req" + str(request_nr),
        "X-M2M-Origin": Origin,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=header) as res:
                if res.status == 200:
                    data = await res.json()
                    request_nr += 1
                    con = data["con"]
                    temp = con["temperature"]
                    timestamp = con["timestamp"]

                    if temp > 200:
                        print("###### For the owner of the car ######")
                        print("[*] Fire Detected. Leave the car immediately.\n")

                        print("###### For the nearby ######")
                        print("[*] A fire has broken out in a vehicle near your car.")
                    elif temp > 130:
                        print("###### For the owner of the car ######")
                        print("[*] A serious issue has occurred with the battery. Inspect the battery immediately.")

                        print("###### For the nearby ######")
                        print("[*] A serious issue has occurred with the battery in a vehicle near your car.")
                                                
                    elif temp > 80:
                        print("###### For the owner of the car ######")
                        print("[*] An issue has been detected with the battery. Be cautious.")
                else:
                    print(f"Error: {res.status} {await res.text()}")
    except Exception as e:
        print(e)                

async def main():
    while True:
        await detect_fire()

if __name__ == "__main__":
    init()
    main()