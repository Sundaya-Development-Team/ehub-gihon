from config import redis_instance as red, log, logging, num_of_dock
from handle_canbus import sendControlMosfetMsg
from time import sleep
from ast import literal_eval

if __name__ == '__main__':
    for dock in range(1,num_of_dock+1):
        try:
            cmos_state = str(red.hget(f'pms{dock}', 'cmos_state'))[2:-1]
        except:
            cmos_state = None
        try:
            dmos_state = str(red.hget(f'pms{dock}', 'dmos_state'))[2:-1]
        except:
            dmos_state = None
        try:
            temp_cmos = int(red.hget(f'pms{dock}', 'temp_cmos'))
        except:
            temp_cmos = None
        try:
            temp_dmos = int(red.hget(f'pms{dock}', 'temp_dmos'))
        except:
            temp_dmos = None

        log.debug(f'dock {dock} cmos:: state: {cmos_state}, temp: {temp_cmos}')
        log.debug(f'dock {dock} dmos:: state: {dmos_state}, temp: {temp_dmos}')
        if cmos_state is not None or temp_cmos is not None:
            if cmos_state == 'ON' and temp_cmos > 52:
                log.info('send msg mosfet cmos off')
                sendControlMosfetMsg(dock, 'input', 'off')
                sleep(0.1)
            elif cmos_state == 'OFF' and temp_cmos < 46:
                log.info('send messange on cmos')
                sendControlMosfetMsg(dock, 'input', 'on')
                sleep(0.1)

        if dmos_state is not None or temp_dmos is not None:
            if dmos_state == 'ON' and temp_dmos > 52:
                log.info('send msg mosfet dmos off')
                sendControlMosfetMsg(dock, 'output', 'off')
            elif dmos_state == 'OFF' and temp_dmos < 46:
                log.info('send messange on dmos')
                sendControlMosfetMsg(dock, 'output', 'on')
