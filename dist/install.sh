#!/bin/bash
mode="$1"

sudo apt-get update

#install led button
sudo apt-get install can-utils -y
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
sudo python3 -m pip install --force-reinstall adafruit-blinka

sudo echo "blacklist snd_bcm2835" > /etc/modprobe.d/snd-blacklist.conf
sudo cp dist/config.txt /boot/config.txt
##########################################################################

cd /usr/lib/python3/dist-packages/
sudo git clone https://sundaya-dev-team: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@github.com/Sundaya-Development-Team/mppt.git
sudo git clone https://sundaya-dev-team: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@github.com/Sundaya-Development-Team/pms.git

#configurasi snmp
sudo cp /var/lib/sundaya/ehub-bakti/dist/snmp/* /etc/snmp/

sudo chmod +x /etc/snmp/*.sh

mkdir /home/pi/sundaya
mkdir /home/pi/sundaya/dataLogging
cp /var/lib/sundaya/ehub-bakti/dist/service/* /etc/systemd/system/

sudo pip3 install -r /var/lib/sundaya/ehub-bakti/requirements.txt

if [ $mode = "deploy" ]
then
    sudo systemctl enable ehub_onboot_handler.service
    sudo systemctl enable check_button.service
    sudo systemctl enable mppt.service
    sudo systemctl enable mppt_snmp.service
    sudo systemctl enable mppt_snmp.timer
    sudo systemctl enable handle_canbus.service
    sudo systemctl enable handle_relay.service
    sudo systemctl enable handle_relay.timer
    sudo systemctl enable handle_mosfet.service
    sudo systemctl enable handle_mosfet.timer
    sudo systemctl enable keep_alive_dock.service
    sudo systemctl enable keep_alive_dock.timer
    sudo systemctl enable accumulate_energy.service
    sudo systemctl enable store_log_data.service
    sudo systemctl enable store_log_data.timer

    sudo systemctl daemon-reload

    sudo systemctl start check_button.service
    sudo systemctl start store_log_data.service
    sudo systemctl start store_log_data.timer
    sudo systemctl start handle_relay.service
    sudo systemctl start handle_relay.timer
    sudo systemctl start accumulate_energy.service
    sudo systemctl start mppt_snmp.timer
    sudo systemctl start mppt.service
    sudo systemctl start handle_canbus.service
    sudo systemctl start handle_mosfet.service
    sudo systemctl start handle_mosfet.timer
    sudo systemctl start keep_alive_dock.timer
fi

echo 'success'