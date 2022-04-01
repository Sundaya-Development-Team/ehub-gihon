from config import redis_instance as red, num_of_dock, log, PANEL2_TYPE
import RPi.GPIO as GPIO
import time
import datetime

def for_snmp(nama_file, data):
    log = open(nama_file, "w")
    log.write(data)
    log.close()

def handle_selection():
    if PANEL2_TYPE == "new":
        bts_on = 13
        bts_off = 26
        vsat_on = 12
        vsat_off = 16
        raw_relay_state = int(red.get('relay_state'))
        if raw_relay_state == 6:
            other_state = False
            vsat_state = True
            bts_state = True
        elif raw_relay_state == 7:
            vsat_state = True
            bts_state = True
            other_state = True
        elif raw_relay_state >= 4 and raw_relay_state < 6:
            vsat_state = True
            bts_state = False
            other_state = False
        elif raw_relay_state == 2 or raw_relay_state == 3:
            vsat_state = False
            bts_state = True
            other_state = False
        elif raw_relay_state == 0 or raw_relay_state == 1:
            vsat_state = False
            bts_state = False
            other_state = False
        else:
            vsat_state = None
            bts_state = None
            other_state = None

    elif PANEL2_TYPE == "old":
        bts_on = 13
        bts_off = 12
        vsat_on = 16
        vsat_off = 19

        if float(red.hget('sensor_arus', 'load2')) > 0:
            red.hset('relay', 'bts', 1)
            bts_state = True
        else:
            red.hset('relay', 'bts', 0)
            bts_state = False
        if float(red.hget('sensor_arus', 'load1')) > 0:
            red.hset('relay', 'vsat', 1)
            vsat_state = True
        else:
            red.hset('relay', 'vsat', 0)
            vsat_state = False
        # if float(red.hget("sensor_arus", "load3")) > 0:
        #     red.hset("relay", "obl", 1)
        #     obl_state = True
        # else:
        #     red.hset("relay", "obl", 0)
        #     obl_state = False
        other_state = False
    return bts_on, bts_off, vsat_on, vsat_off, bts_state, vsat_state, other_state

if __name__ == '__main__':
    try:
        bts_on, bts_off, vsat_on, vsat_off, bts_state, vsat_state, other_state = handle_selection()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(bts_off,GPIO.OUT)
        GPIO.setup(vsat_on,GPIO.OUT)
        GPIO.setup(vsat_off,GPIO.OUT)
        GPIO.setup(bts_on,GPIO.OUT)
        if PANEL2_TYPE == "new":
            other_on = 19
            other_off = 20
            GPIO.setup(other_off,GPIO.OUT)
            GPIO.setup(other_on,GPIO.OUT)

        voltage = []
        dock_active = red.hgetall('dock_active')
        for key, val in dock_active.items():
            if int(val) and red.hget(key, 'dmos_state') == b'ON' and int(red.hget(key, 'voltage')) != 0:
                pms_v = red.hget(key, 'voltage')
                voltage.append(float(pms_v))
        avg_volt = sum(voltage)/len(voltage)
        min_volt = min(voltage)
        log.info(min_volt)
        log.info(f'bts_state = {bts_state} vsat_state = {vsat_state}')
        if avg_volt <= 4673:
            log.info('bts cutoff')
            GPIO.output(bts_off,GPIO.HIGH) #RELAY 2 reset
            GPIO.output(bts_on,GPIO.LOW)
            time.sleep(1)
            GPIO.output(bts_off,GPIO.LOW)
            red.set('relay:bts:last_cutoff', datetime.datetime.now().strftime('%Y%m%dT%H%M%S%z'))
        elif avg_volt >= 4800:
            log.info('bts reconnect')
            GPIO.output(bts_on,GPIO.HIGH)
            GPIO.output(bts_off,GPIO.LOW)
            time.sleep(1)
            GPIO.output(bts_on,GPIO.LOW)
            red.set('relay:bts:last_reconnect', datetime.datetime.now().strftime('%Y%m%dT%H%M%S%z'))

        if avg_volt <= 4473:
            log.info('vsat cutoff')
            GPIO.output(vsat_on,GPIO.LOW)
            GPIO.output(vsat_off,GPIO.HIGH)
            if PANEL2_TYPE == "new":
                GPIO.output(other_on,GPIO.LOW)
                GPIO.output(other_off,GPIO.HIGH)
            time.sleep(1)
            GPIO.output(vsat_off,GPIO.LOW)
            if PANEL2_TYPE == "new":
                GPIO.output(other_off,GPIO.LOW)
            red.set('relay:vsat:last_cutoff', datetime.datetime.now().strftime('%Y%m%dT%H%M%S%z'))
        elif avg_volt >= 4550:
            log.info('vsat reconnect')
            GPIO.output(vsat_off,GPIO.LOW) # RELAY 1 set
            GPIO.output(vsat_on,GPIO.HIGH)
            if PANEL2_TYPE == "new":
                GPIO.output(other_off,GPIO.LOW) # RELAY 1 set
                GPIO.output(other_on,GPIO.HIGH)
            time.sleep(1)
            GPIO.output(vsat_on,GPIO.LOW)
            other_state = True
            if PANEL2_TYPE == "new":
                GPIO.output(other_on,GPIO.LOW)
            red.set('relay:vsat:last_reconnect', datetime.datetime.now().strftime('%Y%m%dT%H%M%S%z'))

    except Exception as e:
        log.info(f"exception: {e}")

    finally:
        GPIO.cleanup()

    # sleep(60)