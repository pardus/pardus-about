#!/usr/bin/env python3

import subprocess, os
from copy import deepcopy

class GPU:

    def __init__(self):

        self.system_pci_ids = "/usr/share/misc/pci.ids"
        self.pardus_pci_ids = "/usr/share/pardus/pardus-about/data/pci.ids"
        self.udev_hwdb = "/usr/lib/udev/hwdb.d/" if os.path.exists("/usr/lib/udev/hwdb.d/") else "/lib/udev/hwdb.d/"
        self.default_gpu = []
        self.extra_gpu = []
        self.all_gpu = []
        self.glx = []

    def get_gpu_name(self, vendor, device):

        device_vendor_name, device_model_name = self.control_pci_ids(vendor, device, self.pardus_pci_ids)

        if device_vendor_name == 0 or device_model_name == 0:
            print("device name not found in {} {}:{}".format(self.pardus_pci_ids, vendor, device))
            device_vendor_name, device_model_name = self.control_pci_ids(vendor, device, self.system_pci_ids)

        if device_vendor_name == 0 or device_model_name == 0:
            print("device name not found in {} {}:{}".format(self.system_pci_ids, vendor, device))

            try:
                vendor_8b = vendor
                device_8b = device
                while len(vendor_8b) < 8:
                    vendor_8b = "0" + vendor_8b
                while len(device_8b) < 8:
                    device_8b = "0" + device_8b

                vendor_8b = "{}".format(vendor_8b).upper()
                device_8b = "{}".format(device_8b).upper()

                vendor_text = "pci:v" + vendor_8b + "*" + "\n ID_VENDOR_FROM_DATABASE="
                model_text = "pci:v" + vendor_8b + "d" + device_8b + "*" + "\n ID_MODEL_FROM_DATABASE="

                with open(self.udev_hwdb + "20-pci-vendor-model.hwdb", encoding="utf-8") as reader:
                    ids_file_output = reader.read()

                if vendor_text in ids_file_output:
                    rest_of_the_ids_file_output = ids_file_output.split(vendor_text, 1)[1]
                    device_vendor_name = rest_of_the_ids_file_output.split("\n", 1)[0]
                    if model_text in ids_file_output:
                        device_model_name = rest_of_the_ids_file_output.split(model_text, 1)[1].split("\n", 1)[0]
                    else:
                        device_model_name = ""
                else:
                    device_vendor_name = ""
                    device_model_name = ""
            except Exception as e:
                print("{}".format(e))
                device_vendor_name = ""
                device_model_name = ""

        if device_vendor_name == "" or device_model_name == "":
            print("device name not found in {} {}:{}".format(self.udev_hwdb, vendor, device))

        if "nvidia" in device_vendor_name.lower():
            device_vendor_name = "NVIDIA"
        elif "amd" in device_vendor_name.lower():
            device_vendor_name = "AMD"
        elif "intel" in device_vendor_name.lower():
            device_vendor_name = "INTEL"

        if device_vendor_name == "NVIDIA" or device_vendor_name == "AMD":
            if "[" in device_model_name and "]" in device_model_name:
                device_model_name = device_model_name[device_model_name.find("[") + 1:device_model_name.find("]")]

        return "{}".format(device_vendor_name), "{}".format(device_model_name)

    def control_pci_ids(self, vendor, device, filepath):

        if os.path.isfile(filepath):
            return self.lookup_pci_ids(vendor, device, filepath)
        print("{} file not found".format(filepath))
        return 0, 0

    def lookup_pci_ids(self, vendor, device, filepath):

        pci_ids = open(filepath, "r").readlines()
        temp_vendor = ""
        ids_lib = {}
        for line in pci_ids:
            # If line is tabbed or contains an hashtag skips
            if line[:3] == "\t\t" or line[0] == "#":
                continue
            # If line isn't tabbed and isn't a newline create a :
            if not line[:1] in ['\t', '\n']:
                temp_vendor = line.split()[0]
                ids_lib[temp_vendor] = {'name': line[6:-1]}
            if line.startswith('\t\t') or line.startswith('\n'):
                continue
            if line.startswith('\t'):
                ids_lib[temp_vendor][line.split()[0]] = {"name": "{}".format(" ".join(line.split()[1:]))}

        if vendor in ids_lib and device in ids_lib[vendor]:
            return ids_lib[vendor]["name"], ids_lib[vendor][device]["name"]

        if vendor not in ids_lib:
            print("{}:{} not found in {}".format(vendor, device, filepath))
        else:
            if device not in ids_lib[vendor]:
                print("{} found {}; but {} not found in {}".format(vendor, ids_lib[vendor]["name"], device, filepath))

        return 0, 0

    def readfile(self, filename):
        if not os.path.exists(filename):
            return ""
        file = open(filename, "r")
        data = file.read()
        file.close()
        return data

    def is_virtual_machine(self):
        cpuinfo = self.readfile("/proc/cpuinfo").split("\n")
        for line in cpuinfo:
            if line.startswith("flags"):
                return "hypervisor" in line
        return False

    def get_gpu(self):
        glx_vendorid = ""
        glx_string = ""
        glx_driver = ""
        pci_bus = True

        try:
            lspci_command = subprocess.check_output(["lspci", "-n"]).decode("utf-8").strip()
        except Exception as e:
            print("{}".format(e))
            lspci_command = ""

        allgpus = []
        gpus_sys_all = []
        gpus_sys = []
        pci_numids = []

        if len(lspci_command) > 0:
            lspci_command = lspci_command.split("\n")

        for pci in lspci_command:
            pci_slot = pci.split(" ")[0]
            pci_class = pci.split(" ")[1].strip(":")
            pci_id = pci.split(" ")[2]
            pci_vendor, pci_device = pci_id.split(":")
            pci_numids.append({"slot": pci_slot, "class": pci_class, "vendor": pci_vendor, "device": pci_device})

        for pci_numid in pci_numids:
            if pci_numid["class"].startswith("03"):  # 03** graphics hardware
                try:
                    kernel_driver = ""
                    kernel_driver_command = subprocess.check_output(["lspci", "-s", pci_numid["slot"], "-k"]).decode(
                        "utf-8").strip().split("\n")
                    kernel_driver = "{}".format(
                        "".join([x.split(":")[1].strip() for x in kernel_driver_command if "driver" in x and ":" in x]))
                    if kernel_driver == "" or kernel_driver is None:
                        kernel_driver = "{}".format("".join(
                            [x.split(":")[1].strip() for x in kernel_driver_command if "module" in x and ":" in x]))
                except:
                    kernel_driver = "unknown"

                allgpus.append({"slot": pci_numid["slot"], "class": pci_numid["class"],
                                "vendor": pci_numid["vendor"], "device": pci_numid["device"], "driver": kernel_driver,
                                })

        try:
            glxinfo_command = subprocess.check_output(["glxinfo", "-B"]).decode("utf-8").strip()

            glxinfo = [x.strip() for x in glxinfo_command.split("\n") if x != ""]

            for glx in glxinfo:
                if glx.startswith("Vendor:"):
                    glx_vendorid = glx.split("0x")[1].rstrip(")").strip()[:4]
                if glx.startswith("OpenGL renderer string:"):
                    glx_string = glx.split("OpenGL renderer string:")[1].strip()

                glx_driver = "{}".format("".join([gpu["driver"] for gpu in allgpus if gpu["vendor"] == glx_vendorid]))
        except Exception as e:
            print("{}".format(e))

        gpus = [gpu for gpu in allgpus if gpu["vendor"] != glx_vendorid and gpu["vendor"] != "ffff"]

        default_gpu_vendor = ""
        default_gpu_model = ""
        default_gpu_name = glx_string
        default_gpu_driver = glx_driver

        glx_pci_vendor_equal = False

        if len(allgpus) == 1:
            default_gpu_vendor, default_gpu_model = self.get_gpu_name(allgpus[0]["vendor"], allgpus[0]["device"])
            default_gpu_name = "{} {}".format(default_gpu_vendor, default_gpu_model)
            default_gpu_driver = allgpus[0]["driver"]
            gpus = [gpu for gpu in allgpus if gpu["vendor"] != allgpus[0]["vendor"]]

        elif len(allgpus) > 1:
            for allgpu in allgpus:
                if glx_vendorid == allgpu["vendor"]:
                    glx_pci_vendor_equal = True
                    default_gpu_vendor, default_gpu_model = self.get_gpu_name(allgpu["vendor"], allgpu["device"])
                    default_gpu_name = "{} {}".format(default_gpu_vendor, default_gpu_model)

            if not glx_pci_vendor_equal:
                print("glx_pci_vendor_equal is False and allgpus > 1")
                default_gpu_vendor, default_gpu_model = self.get_gpu_name(gpus[0]["vendor"], gpus[0]["device"])
                default_gpu_name = "{} {}".format(default_gpu_vendor, default_gpu_model)
                default_gpu_driver = gpus[0]["driver"]
                gpus = [gpu for gpu in allgpus if gpu["vendor"] != allgpus[0]["vendor"]]

        else:
            pci_bus = False
            gpus_sys_all = self.get_gpu_from_sysclass()
            gpus_sys = deepcopy(gpus_sys_all)
            if len(gpus_sys_all) >= 1:
                default_gpu_name = "{} {}".format(gpus_sys_all[0]["vendor"], gpus_sys_all[0]["model"])
                default_gpu_driver = "{}".format(gpus_sys_all[0]["driver"])
                gpus_sys.pop(0)


        if self.is_virtual_machine():
            default_gpu_name = glx_string
            if len(allgpus) == 1:
                default_gpu_driver = allgpus[0]["driver"]
                gpus = [gpu for gpu in allgpus if gpu["vendor"] != allgpus[0]["vendor"]]

        self.default_gpu.append({"name": "{}".format(default_gpu_name),
                                 "driver": "{}".format(default_gpu_driver)})

        self.glx.append({"name": "{}".format(glx_string),
                         "driver": "{}".format(glx_driver),
                         "vendor": "{}".format(glx_vendorid)})

        if pci_bus:
            for gpu in gpus:
                gpu_vendor, gpu_model = self.get_gpu_name(gpu["vendor"], gpu["device"])
                gpu_name = "{} {}".format(gpu_vendor, gpu_model)
                self.extra_gpu.append({"name": "{}".format(gpu_name),
                                       "driver": "{}".format(gpu["driver"]),
                                       "vendor": "{}".format(gpu["vendor"])})

            for allgpu in allgpus:
                gpu_vendor, gpu_model = self.get_gpu_name(allgpu["vendor"], allgpu["device"])
                gpu_name = "{} {}".format(gpu_vendor, gpu_model)
                self.all_gpu.append({"name": "{}".format(gpu_name),
                                     "driver": "{}".format(allgpu["driver"]),
                                     "slot": "{}".format(allgpu["slot"]),
                                     "class": "{}".format(allgpu["class"]),
                                     "device": "{}".format(allgpu["device"]),
                                     "vendor": "{}".format(allgpu["vendor"])})
        else:
            for gpu_sys in gpus_sys:
                gpu_name = "{} {}".format(gpu_sys["vendor"], gpu_sys["model"])
                self.extra_gpu.append({"name": "{}".format(gpu_name),
                                       "driver": "{}".format(gpu_sys["driver"])})

            for gpu_sys_all in gpus_sys_all:
                gpu_name = "{} {}".format(gpu_sys_all["vendor"], gpu_sys_all["model"])
                self.all_gpu.append({"name": "{}".format(gpu_name),
                                     "driver": "{}".format(gpu_sys_all["driver"])})

        return self.default_gpu, self.extra_gpu, self.glx, self.all_gpu

    def get_gpu_from_sysclass(self):
        gpu_list = []
        for file in os.listdir("/sys/class/drm/"):
            if "-" not in file and file.split("-")[0].rstrip("0123456789") == "card":
                if os.path.isfile("/sys/class/drm/" + file + "/device/modalias"):
                    with open("/sys/class/drm/" + file + "/device/modalias") as modalias_file:
                        modalias = modalias_file.read().strip()
                    device_subtype, device_alias = modalias.split(":", 1)
                    if device_subtype == "of":
                        try:
                            vendor = device_alias.split("C", 1)[-1].split("C", 1)[0].split(",")[0].title()
                            model = device_alias.split("C", 1)[-1].split("C", 1)[0].split(",")[1].title()
                        except:
                            vendor = ""
                            model = ""
                        driver = "-"
                        if os.path.isfile("/sys/class/drm/" + file + "/device/uevent"):
                            with open("/sys/class/drm/" + file + "/device/uevent") as uevent_file:
                                uevent_lines = uevent_file.read().strip().split("\n")
                            for line in uevent_lines:
                                if line.startswith("DRIVER="):
                                    driver = line.split("=")[-1]
                                    break
                        gpu_list.append({"gpu": file, "modalias": modalias, "vendor": vendor, "model": model,
                                         "driver": driver})
        gpu_list = sorted(gpu_list, key=lambda x: x["gpu"])
        print("gpu_sys: {}".format(gpu_list))
        return gpu_list