from config import redis_instance as red, log
import re
import os
from time import sleep
PATH = '/home/pi/sundaya/dataLogging/'

def initialize_snmp():
    os.system('sudo service snmpd restart')
    sleep(1.5)

def for_snmp(nama_file, data):
    log = open(nama_file, "w")
    log.write(data)
    log.close()

def redisWriteDataToSNMP(write=True):
    data = dict()
    for id in range(1,4):
        data[f'mppt{id}_pv_voltage'] = red.hget(f'mppt{id}', 'pv_voltage')
        data[f'mppt{id}_pv_current'] = red.hget(f'mppt{id}', 'pv_current')
        # data[f'mppt{id}_pv_power'] = red.hget(f'mppt{id}', 'pv_power')
    if write:
        for key, value in data.items():
            log.info(value)
            if re.match("^mppt._pv_current$", key) is not None:
                if data[key] is not None:
                    for_snmp(f'{PATH}{key}.txt', f'{int(float(data[key]) * 100)}')
                else:
                    for_snmp(f'{PATH}{key}.txt', '0')
            else:
                if data[key] is not None:
                    for_snmp(f'{PATH}{key}.txt', f'{int(float(data[key]) * 100)}')
                else:
                    for_snmp(f'{PATH}{key}.txt', '0')

def redisWriteDataPMS(write=True):
    voltage_list = list()
    vsat_curr = 0
    bts_curr = 0
    if red.hget('sensor_arus', 'load1') is not None:
        vsat_curr = int(float(red.hget('sensor_arus', 'load1')) * 100)
    if red.hget('sensor_arus', 'load2') is not None:
        bts_curr = int(float(red.hget('sensor_arus', 'load2')) * 100)
    log.debug(f'vsat curr : {vsat_curr} bts curr : {bts_curr}')
    if red.hget("sensor_arus", "load3") is not None:
        obl_curr = int(float(red.hget("sensor_arus", "load3")) * 100)
    log.debug(f"vsat curr : {vsat_curr} bts curr : {bts_curr} obl curr : {obl_curr}")
    dock_active = red.hgetall("dock_active")
    bts_state = bool(red.hget("relay", "bts"))
    vsat_state = bool(red.hget("relay", "vsat"))
    obl_state = bool(red.hget("relay", "obl"))

    # battery voltage mppt
    mppt_battery_volt = float(red.hget('mppt1', 'batt_voltage'))
    mppt_battery_volt = mppt_battery_volt * 100
    print(mppt_battery_volt)

    for dock, val in dock_active.items():
        if int(val) and red.hget(dock, 'dmos_state') == b'ON' and int(float(red.hget(dock, 'voltage'))) != 0:
            voltage_list.append(int(float(red.hget(dock, 'voltage'))))
    if len(voltage_list) == 0:
        avg_vpack = 0
    else:
        avg_vpack = (sum(voltage_list)/len(voltage_list)) - 0.8
    if write:
        for_snmp(f'{PATH}arus1.txt', str(vsat_curr))
        for_snmp(f'{PATH}arus2.txt', str(bts_curr))
        for_snmp(f'{PATH}arus3.txt', str(obl_curr))
        for_snmp(f'{PATH}batt_voltage.txt', str(avg_vpack))
        for_snmp(f'{PATH}lvd1.txt', str(avg_vpack))
        for_snmp(f'{PATH}lvd2.txt', str(avg_vpack))
        for_snmp(f'{PATH}lvd3.txt', str(avg_vpack))
        # for_snmp(f'{PATH}lvd1.txt', str(avg_vpack)) if vsat_state else for_snmp(f'{PATH}lvd1.txt', '0')
        # for_snmp(f'{PATH}lvd2.txt', str(avg_vpack)) if bts_state else for_snmp(f'{PATH}lvd2.txt', '0')
        # for_snmp(f'{PATH}lvd3.txt', str(avg_vpack)) if obl_state else for_snmp(f'{PATH}lvd3.txt', '0')
        for_snmp(f'{PATH}batt_voltage.txt', str(avg_vpack))

if __name__ == '__main__':
    initialize_snmp()
    redisWriteDataToSNMP(write=True)
    redisWriteDataPMS(write=True)