import pytz
from config import MPPT_TYPE
from utils import send_command
from config import redis_instance as red, num_of_dock, number_mppt
from datetime import datetime
from time import sleep

def redisParser(key1,key2,type_data):
    try:
        val = type_data(red.hget(key1,key2))
    except:
        val = red.hget(key1,key2)
    return val

def getDatetime():
    wib_timezone = pytz.timezone('Asia/Jakarta')
    dt = datetime.now(wib_timezone).strftime('%Y%m%dT%H%M%S%z')
    return dt

def getRaspiCPUTemp():
    temp = round(int(send_command('cat /sys/class/thermal/thermal_zone0/temp')) / 1000, 1)
    return temp

def getNOCData():
    energy_data = dict()
    energy_data['cpu_temp'] = getRaspiCPUTemp()
    energy_data['edl1'] = -1 * round(redisParser('accumulated', 'edl1',type_data=float) / 1000,1)
    energy_data['edl2'] = -1 * round(redisParser('accumulated', 'edl2',type_data=float) / 1000,1)
    energy_data['batt_volt'] = redisParser('accumulated', 'avg_vpack',type_data=float)
    dock_active = str()
    for no in range(1,num_of_dock+1):
        dock_active += redisParser('dock_active', f'pms{no}', type_data=str)[2:-1]
    energy_data['dock_active'] = hex(int(dock_active,2))[2:]
    energy_data['min_battv'] = redisParser('accumulated', 'min_vpack', type_data=float)
    energy_data['max_battv'] = redisParser('accumulated', 'max_vpack', type_data=float)
    energy_data['load1'] = redisParser('sensor_arus', 'load1',type_data=float)
    energy_data['load2'] = redisParser('sensor_arus', 'load2',type_data=float)
    for no in range(1,len(number_mppt)+1):
        if MPPT_TYPE == 'mppt-srne':
            energy_data[f'eh{no}'] = round((redisParser(f'mppt{no}', 'harvest_accumulate_energy',type_data=int) * 30) / 1000, 1)
        elif MPPT_TYPE == 'mppt-epveper':
            eh = round((redisParser(f'mppt{no}', 'harvest_accumulate_energy',type_data=int) * 30), 1)
            try:
                eh_accumulated = eh - round(float(red.get(f'mppt_prev_energy{no}')),1)
            except:
                eh_accumulated = 0
            energy_data[f'eh{no}'] = eh_accumulated
            red.set(f'mppt_prev_energy{no}', eh)
        energy_data[f'pv{no}_volt'] = redisParser(f'mppt{no}', 'pv_voltage',type_data=float)
        energy_data[f'pv{no}_curr'] = redisParser(f'mppt{no}', 'pv_current',type_data=float)
    for _ in range(5):
        red.hset('accumulated', 'edl1', 0)
        red.hset('accumulated', 'edl2', 0)
        red.hset('mppt1', 'harvest_accumulate_energy',0)
        red.hset('mppt2', 'harvest_accumulate_energy',0)
        red.hset('mppt3', 'harvest_accumulate_energy',0)
        sleep(0.2)
    return energy_data

def getBatteryData():
    num_of_cell =14
    list_dvc = []
    list_vpack = [redisParser(f'pms{dock}', 'voltage',type_data=int) for dock in range(1,num_of_dock+1) if redisParser("dock_active", f"pms{dock}", type_data=int)]
    for dock in range(1, num_of_dock+1):
        if redisParser("dock_active", f"pms{dock}", type_data=int):
            list_cells = [redisParser(f'pms{dock}', f'cell{num}_v', type_data=int) for num in range(1, num_of_cell+1)]
            dvc = int(max(list_cells) - min(list_cells))
            list_dvc.append(dvc)
    min_vpack = min(list_vpack) * 0.01
    max_vpack = max(list_vpack) * 0.01
    return {'max_battv': [list_vpack.index(max(list_vpack)) + 1, max_vpack], 'min_battv': [list_vpack.index(min(list_vpack)) + 1, min_vpack], 'dvc': list_dvc}

if __name__ == "__main__":
    data = dict()
    dt = getDatetime()
    data = getNOCData()
    batt_data = getBatteryData()
    data.update(batt_data)
    red.hset('data', dt, str(data))