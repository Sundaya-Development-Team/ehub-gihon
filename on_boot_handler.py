from utils import send_command

if __name__ == "__main__":
    send_command('sudo systemctl stop hostapd.service')
    send_command('sudo systemctl disable hostapd.service')