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

def sendChangeDockMsg(dock):
    messages = generateChangeDockMsg(dock)
    for msg in messages:
        can0.send(msg)

def sendControlMosfetMsg(dock, fet_type, fet_state):
    messages = generateMsgMosfetControl(dock, fet_type, fet_state)
    for msg in messages:
        can0.send(msg)
        sleep(0.5)

def shiftingDock (dock):
    shift_register = ShiftRegister(num_of_registers=6)
    if dock > 16:
        numberdock = dock-2
    else:
        numberdock = dock-1

    numberShift = int(numberdock/4)
    if dock > 16:
        pinShift = dock-1 + (4*numberShift)
    else:
        pinShift = dock + (4*numberShift)

    shift = int(pinShift)

    log.debug(numberdock)
    log.debug(numberShift)
    log.debug(shift)

    shift_register.setOutput(shift-1, GPIO.LOW)
    shift_register.latch()
    sendChangeDockMsg(dock)
    sleep(0.5)

    shift_register.setOutput(shift-1, GPIO.HIGH)
    shift_register.latch()
    sendChangeDockMsg(dock)
    sleep(0.5)

    shift_register.setOutput(shift-1, GPIO.LOW)
    shift_register.latch()
    sleep(0.5)


def handleDockChange(msg):
    if msg.arbitration_id == id17VoltCurr:
        pms_active = red.lrange('pms_active', 1, 16)
        if pms_active:
            dock_active = [int(is_actived) for is_actived in pms_active]
        if msg.arbitration_id in idMsgVoltageCurr:
            dock = idMsgVoltageCurr.index(msg.arbitration_id)
            if not dock_active[dock - 1]:
                shiftingDock(dock)

async def heartbeatPMS():
    while True:
        for dock,count in enumerate(heartbeat):
            log.debug(f'heartbeat pms{dock}: {count}')
            if dock != 17:
                if count > 3000:
                    heartbeat[dock] = 0
                if count == 0:
                    red.hset('dock_active', f'pms{dock}', 0)
                if count > 0:
                    red.hset('dock_active', f'pms{dock}', 1)
        await asyncio.sleep(1)

def handleVoltCurr(msg):
    if msg.arbitration_id in idMsgVoltageCurr:
        dock = idMsgVoltageCurr.index(msg.arbitration_id)
        heartbeat[dock] += 100
        for i in range(0, num_of_dock+1):
            if i != dock:
                if heartbeat[i] > 0:
                    heartbeat[i] -= 2
                else:
                    heartbeat[i] = 0
        hex_msg = binascii.hexlify(msg.data)
        volt_curr_data = str(hex_msg.decode("utf-8"))
        convData = conVoltAmp(volt_curr_data)
        log.debug(convData)
        red.hset(f'pms{dock}', 'current', convData[1])
        red.hset(f'pms{dock}', 'voltage', convData[0])

def handleReadMosfetState(msg):
    mos_state_definition = {
        '53': {
            'cmos' : 'ON',
            'dmos' : 'OFF'
        },
        '42': {
            'cmos' : 'OFF',
            'dmos' : 'ON'
        },
        '31': {
            'cmos' : 'ON',
            'dmos' : 'ON'
        },
        '65': {
            'cmos' : 'OFF',
            'dmos' : 'OFF'
        },
    }
    if msg.arbitration_id in idMsgMosfet:
        dock = idMsgMosfet.index(msg.arbitration_id)
        hex_msg = binascii.hexlify(msg.data)
        msg2data = str(hex_msg.decode("utf-8"))
        cmos_state= mos_state_definition.get(msg2data[:2]).get('cmos')
        dmos_state= mos_state_definition.get(msg2data[:2]).get('dmos')
        temp_top = 100 - int(msg2data[6:8], 16)
        temp_mid = 100 - int(msg2data[8:10], 16)
        temp_bot = 100 - int(msg2data[10:12], 16)
        temp_cmos = 100 - int(msg2data[14:16], 16)
        temp_dmos = 100 - int(msg2data[12:14], 16)
        red.hset(f'pms{dock}', 'cmos_state', cmos_state)
        red.hset(f'pms{dock}', 'dmos_state', dmos_state)
        red.hset(f'pms{dock}', 'temp_top', temp_top)
        red.hset(f'pms{dock}', 'temp_mid', temp_mid)
        red.hset(f'pms{dock}', 'temp_bot', temp_bot)
        red.hset(f'pms{dock}', 'temp_cmos', temp_cmos)
        red.hset(f'pms{dock}', 'temp_dmos', temp_dmos)
        log.debug(f'temp top:: dock: {dock} data: {temp_top}')
        log.debug(f'temp mid:: dock: {dock} data: {temp_mid}')
        log.debug(f'temp bot:: dock: {dock} data: {temp_bot}')
        log.debug(f'temp cmos:: dock: {dock} data: {temp_cmos}')
        log.debug(f'temp dmos:: dock: {dock} data: {temp_dmos}')
        log.debug(f'cmos state:: dock: {dock} data: {cmos_state}')
        log.debug(f'dmos state:: dock: {dock} data: {dmos_state}')

