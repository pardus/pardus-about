import os
import subprocess
import distro
import socket
import getpass
import platform
import tarfile
import shutil
from gi.repository import GLib

class Get_system_info:
    def __init__(self):
        self.path = "/tmp/pardus_system_report"
        self.distro_name = distro.name()
        self.distro_version = distro.version()
        self.distro_codename = distro.codename()
        self.user = getpass.getuser()
        self.host_name = f"{self.user}@{socket.gethostname()}"
        self.kernel = platform.uname().release
        self.desktop_env = os.environ.get("XDG_CURRENT_DESKTOP")
        self.hide_dialog=None

    def get_ui_data(self):
        return [self.distro_name, self.distro_version, self.distro_codename,
                self.host_name, self.kernel, self.desktop_env]

    def start_system_report(self):
        self.generate_system_info_file()
        self.compress_file()
        GLib.idle_add(self.hide_dialog)


    def compress_file(self):
        file_name = "pardus_sistem_raporu" if os.environ.get(
            "LANG") == 'tr_TR.UTF-8' else "pardus_system_report" 
        try:
            tar_file_path = os.path.join(self.get_desktop_path(), f"{file_name}.tar.gz")
            with tarfile.open(tar_file_path, "w:gz") as tar:
                tar.add(self.path, arcname=os.path.basename(self.path))
        except Exception as e:
            print(f"Hata: {e}")


    def generate_system_info_file(self):
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        os.makedirs(self.path)
        files = ["/var/log/auth.log", "/var/log/boot.log", "/var/log/daemon.log",
                 "/var/log/dpkg.log", "/var/log/kern.log", "/var/log/syslog", "/var/log/user.log",
                 "/etc/hosts", "/etc/apt/sources.list"]
        self.get_system_info_file()

        self.write_to_file(f"{self.path}/dmesg",
                           args_str=self.get_cmd("pkexec dmesg"))
        self.write_to_file(f"{self.path}/journalctl",
                           args_str=self.get_cmd("journalctl -q -n 1000"))
        self.write_to_file(f"{self.path}/lspci",
                           args_str=self.get_cmd("lspci -vvv"))
        self.write_to_file(f"{self.path}/lsusb",
                           args_str=self.get_cmd("lsusb"))
        self.write_to_file(f"{self.path}/apt_list",
                           args_str=self.get_cmd("apt list"))

        self.copy_files(files)
        self.copy_files(["/etc/apt/sources.list.d"], is_folder=True)

    def get_system_info_file(self):  # ? dump_system_info.sh
        data = (f"{self.distro_name} {self.distro_version} ({self.distro_codename})",
                self.host_name, f"Kernel: {self.kernel}", f"Desktop: {self.desktop_env}",
                f"CPU: {self.get_cpu_info()}", f"CPU: {self.get_gpu_info()}",
                f"Memory: {self.get_ram_info()}")
        self.write_to_file("/tmp/pardus_system_report/system_info", data)

    def get_cmd(self, command: str):
        try:
            output = subprocess.check_output(
                command.split()).decode("utf-8")
            return output
        except subprocess.CalledProcessError:
            return "Unknown"

    def copy_files(self, files: list, is_folder=False):
        try:
            if not is_folder:
                shell_command = (
                    f"""
                    pkexec bash -c '
                    cp {' '.join(files)} {self.path} && 
                    cd {self.path} &&
                    chown {self.user}:{self.user} *'
                    """
                )
                subprocess.run(shell_command, shell=True)
            else:
                for f in files:
                    p = f.split("/")[-1]
                    #print(f"{self.path}/{p}", f.split("/"))
                    shutil.copytree(f, f"{self.path}/{p}")
        except Exception as e:
            print(f"{e}")

    def get_gpu_info(self):
        output = self.get_cmd("glxinfo").split("\n")
        searched = "OpenGL renderer string"
        result = list(filter(lambda val: searched in val, output))
        return result[0].replace("OpenGL renderer string: ", "")

    def get_cpu_info(self):
        infos = open("/proc/cpuinfo", "r").read().split("\n")
        cpu_info = list(filter(lambda val: "model name" in val, infos))[
            0].split(":")[-1].strip()
        cpu_core = list(filter(lambda val: "siblings" in val, infos))[
            0].split(":")[-1].strip()
        return cpu_info + " *" + cpu_core

    def get_ram_info(self):
        infos = open("/proc/meminfo", "r").read().split("\n")
        ram_info = list(filter(lambda val: "MemTotal:" in val, infos))[
            0].split()[-2]
        ram_info = int(ram_info)/(1024 ** 2)
        return f"{ram_info:.2f} Gb"
    
    def get_desktop_path(self):
        return self.get_cmd("xdg-user-dir DESKTOP").split()[0]

    def write_to_file(self, path: str, args: tuple = None, args_str: str = None):
        file = "\n".join(args) if args_str == None else args_str
        with open(path, "w") as f:
            f.write(file)
