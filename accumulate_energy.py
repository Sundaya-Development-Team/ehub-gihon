from datetime import datetime
from time import sleep
from config import redis_instance as red, num_of_dock
from store_log_data import redisParser

if __name__ == '__main__':
    reset = True
    while True:
        edl1 = redisParser('accumulated', 'edl1', type_data=float)
        edl2 = redisParser('accumulated', 'edl2', type_data=float)
        currentDT = datetime.now()
        jam = currentDT.hour
        menit = currentDT.minute
        if(jam == 0 and menit < 1 and reset == True):
            edl1 = 0
            edl2 = 0
            reset = False
        elif(jam != 0 and menit > 0):
            reset = True
        if edl1 is None:
            edl1 = 0
        if edl2 is None:
            edl2 = 0
        list_vpack = [redisParser(f'pms{dock}', 'voltage',type_data=int) for dock in range(1,num_of_dock+1) if redisParser("dock_active", f"pms{dock}", type_data=int) and redisParser(f'pms{dock}', 'voltage',type_data=int) != 0]
        avg_vpack = round(float(sum(list_vpack)/len(list_vpack) * 0.01), 2)
        load1 = redisParser('sensor_arus', 'load1',type_data=float)
        load2 = redisParser('sensor_arus', 'load2',type_data=float)
        edl1 += (avg_vpack * load1) if load1 is not None else (avg_vpack * 0)
        edl2 += (avg_vpack * load2) if load2 is not None else (avg_vpack * 0)
        red.hset('accumulated', 'avg_vpack', avg_vpack)
        red.hset('accumulated', 'edl1', round(edl1,2))
        red.hset('accumulated', 'edl2', round(edl2,2))
        sleep(1)