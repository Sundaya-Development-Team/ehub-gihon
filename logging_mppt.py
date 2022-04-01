from time import sleep
from mppt.mpptsrne.sync import MPPTSRNE
from mppt.mpptepveper.mppt_epveper import MPPTEPVEPER
from config import redis_instance as red, log, number_mppt, MPPT_TYPE
import sys


port = '/dev/ttyS0'
if len(sys.argv) > 1:
    if sys.argv[1] != 'mppt-srne' or sys.argv[1] != 'mppt-epveper':
        raise Exception('Input mppt srne or mppt epveper')
    MPPT_TYPE = sys.argv[1]

if MPPT_TYPE == 'mppt-srne':
    mppt = MPPTSRNE(port=port, baudrate=9600)
elif MPPT_TYPE == 'mppt-epveper':
    mppt = MPPTEPVEPER(port=port, baudrate=115200)


def getAllSerialNumber(store=True):
    for index,id in enumerate(number_mppt):
        serial_num = mppt.getSerialNumber(id)
        log.debug(f'mppt {index+1} : {serial_num}')
        if store:
            red.hset(f'mppt{index+1}', 'serial_number', serial_num)
        sleep(0.5)

def getAllPVInfo(store=True):
    for index,id in enumerate(number_mppt):
        pvinfo = mppt.getPVInfo(id)
        log.debug(f'mppt {index+1} : {pvinfo}')
        if store:
            red.hset(f'mppt{index+1}', 'pv_voltage', pvinfo.get('pv_voltage').get('value'))
            red.hset(f'mppt{index+1}', 'pv_current', pvinfo.get('pv_current').get('value'))
            # red.hset(f'mppt{index+1}', 'pv_power', pvinfo.get('pv_power').get('value'))
        sleep(0.1)

def getBatteryVolt(store=True):
    for index,id in enumerate(number_mppt):
        battinfo = mppt.getBattVoltage(id)
        log.info(f'mppt {index+1} : {battinfo}')
        if store:
            red.hset(f'mppt{index+1}', 'batt_voltage', battinfo.get('battery_voltage').get('value'))

def getAllEnergy(store=True):
    for index,id in enumerate(number_mppt):
        try:
            accumulate_energy = int(red.hget(f'mppt{index+1}', 'harvest_accumulate_energy'))
        except TypeError:
            accumulate_energy = 0
        try:
            past_energy = int(red.hget(f'mppt{index+1}', 'harvest_energy'))
        except TypeError:
            past_energy = 0
        energy = mppt.getEnergyDay(id)
        if MPPT_TYPE == 'mppt-srne':
            if energy.get('harvest_energy').get('value') < past_energy:
                past_energy -= 65535
            accumulate_energy += energy.get('harvest_energy').get('value') - past_energy
        elif MPPT_TYPE == 'mppt-epveper':
            accumulate_energy = energy.get('harvest_energy').get('value')
        log.debug(f'mppt {index+1} : {energy.get("harvest_energy").get("value")}, past: {past_energy}, accumulate: {accumulate_energy}')
        if store:
            red.hset(f'mppt{index+1}', 'harvest_energy', energy.get('harvest_energy').get('value'))
            red.hset(f'mppt{index+1}', 'harvest_accumulate_energy', accumulate_energy)
        sleep(0.2)

# def settingParameter(id):
#     values = [557,552,547,547,547,537,490,480,470,460]
#     val_param = [int(val/4) for val in values]
#     val_param.insert(0, 12336)
#     val_param.insert(1, 0)
#     rr = mppt.setRegisters(id, addr.SETTING_PARAMETER[0], val_param)
#     return rr

def initialize(store=True):
    try:
        getAllSerialNumber(store=store)
        for id in number_mppt:
            print(mppt.settingParameter(id))
            sleep(2)
    except:
        print('Setting Error')

def mainFlow(loop=True, store=True):
    while loop:
        try:
            getAllPVInfo(store=store)
            getAllEnergy(store=store)
            red.set('error', 1)
        except Exception as e:
            red.set('error', 0)
            log.debug('Failed to run program')
            log.debug(e)
    getAllPVInfo(store=store)
    # getAllEnergy(store=False)

if __name__ == '__main__':
    initialize(store=False)
    mainFlow(loop=True)
    sleep(0.1)
