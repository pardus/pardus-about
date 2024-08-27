import os
import apt
import json

cpuinfo_path = "/proc/cpuinfo"
gpu_class = 0x030000
dc_class = 0x038000
sec_gpu_class = 0x030200
pci_dev_path = "/sys/bus/pci/devices"
pci_id_paths = ["/usr/share/misc/pci.ids", "/usr/share/hwdata/pci.ids"]


def int2hex(num):
    """
    Convert an integer to its hexadecimal string representation.

    :param num: The integer to convert.
    :return: A string representing the hexadecimal value of the integer.
    """
    return str(hex(num)[2:]).upper()


def line_split(line):
    """
    Split a line from /proc/cpuinfo on the tab and colon characters and strip whitespace.

    :param line: The line to split.
    :return: The part of the line after the tab and colon, stripped of leading and trailing whitespace.
    """
    return line.split("\t:")[1].strip()


def get_desktop_environment():
    """
    Get the desktop environment of the current user.
    """

    desktop_session = os.environ.get("XDG_CURRENT_DESKTOP")
    desktop_version = None
    cache = apt.Cache()
    if desktop_session == "GNOME":
        gnome = cache["gnome-shell"]
        desktop_version = gnome.installed.version.split("-")[0]

    return desktop_session, desktop_version


def get_cpu():
    """
    Parse the /proc/cpuinfo file to retrieve CPU information and return an instance of the CPU class.

    :return: An instance of the CPU class populated with information from /proc/cpuinfo.
    """
    with open(cpuinfo_path, "r") as f:
        file_content = f.readlines()
        model = None
        thread_no = None
        for line in file_content:
            if "model name" in line:
                model = line_split(line)
            if "siblings" in line:
                thread_no = line_split(line)

        return model, thread_no


import os


def parse_pci_ids():
    """
    Parse the PCI IDs from the pci.ids files and create a dictionary of devices.

    :return: A dictionary where keys are vendor IDs and values are dictionaries with vendor and device information.
    """
    for p in pci_id_paths:
        if os.path.isfile(p):
            with open(p, "r") as f:
                lines = f.readlines()
            devices = {}
            current_vendor = None

            for line in lines:
                if line.startswith("#") or line.strip() == "":
                    continue

                if not line.startswith("\t"):
                    # This is a vendor entry
                    if current_vendor:
                        devices[current_vendor] = vendor_info
                    vendor_id, vendor_name = line.strip().split(" ", 1)
                    current_vendor = int2hex(int(vendor_id, 16))
                    vendor_info = {"vendor_name": vendor_name.strip(), "devices": []}
                else:
                    # This is a device entry
                    device_id, device_name = line.strip().split(" ", 1)
                    vendor_info["devices"].append(
                        {
                            "device_id": int2hex(int(device_id, 16)),
                            "device_name": device_name.strip(),
                            "vendor_name": vendor_info["vendor_name"],
                        }
                    )
            if current_vendor:
                devices[current_vendor] = vendor_info

            return devices


parsed_pci_ids = parse_pci_ids()


def get_device_name(vendor_id, device_id):
    """
    Retrieve the device name for a given vendor and device ID.

    """
    for dev in parsed_pci_ids[vendor_id]["devices"]:
        if dev["device_id"] == device_id:
            return dev["device_name"]


def get_gpu():
    """
    Get GPU information.
    """
    devices = []
    for root, dirs, files in os.walk(pci_dev_path):
        for pci_dir in dirs:
            dev_content_path = os.path.join(root, pci_dir, "class")
            if os.path.exists(dev_content_path):
                with open(dev_content_path, "r") as f:
                    cont = f.readline().strip()
                    cont = int(cont, 16)
                    if cont == gpu_class or cont == dc_class:
                        is_secondary_gpu = cont == sec_gpu_class
                        vendor_id = None
                        driver = None
                        device_id = cont
                        ven_content_path = os.path.join(root, pci_dir, "vendor")
                        if os.path.exists(ven_content_path):
                            with open(ven_content_path) as f:
                                vendor_id = f.readline().strip()
                                vendor_id = int2hex(int(vendor_id, 16))
                        dev_content_path = os.path.join(root, pci_dir, "device")
                        if os.path.exists(dev_content_path):
                            with open(dev_content_path) as f:
                                device_id = f.readline().strip()
                                device_id = int2hex(int(device_id, 16))
                        drv_content_path = os.path.join(
                            root, pci_dir, "driver", "module"
                        )
                        if os.path.exists(drv_content_path):
                            gpu_drv_p = os.readlink(drv_content_path)
                            driver = os.path.basename(gpu_drv_p)
                        vendor = parsed_pci_ids[vendor_id]["vendor_name"]
                        device = get_device_name(vendor_id, device_id)
                        devices.append(
                            {
                                "vendor": vendor,
                                "device": device,
                                "driver": driver,
                                "is_secondary_gpu": is_secondary_gpu,
                            }
                        )
    return devices


def get_os_info():
    """
    Get OS information
    """
    cpu_model, thread_no = get_cpu()
    print("CPU Model: ", cpu_model)
    print("Thread Number: ", thread_no)
    kernel = os.uname().sysname
    release = os.uname().release
    print(get_desktop_environment())

    return kernel, release


def get_kernel():
    """
    Get the kernel version.
    """
    kernel = os.uname().sysname
    release = os.uname().release
    return kernel, release


def get_ram_size():
    """
    Get the total physical and total RAM size.
    """
    total_ram = 0
    total_physical_ram = 0
    # physical ram size
    try:
        with open("/sys/devices/system/memory/block_size_bytes") as bsbyte:
            block_size = int(bsbyte.read().strip(), 16)
        total_online_mem = 0
        total_offline_mem = 0
        m_files = os.listdir("/sys/devices/system/memory/")
        for file in m_files:
            if os.path.isdir("/sys/devices/system/memory/" + file) and file.startswith(
                "memory"
            ):
                with open("/sys/devices/system/memory/" + file + "/online") as online:
                    memory_on_off = online.read().strip()
                if memory_on_off == "1":
                    total_online_mem = total_online_mem + block_size
                if memory_on_off == "0":
                    total_offline_mem = total_offline_mem + block_size
        total_physical_ram = total_online_mem + total_offline_mem
    except Exception as e:
        print("Exception on /sys/devices/system/memory/block_size_bytes : {}".format(e))

    try:
        with open("/proc/meminfo") as meminfo:
            meminfo_lines = meminfo.read().split("\n")
        for line in meminfo_lines:
            if "MemTotal:" in line:
                total_ram = int(line.split()[1]) * 1024
    except Exception as e:
        print("Exception on /proc/meminfo : {}".format(e))
    return total_physical_ram, total_ram
