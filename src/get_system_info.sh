#!/bin/bash

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

echo $distro;
echo $distro_version;
echo $distro_codename;
echo "$USER@$HOSTNAME";
echo $kernel;
echo $XDG_CURRENT_DESKTOP;
echo "$cpu_model x$cpu_count";
echo $cpu_max_hz;
echo $gpu;
echo $ram;
