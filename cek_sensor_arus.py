import redis
import can
import binascii
import os
from time import sleep
from config import redis_instance as red, log, logging, num_of_dock, MPPT_TYPE, PANEL2_TYPE
from pms.address import *
from pms.pms import *


can0 = can.Bus(channel='can0', bustype='socketcan_ctypes')

def initialize_canbus():
    log.info('canbus initialize...')
    os.system('sudo ip link set can0 type can bitrate 250000')
    os.system('sudo ifconfig can0 up')
    sleep(2)
    init_sensor = can.Message(arbitration_id=0x0, data=[0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff], is_extended_id=False)
    can0.send(init_sensor)
    sleep(1)
    log.info('done....')

def canbus_up():
    os.system('sudo ifconfig can0 up')
    log.warning('up canbus')

def canbus_down():
    os.system('sudo ifconfig can0 down')
    log.warning('down canbus')

def handleSensorArus():
    log.info(f"load1: {red.hget('sensor_arus', 'load1')}")
    log.info(f"load2: {red.hget('sensor_arus', 'load2')}")
    log.info(f"load3: {red.hget('sensor_arus', 'load3')}")
    


if __name__ == '__main__':
    handleSensorArus()
