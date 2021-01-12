#!/bin/bash
DIR="/tmp/pardus_system_report"

# === LOGS ===
dmesg > $DIR/dmesg;
journalctl -q -n 1000 > $DIR/journalctl;
lspci -vvv > $DIR/lspci;
lsusb > $DIR/lsusb;

cp /var/log/auth.log $DIR/auth.log;
cp /var/log/boot.log $DIR/boot.log;
cp /var/log/daemon.log $DIR/daemon.log;
cp /var/log/dpkg.log $DIR/dpkg.log;
cp /var/log/kern.log $DIR/kern.log;
cp /var/log/syslog $DIR/syslog;
cp /var/log/user.log $DIR/user.log;

cp /etc/hosts $DIR/hosts;
cp /etc/apt/sources.list $DIR/sources.list;
cp -R /etc/apt/sources.list.d/ $DIR/;
apt list > $DIR/apt\ list;

# === ZIP FOLDER ===
ZIPNAME="pardus_system_report.tar.gz";
if [ $LANG == "tr_TR.UTF-8" ]; then
    ZIPNAME="pardus_sistem_raporu.tar.gz";
fi
tar -czf /tmp/$ZIPNAME -C $DIR .
rm -rf $DIR