def handleSensorArus(msg):
    lost_conn_arus[0] += 1
    if msg.arbitration_id == idSensorArus:
        heartbeat_arus[0] += 1
        hex_msg = binascii.hexlify(msg.data)
        str_msg = str(hex_msg)
        relay_state = int(str_msg[5])
        if PANEL2_TYPE == "new":
            log.debug(relay_state)
        A1 = int(f'0x{str_msg[6:8]}',0)
        mA1 = int(f'0x{str_msg[8:10]}',0)
        A2 = int(f'0x{str_msg[10:12]}',0)
        mA2 = int(f'0x{str_msg[12:14]}',0)
        A3 = int(f'0x{str_msg[14:16]}',0)
        mA3 = int(f'0x{str_msg[16:18]}',0)
        if len(str(mA1)) < 2:
            mA1 = mA1 * 10
        if mA1 == 0:
            A1 = A1 * 10
        if len(str(mA2)) < 2:
            mA2 = mA2 * 10
        if mA2 == 0:
            A2 = A2 * 10
        if len(str(mA3)) < 2:
            mA3 = mA3 * 10
        if mA3 == 0:
            A3 = A3 * 10
        load1 = round(float(f'{A1}{mA1}') * 0.01,2)
        load2 = round(float(f'{A2}{mA2}') * 0.01,2)
        load3 = round(float(f'{A3}{mA3}') * 0.01,2)
        if PANEL2_TYPE == "new":
            red.set('relay_state', relay_state)
        else:
            relay_state = 0
            if load1 > 0:
                relay_state += 4
            elif load2 > 0:
                relay_state += 2
            elif load3 > 0:
                relay_state += 1
            red.set('relay_state', relay_state)
        red.hset('sensor_arus', 'load1', load1)
        red.hset('sensor_arus', 'load2', load2)
        red.hset('sensor_arus', 'load3', load3)
        log.debug(f'sensor arus: load1 data: {load1}')
        log.debug(f'sensor arus: load1 data: {load2}')
        log.debug(f'sensor arus: load1 data: {load3}')
    if lost_conn_arus[0] > 5000:
        red.hset('sensor_status', 'arus_heartbeat',heartbeat_arus[0])
        heartbeat_arus[0] = 0

def handleCellVBatch1(msg):
    if msg.arbitration_id in idMsgCellBatch1:
        dock = idMsgCellBatch1.index(msg.arbitration_id)
        hex_msg = binascii.hexlify(msg.data)
        # cell2_v = 25700 - (int(msg2data[4:6],16) + ((int(msg2data[6:8],16) - 1 if int(msg2data[4:6],16) > 100 else int(msg2data[6:8],16)) * 256))
        msg2data = str(hex_msg.decode("utf-8"))
        cell1_v = cell_calculate(msg2data[:2],msg2data[2:4])
        cell2_v = cell_calculate(msg2data[4:6],msg2data[6:8])
        cell3_v = cell_calculate(msg2data[8:10],msg2data[10:12])
        cell4_v = cell_calculate(msg2data[12:14],msg2data[14:16])
        red.hset(f'pms{dock}', 'cell1_v', cell1_v)
        red.hset(f'pms{dock}', 'cell2_v', cell2_v)
        red.hset(f'pms{dock}', 'cell3_v', cell3_v)
        red.hset(f'pms{dock}', 'cell4_v', cell4_v)
        log.debug(f'cell1_voltage:: dock: {dock} data:{cell1_v}')
        log.debug(f'cell2_voltage:: dock: {dock} data:{cell2_v}')
        log.debug(f'cell3_voltage:: dock: {dock} data:{cell3_v}')
        log.debug(f'cell4_voltage:: dock: {dock} data:{cell4_v}')


