target_ip=$1

sudo sshpass -p Joulestore20202020 scp -o StrictHostKeyChecking=no -vvv -r /home/ubuntu/ehub-bakti pi@$target_ip:/home/pi/ehub-bakti
sudo sshpass -p Joulestore20202020 ssh pi@$target_ip 'sudo sh /home/pi/ehub-bakti/scripts/update-ehub-client.sh'