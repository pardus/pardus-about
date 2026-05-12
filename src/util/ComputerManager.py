import os
import gi
import json

from . import DBusManager
from . import HardwareDetector
from . import OSManager

import Actions

gi.require_version("GUdev", "1.0")
gi.require_version("GLib", "2.0")
from gi.repository import GUdev, GLib


FILTERED_WORDS = [
    "o.e.m.",
    "oem",
    "manufacturer",
    "n/a",
    "default",
    "string",
    "filled",
    "product",
    "name",
    "unknown",
]


class ComputerManager:
    computer_info = None
    processor_info = None
    memory_info = None

    def __init__(self):
        self.prepare_data()
        self.prepare_cpu_info()
        self.prepare_memory_info()

    def prepare_data(self):
        self.computer_info = {}
        self.processor_info = {}
        self.memory_info = []

        # Model
        model = None
        try:
            model = DBusManager.read_string_in_tuple(
                "org.freedesktop.hostname1",
                "/org/freedesktop/hostname1",
                "HardwareModel",
                0,
            )
        except Exception:
            pass

        if model:
            self.computer_info["model"] = model
        else:
            self.computer_info["model"] = "Unknown"
            if os.path.isfile("/sys/devices/virtual/dmi/id/product_name"):
                with open("/sys/devices/virtual/dmi/id/product_name", "r") as f:
                    self.computer_info["model"] = f.readline().strip()

        # Vendor
        vendor = None
        try:
            vendor = DBusManager.read_string_in_tuple(
                "org.freedesktop.hostname1",
                "/org/freedesktop/hostname1",
                "HardwareVendor",
                0,
            )
        except Exception:
            pass
        if vendor:
            self.computer_info["vendor"] = vendor
        else:
            self.computer_info["vendor"] = "Unknown"
            if os.path.isfile("/sys/devices/virtual/dmi/id/sys_vendor"):
                with open("/sys/devices/virtual/dmi/id/sys_vendor", "r") as f:
                    self.computer_info["vendor"] = f.readline().strip()

        # Family
        self.computer_info["family"] = "Unknown"
        if os.path.isfile("/sys/devices/virtual/dmi/id/product_family"):
            with open("/sys/devices/virtual/dmi/id/product_family", "r") as f:
                family = f.readline().strip()

                for f in FILTERED_WORDS:
                    if f.lower() in family.lower():
                        family = ""
                        break

                self.computer_info["family"] = family

        # Chassis
        chassis = None
        try:
            chassis = DBusManager.read_string_in_tuple(
                "org.freedesktop.hostname1", "/org/freedesktop/hostname1", "Chassis", 0
            )
        except Exception:
            pass

        if chassis:
            self.computer_info["chassis"] = chassis
        else:
            self.computer_info["chassis"] = "0"
            if os.path.isfile("/sys/devices/virtual/dmi/id/chassis_type"):
                with open("/sys/devices/virtual/dmi/id/chassis_type", "r") as f:
                    self.computer_info["chassis"] = f.readline().strip()

        # Bios Date
        self.computer_info["bios_date"] = "Unknown"
        if os.path.isfile("/sys/devices/virtual/dmi/id/bios_date"):
            with open("/sys/devices/virtual/dmi/id/bios_date", "r") as f:
                self.computer_info["bios_date"] = f.readline().strip()

        # Is Live USB?
        self.computer_info["live_boot"] = self.is_live_boot()

        # Oem Available
        self.computer_info["oem"] = os.path.isfile("/sys/firmware/acpi/tables/MSDM")

        # Deep sleep mode support
        with open("/sys/power/mem_sleep", "r") as f:
            self.computer_info["mem_sleep_support"] = "deep" in f.read()

        # ACPI:
        p = Actions.run("acpi")
        self.computer_info["is_acpi_supported"] = p.returncode == 0

        # Dual boot oses
        self.computer_info["dualboot"] = {}
        p = Actions.run("dualboot", capture_output=True)
        if p.returncode == 0:
            try:
                self.computer_info["dualboot"] = json.loads(p.stdout.decode("utf-8"))
            except Exception as e:
                print(e)
                print(p.stdout)

        # Boot mode (Uefi or legacy)
        self.computer_info["boot"] = "legacy"
        if os.path.isdir("/sys/firmware/efi/"):
            self.computer_info["boot"] = "UEFI"
            with open("/sys/firmware/efi/fw_platform_size", "r") as f:
                if "32" == f.readline().strip():
                    self.computer_info["boot"] = "UEFI32"

    def prepare_cpu_info(self):
        with open("/proc/cpuinfo", "r") as f:
            core_count = 0
            model_name = ""
            model_id = ""
            vendor = ""
            family = ""
            for line in f.readlines():
                splitted = line.split(":")
                if len(splitted) < 2:
                    continue

                key = splitted[0].strip()
                value = splitted[1].strip()

                if key == "siblings":
                    thread_count = int(value)
                elif key == "cpu cores":
                    core_count = int(value)
                elif key == "model name":
                    model_name = value
                elif key == "model":
                    model_id = value
                elif key == "cpu family":
                    family = value
                elif key == "vendor_id":
                    if "NTEL" in value.upper():
                        vendor = "Intel"
                    elif "AMD" in value.upper():
                        vendor = "AMD"
                    else:
                        vendor = "Unknown"

                if core_count and model_name and family and vendor and model_id:
                    break

            self.processor_info = {
                "name": model_name,
                "model_id": model_id,
                "vendor": vendor,
                "family_id": family,
                "core_count": core_count,
                "thread_count": thread_count,
            }

            return self.processor_info

    def prepare_memory_info(self):
        client = GUdev.Client.new(["dmi"])
        device = client.query_by_sysfs_path("/sys/devices/virtual/dmi/id")
        if device is None:
            return self.memory_info

        num_ram = device.get_property_as_uint64("MEMORY_ARRAY_NUM_DEVICES")
        for i in range(num_ram):
            vendor = device.get_property(f"MEMORY_DEVICE_{i}_MANUFACTURER")
            size = device.get_property_as_uint64(f"MEMORY_DEVICE_{i}_SIZE") / (
                1024 * 1024 * 1024
            )
            mem_type = device.get_property(f"MEMORY_DEVICE_{i}_TYPE")
            factor = device.get_property(f"MEMORY_DEVICE_{i}_FORM_FACTOR")
            # name = f"{size} GB {mem_type} {factor}"
            serial = device.get_property(f"MEMORY_DEVICE_{i}_SERIAL_NUMBER")
            ram_speed_mts = device.get_property(f"MEMORY_DEVICE_{i}_SPEED_MTS")
            part_number = device.get_property(f"MEMORY_DEVICE_{i}_PART_NUMBER")

            mem_device = {
                # "name": name,
                "vendor": vendor,
                "size": size,
                "factor": factor,
                "type": mem_type,
                "serial_number": serial,  # private information
                "speed": ram_speed_mts,
                "part_number": part_number,
            }

            for k in mem_device.keys():
                if mem_device[k] is None:
                    mem_device[k] = ""

            self.memory_info.append(mem_device)

        return self.memory_info

    def is_live_boot(self):
        with open("/proc/cmdline", "r") as f:
            data = f.read()

            if "boot=live" in data or "/live/vmlinuz" in data:
                return True

        return False

    def get_processor_info(self):
        return self.processor_info

    def get_computer_info(self):
        return self.computer_info

    def get_memory_info(self):
        return self.memory_info

    def get_memory_summary(self):
        size = 0
        if len(self.memory_info) == 0:
            return "Unknown"
        for mem in self.memory_info:
            size += mem["size"]

        summary = f"{size} GB"
        info = self.memory_info[0]
        # Add type if exists (DDR5)
        if info["type"] and info["type"] != "Unknown":
            summary += " " + info["type"]

        # Add factor if exists (SODIMM)
        if info["factor"] and info["factor"] != "Unknown":
            summary += " " + info["factor"]

        summary = summary.strip()  # strip whitespace

        return summary

    def get_all_device_info(self):
        pci_and_usb_devices = HardwareDetector.get_hardware_info()

        computer_info = {
            "processor": self.processor_info,
            "memory": self.memory_info,
            "computer": self.computer_info,
            "os": OSManager.get_os_info(),
        }

        computer_info.update(pci_and_usb_devices)

        return computer_info