def handleCellVBatch2(msg):
    if msg.arbitration_id in idMsgCellBatch2:
        dock = idMsgCellBatch2.index(msg.arbitration_id)
        hex_msg = binascii.hexlify(msg.data)
        msg2data = str(hex_msg.decode("utf-8"))
        cell5_v = cell_calculate(msg2data[:2],msg2data[2:4])
        cell6_v = cell_calculate(msg2data[4:6],msg2data[6:8])
        cell7_v = cell_calculate(msg2data[8:10],msg2data[10:12])
        cell8_v = cell_calculate(msg2data[12:14],msg2data[14:16])
        red.hset(f'pms{dock}', 'cell5_v', cell5_v)
        red.hset(f'pms{dock}', 'cell6_v', cell6_v)
        red.hset(f'pms{dock}', 'cell7_v', cell7_v)
        red.hset(f'pms{dock}', 'cell8_v', cell8_v)
        log.debug(f'cell5_voltage:: dock: {dock} data:{cell5_v}')
        log.debug(f'cell6_voltage:: dock: {dock} data:{cell6_v}')
        log.debug(f'cell7_voltage:: dock: {dock} data:{cell7_v}')
        log.debug(f'cell8_voltage:: dock: {dock} data:{cell8_v}')


def handleCellVBatch3(msg):
    if msg.arbitration_id in idMsgCellBatch3:
        dock = idMsgCellBatch3.index(msg.arbitration_id)
        hex_msg = binascii.hexlify(msg.data)
        msg2data = str(hex_msg.decode("utf-8"))
        cell9_v = cell_calculate(msg2data[:2],msg2data[2:4])
        cell10_v = cell_calculate(msg2data[4:6],msg2data[6:8])
        cell11_v = cell_calculate(msg2data[8:10],msg2data[10:12])
        cell12_v = cell_calculate(msg2data[12:14],msg2data[14:16])
        red.hset(f'pms{dock}', 'cell9_v', cell9_v)
        red.hset(f'pms{dock}', 'cell10_v', cell10_v)
        red.hset(f'pms{dock}', 'cell11_v', cell11_v)
        red.hset(f'pms{dock}', 'cell12_v', cell12_v)
        log.debug(f'cell9_voltage:: dock: {dock} data:{cell9_v}')
        log.debug(f'cell10_voltage:: dock: {dock} data:{cell10_v}')
        log.debug(f'cell11_voltage:: dock: {dock} data:{cell11_v}')
        log.debug(f'cell12_voltage:: dock: {dock} data:{cell12_v}')


def handleCellVBatch4(msg):
    if msg.arbitration_id in idMsgCellBatch4:
        dock = idMsgCellBatch4.index(msg.arbitration_id)
        hex_msg = binascii.hexlify(msg.data)
        msg2data = str(hex_msg.decode("utf-8"))
        cell13_v = cell_calculate(msg2data[:2],msg2data[2:4])
        cell14_v = cell_calculate(msg2data[4:6],msg2data[6:8])
        red.hset(f'pms{dock}', 'cell13_v', cell13_v)
        red.hset(f'pms{dock}', 'cell14_v', cell14_v)
        log.debug(f'cell13_voltage:: dock: {dock} data:{cell13_v}')
        log.debug(f'cell14_voltage:: dock: {dock} data:{cell14_v}')

