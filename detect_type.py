import can
import os
import binascii
from time import sleep
from config import redis_instance as red

def initialize_canbus(can0):
    os.system('sudo ip link set can0 type can bitrate 250000')
    os.system('sudo ifconfig can0 up')
    print('init canbus')
    sleep(2)
    init_sensor = can.Message(arbitration_id=0x0, data=[0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff], is_extended_id=False)
    can0.send(init_sensor)
    sleep(1)
    print('init canbus done')

def close_services():
    print('close services')
    os.system('sudo systemctl stop handle_canbus')
    sleep(1)
    os.system('sudo systemctl stop mppt')
    sleep(1)
    os.system('sudo systemctl stop accumulate_energy')
    sleep(1)
    os.system('sudo systemctl stop handle_relay.timer')
    sleep(1)

def start_services():
    print('start services')
    os.system('sudo systemctl daemon-reload')
    sleep(1)
    os.system('sudo systemctl start handle_canbus')
    sleep(1)
    os.system('sudo systemctl start mppt')
    sleep(1)
    os.system('sudo systemctl start accumulate_energy')
    sleep(1)
    os.system('sudo systemctl start handle_relay.timer')
    sleep(1)

def handleSensorArus(msg):
    relay_state = None
    if msg.arbitration_id == 490784999:
        hex_msg = binascii.hexlify(msg.data)
        str_msg = str(hex_msg)
        relay_state = int(str_msg[5])
    return relay_state

def detect_panel2():
    can0 = can.Bus(channel='can0', bustype='socketcan_ctypes')
    initialize_canbus(can0)
    for i in range(2000):
        msg = can0.recv(1)
        sensor_arus = handleSensorArus(msg)
        if sensor_arus != None and sensor_arus in [0, 1, 2, 4, 6, 7, 8]:
            print('panel 2 baru')
            red.set('PANEL2_TYPE', 'new')
            break
        if i == 1999:
            red.set('PANEL2_TYPE', 'old')
            print('panel 2 lama')


if __name__ == "__main__":
    close_services()
    detect_panel2()
    start_services()