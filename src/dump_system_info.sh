#!/bin/bash
DIR="/tmp/pardus_system_report"
mkdir $DIR

# === SYSTEM INFO ===
distro="$(lsb_release -si)";
distro_version="$(lsb_release -sr)";
distro_codename="$(lsb_release -sc)";

kernel="$(uname -r)";
arch="$(uname -m)";

cpu_model="$(awk -F':' '/^model name/ {split($2, A, "@"); print A[1]; exit}' /proc/cpuinfo | xargs)";
cpu_count="$(grep -c '^processor' /proc/cpuinfo)";

cpu_max_hz_file="/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq"
cpu_max_hz="0"
if [ -f $cpu_max_hz_file ]; then
    cpu_max_hz="$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)";
fi

gpu="$(glxinfo | grep "OpenGL renderer string" | cut -d ':' -f2 | xargs)";

ram="$(free --giga | awk 'NR==2{print $2}')";

systeminfo="$DIR/systeminfo.txt";
touch $systeminfo;

echo "$distro $distro_version ($distro_codename)" >> $systeminfo;
echo "$USER@$HOSTNAME" >> $systeminfo;
echo "Kernel: $kernel" >> $systeminfo;
echo "Desktop: $XDG_CURRENT_DESKTOP" >> $systeminfo;
echo "CPU: $cpu_model x$cpu_count" >> $systeminfo;
echo "GPU: $gpu" >> $systeminfo;
echo "RAM: $ram GB" >> $systeminfo;