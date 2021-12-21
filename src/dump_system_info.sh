#!/bin/bash
DIR="/tmp/pardus_system_report"
if [ -d "$DIR" ]; then
    rm -rf $DIR;
fi
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

totalmem=0; for mem in /sys/devices/system/memory/memory*; do [[ "$(cat ${mem}/online)" == "1" ]] && totalmem=$((totalmem+$((0x$(cat /sys/devices/system/memory/block_size_bytes))))); done
ram=$((totalmem/1024**3))

systeminfo="$DIR/systeminfo";
touch $systeminfo;

# DE version
DE=$XDG_CURRENT_DESKTOP;
DE_VER="";
if [[ $DE == "GNOME" ]]; then
    VER=($(gnome-shell --version))
    VER=${VER[2]}
    DE_VER=$VER;
elif [[ $DE == "XFCE" ]]; then
    VER=($(xfce4-panel --version))
    VER=${VER[3]::-1}
    DE_VER=$VER;
fi

echo "$distro $distro_version ($distro_codename)" >> $systeminfo;
echo "$USER@$HOSTNAME" >> $systeminfo;
echo "Kernel: $kernel" >> $systeminfo;
echo "Desktop: $DE $DE_VER" >> $systeminfo;
echo "CPU: $cpu_model x$cpu_count" >> $systeminfo;
echo "GPU: $gpu" >> $systeminfo;
echo "RAM: $ram GB" >> $systeminfo;