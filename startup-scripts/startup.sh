# Requires wifi-connect from https://github.com/balena-io/wifi-connect/
echo "Testing connection"
sleep 10
echo "......................................................."
ip route | grep -v linkdown
if [ $? != 0 ]
then
        echo ""
        echo "No network connection found"
        python3 wifi-config.py &
        wifi-connect --portal-ssid="$WIFI_CONFIG_SSID" --portal-passphrase="$WIFI_CONFIG_PASSWD"
else
        echo ""
        echo "Network connection found"
fi
echo "......................................................."
echo ""
export FLASK_APP=/home/pi/Documents/raspberry-capture-kit/capturekit.py
cd /home/pi/Documents/raspberry-capture-kit/
flask run --host=0.0.0.0 --port=80

