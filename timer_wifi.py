import re
from datetime import datetime, timedelta
from utils import send_command, check_program_active_time

CHECK_WIFI_STATUS= 'sudo systemctl is-failed hostapd.service'

def turn_off():
    send_command('sudo systemctl stop hostapd.service')
    send_command('sudo systemctl disable hostapd.service')
    send_command('sudo systemctl restart check_button.service')

if __name__ == '__main__':
    wifi_status = send_command(CHECK_WIFI_STATUS).rstrip()
    if wifi_status == 'active':
        active_time = check_program_active_time('hostapd.service')
        active_length = datetime.now() - datetime.strptime(active_time, "%Y-%m-%d %H:%M:%S")
        if active_length >= timedelta(hours=1):
            turn_off()