async def readCanbus():
    can0 = can.Bus('can0', bustype='socketcan_ctypes', receive_own_messages=False)
    reader = can.AsyncBufferedReader()

    listeners = [
        reader,         # AsyncBufferedReader() listener
        handleVoltCurr,
        handleReadMosfetState,
        handleCellVBatch1,
        handleCellVBatch2,
        handleCellVBatch3,
        handleCellVBatch4,
        handleSensorArus,
    ]

    # Create Notifier with an explicit loop to use for scheduling of callbacks
    # while True:
    loop = asyncio.get_event_loop()
    notifier = can.Notifier(can0, listeners, loop=loop)
    while True:
        try:
            msg = await reader.get_message()
        except can.CanError:
            canbus_up()
# Wait for last message to arrive
    await reader.get_message()
    print('Done!')

    # Clean-up
    notifier.stop()
    can0.shutdown()
    # canbus_down()
    # await asyncio.sleep(2)
    # canbus_up()
    log.debug('sleep asyncio')
    #   await asyncio.sleep(30)

async def cekDockActive():
    can0 = can.Bus('can0', bustype='socketcan_ctypes', receive_own_messages=False)
    reader = can.AsyncBufferedReader()

    dock_active = [0 for i in range(0, num_of_dock+1)]
    listeners = [
        reader,
    ]

    # Create Notifier with an explicit loop to use for scheduling of callbacks
    loop = asyncio.get_event_loop()
    notifier = can.Notifier(can0, listeners, loop=loop)

    while True:
        for _ in range(30):
            try:
                msg = await reader.get_message()
                if msg.arbitration_id in idMsgVoltageCurr:
                    dock = idMsgVoltageCurr.index(msg.arbitration_id)
                    log.debug(f'id batre {dock}')
                    dock_active[dock] = 1
            except can.CanError:
                canbus_up()
        if num_of_dock > 16:
            dock_active.pop(17)
        for count,dock in enumerate(dock_active):
            red.hset('dock_active', f'pms{count+1}', dock)
    # Wait for last message to arrive
    await reader.get_message()
    print('Done!')

    # Clean-up
    notifier.stop()
    can0.shutdown()


async def cekNewBattery(init=False):
    can0 = can.Bus('can0', bustype='socketcan_ctypes')
    reader = can.AsyncBufferedReader()

    listeners = [
        reader,         # AsyncBufferedReader() listener
    ]
    while True:
        try:
            loop = asyncio.get_event_loop()
            notifier = can.Notifier(can0, listeners, loop=loop)

            for _ in range(1000):
                try:
                    msg = await reader.get_message()
                except can.CanError:
                    canbus_up()
                if msg.arbitration_id == id17VoltCurr:
                    dock_active = [0 for i in range(0,num_of_dock+1)]
                    i = 0
                    n = num_of_dock+10
                    while i < n:
                        try:
                            msg = await reader.get_message()
                        except can.CanError:
                            canbus_up()
                        if msg.arbitration_id in idMsgVoltageCurr:
                            dock = idMsgVoltageCurr.index(msg.arbitration_id)
                            log.debug(f'id batre {dock}')
                            dock_active[dock] = 1
                            i += 1
                        if num_of_dock > 16:
                            dock_active[17] = 1
                    log.debug(f'dock active = {dock_active}')
                    if dock_active[0]:
                        while True:
                            try:
                                dock_empty = dock_active.index(0)
                                log.debug(f'shifting dock 17 to {dock_empty}')
                                shiftingDock(dock_empty)
                                dock_active[dock_empty] = 1
                            except ValueError:
                                break
            await reader.get_message()
            notifier.stop()
            if init:
                # for dock in range(1,num_of_dock+1):
                #     sendControlMosfetMsg(dock, 'input', 'on')
                #     sleep(0.2)
                #     sendControlMosfetMsg(dock, 'output', 'on')
                log.debug('initialize done')
                break
            await asyncio.sleep(10)
        except:
            pass

if __name__ == '__main__':
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    initialize_canbus()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cekNewBattery(init=True))
    loop.create_task(heartbeatPMS())
    loop.create_task(readCanbus())
    loop.create_task(cekNewBattery(init=False))
    loop.run_forever()