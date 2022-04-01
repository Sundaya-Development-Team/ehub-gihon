echo "update program ehub"
echo "updating.."
sudo cp -r /home/pi/ehub-bakti/ /var/lib/sundaya/ehub-bakti/
echo "restart service..."
sudo systemctl daemon-reload
sudo systemctl restart mppt
sudo systemctl restart handle_canbus
sudo systemctl restart accumulate_energy
echo "update done"  