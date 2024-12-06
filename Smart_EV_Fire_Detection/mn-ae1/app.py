### This applicatoin pre-processes raw data of sensros and send to MN-CSE ###

from flask import Flask, request, jsonify, render_template, redirect
import requests as req
import base64
import os
import struct
import time

app = Flask(__name__)

MN_CSE_URL = "http://127.0.0.1:7580/Mobius-MN"
Origin = ""

request_nr = 1

collision = False
latitude = 0
longitude = 0
altitude = 0
temperature = 0

@app.route('/IMU_Data', methods=['POST'])
async def receive_data():
    global collision
    ACCELERATION_THRESHOLD = 15000
    GYROSCOPE_THRESHOLD = 300
    try:
        acc_x = int(request.form['acc_x'])
        acc_y = int(request.form['acc_y'])
        acc_z = int(request.form['acc_z'])
        gyr_x = int(request.form['gyr_x'])
        gyr_y = int(request.form['gyr_y'])
        gyr_z = int(request.form['gyr_z'])
        timestamp = int(request.form['timestamp'])

        if ((abs(acc_x) > ACCELERATION_THRESHOLD or abs(acc_y) > ACCELERATION_THRESHOLD or abs(acc_z) > ACCELERATION_THRESHOLD)
            or (abs(gyr_x) > GYROSCOPE_THRESHOLD or abs(gyr_y) > GYROSCOPE_THRESHOLD or abs(gyr_z) > GYROSCOPE_THRESHOLD)):
            collision = True
        else:
            collision = False

        con = {
            "collision": collision,
            "timestamp": timestamp,
        }

        createCIN("/Sensors/Collision", con)

        return jsonify({"msg": "Success"}), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 400

@app.route('/IR_Data', methods=['POST'])
def receive_temperature_data():
    global temperature
    try:
        temperature = float(request.form['temperature'])
        timestamp = int(request.form['timestamp'])
        
        con = {
            "temperature": temperature,
            "timestamp": timestamp
        }

        createCIN("/Sensors/Temperature", con)

        return jsonify({"msg": "Success"}), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 400

@app.route('/GPS_Data', methods=['POST'])
def receive_gps_data():
    global latitude, longitude, altitude
    try:
        binary_data = request.data

        lat, lon, alt = struct.unpack('<I I I', binary_data[4:16])

        latitude = lat / 1e7
        longitude = lon / 1e7
        altitude = alt / 1e7
        timestamp = int(time.time() * 1000) & 0xFFFFFFFF

        con = {
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "timestamp": timestamp
        }

        createCIN("/Sensors/GPS", con)

        return jsonify({"msg": "Success"}), 200

    except Exception as e:
        return jsonify({'msg': str(e)}), 400

def register():
    global request_nr, Origin

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
            "rn": "MN-AE-"+car_id_num,
            "api": "0.2.481.2.0001.001."+base64.b64encode(car_id_num.encode('UTF-8')).decode('ascii'),
            "rr": True,
        }
    }

    try:
        res = req.post(MN_CSE_URL, headers=header, json=json_data)
        if "rsc" in res:
            print("[*] Error:", res['msg'])
        else:
            with open('Origin.txt', 'a', encoding='UTF-8') as f:
                f.write(Origin)
            print("[*] Registration Success!!")

    except Exception as e:
        print("[*] Registration Error :", e)

    request_nr += 1

def createContainer(resourceName:str, path = ""):
    global request_nr

    url = MN_CSE_URL + path
    print(url)
    header = {
        "X-M2M-RI": "req"+str(request_nr),
        "X-M2M-Origin": Origin,
        "Content-Type": "application/json;ty=3"
    }

    json_data = {
        "m2m:cnt": {
            "rn": resourceName,
            "mbs": 16384,
            "mia": 60
        }
    }

    try:
        res = req.post(url, headers=header, json=json_data)
        if "rsc" in res:
            print("[*] Error:", res['msg'])
        else:
            print(f"[*] Container {path+resourceName} Registration Success!!")

    except Exception as e:
        print("[*] Registration Error :", e)

    request_nr += 1

def createCIN(path, con):
    global request_nr

    url = MN_CSE_URL + path
    header = {
        "X-M2M-RI": "req"+str(request_nr),
        "X-M2M-Origin": Origin,
        "Content-Type": "application/json;ty=4"
    }

    json_data = {
        "m2m:cin": {
            "con": con
        }
    }

    print(json_data)

    try:
        res = req.post(url, headers=header, json=json_data)
        if "rsc" in res:
            print("[*] Error:", res['msg'])
        else:
            print(f"[*] CIN Inserted")

    except Exception as e:
        print("[*] CIN Insertion Error :", e)

    request_nr += 1

def init():
    print("[*] MN-AE Executed")
    register()
    createContainer("Sensors")
    createContainer("Temperature", "/Sensors")
    createContainer("Collision", "/Sensors")
    createContainer("Gas", "/Sensors")
    createContainer("GPS", "/Sensors")

if __name__ == '__main__':
    init()
    app.run('0.0.0.0', port=5555, debug=True)