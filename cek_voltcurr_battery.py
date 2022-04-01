import redis
import can
import binascii
import os
from time import sleep
from config import redis_instance as red, log, logging, num_of_dock, MPPT_TYPE, PANEL2_TYPE
from pms.address import *
from pms.pms import *
import asyncio
import uvloop


can0 = can.Bus(channel='can0', bustype='socketcan_ctypes')
heartbeat = [0 for _ in range(0,num_of_dock+1)]
lost_conn_count = [0 for _ in range(0,num_of_dock+1)]
heartbeat_arus = [0,]
lost_conn_arus = [0,]
# 25700 - (int(msg2data[4:6],16) + ((int(msg2data[6:8],16) - 1 if int(msg2data[4:6],16) > 100 else int(msg2data[6:8],16)) * 256))
cell_calculate = lambda byte1, byte2 : 25700 - (int(byte1,16) + ((int(byte2,16) - 1 if int(byte1,16) > 100 else int(byte2,16)) * 256))

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


def handleVoltCurr():
    for dock in range(1, 17):
        curr = red.hget(f'pms{dock}', 'current')
        volt = red.hget(f'pms{dock}', 'voltage')
        print(f"current: {curr}")
        print(f"voltage: {volt}")


if __name__ == '__main__':
    handleVoltCurr()
