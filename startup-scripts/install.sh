echo "fixing git"
find .git/objects/ -type f -empty | xargs rm
git fetch -p
git fsck --full
echo "deleting flask service"
systemctl stop flask.service
rm -rf /etc/systemd/system/flask.service
echo "reloading systemctl daemon"
systemctl daemon-reload
echo "changing startup"
cd /home/pi/Documents/raspberry-capture-kit/startup-scripts
cp ./startup.desktop /etc/xdg/autostart/startup.desktop
echo "launchflask.sh permissions"
chmod 755 ../launchflask.sh
echo "startup.sh permissions"
chmod 755 ./startup.sh