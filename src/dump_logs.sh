#!/bin/bash
DIR="/tmp/pardus_system_report"

# === LOGS ===
dmesg > $DIR/dmesg.txt;
journalctl -q -n 1000 > $DIR/journalctl.txt;

cp /var/log/auth.log $DIR/auth.log;
cp /var/log/boot.log $DIR/boot.log;
cp /var/log/daemon.log $DIR/daemon.log;
cp /var/log/dpkg.log $DIR/dpkg.log;
cp /var/log/kern.log $DIR/kern.log;
cp /var/log/syslog $DIR/syslog;
cp /var/log/user.log $DIR/user.log;

# === ZIP FOLDER ===
tar -czf /tmp/pardus_system_report.tar.gz -C $DIR .
rm -rf $DIR