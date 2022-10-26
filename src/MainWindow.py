import os, subprocess, time
import platform

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk, Gdk, GdkPixbuf

import locale
from locale import gettext as _

import socket
import fcntl
import struct
import threading
import json

from GPU import GPU

# Translation Constants:
APPNAME = "pardus-about"
TRANSLATIONS_PATH = "/usr/share/locale"
# SYSTEM_LANGUAGE = os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)
# locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)

class MainWindow:
    def __init__(self, application):
        # Gtk Builder
        self.builder = Gtk.Builder()

        # Translate things on glade:
        # self.builder.set_translation_domain(APPNAME)

        # Import UI file:
        self.builder.add_from_file(os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade")
        self.builder.connect_signals(self)

        # Window
        self.window = self.builder.get_object("window")
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_application(application)
        self.window.connect("destroy", self.onDestroy)
        self.defineComponents()

        # self.stack_main.set_visible_child_name("loading")

        self.addTurkishFlag()

        thread1 = threading.Thread(target=self.add_gpus_to_ui, args=(self.get_gpu(),))
        thread1.daemon = True
        thread1.start()

        thread2 = threading.Thread(target=self.add_ip_to_ui, args=(self.get_ips(),))
        thread2.daemon = True
        thread2.start()

        self.readSystemInfo()

        # Set application:
        self.application = application

        # Show Screen:
        self.window.show_all()

    # Window methods:
    def onDestroy(self, action):
        self.window.get_application().quit()
    
    def defineComponents(self):
        self.dialog_report_exported = self.builder.get_object("dialog_report_exported")
        self.dialog_gathering_logs = self.builder.get_object("dialog_gathering_logs")

        self.lbl_distro = self.builder.get_object("lbl_distro")
        self.lbl_distro_version = self.builder.get_object("lbl_distro_version")
        self.lbl_distro_codename = self.builder.get_object("lbl_distro_codename")

        self.lbl_user_host = self.builder.get_object("lbl_user_host")
        self.lbl_kernel = self.builder.get_object("lbl_kernel")
        self.lbl_desktop = self.builder.get_object("lbl_desktop")
        self.lbl_cpu = self.builder.get_object("lbl_cpu")
        self.lbl_gpu = self.builder.get_object("lbl_gpu")
        self.lbl_title_gpu = self.builder.get_object("lbl_title_gpu")
        self.lbl_ram = self.builder.get_object("lbl_ram")
        self.lbl_ram_phy = self.builder.get_object("lbl_ram_phy")
        self.lbl_ip_public = self.builder.get_object("lbl_ip_public")
        self.lbl_ip_local = self.builder.get_object("lbl_ip_local")

        self.box_extra_gpu = self.builder.get_object("box_extra_gpu")

        self.popover_menu = self.builder.get_object("popover_menu")

        self.dialog_about = self.builder.get_object("dialog_about")
        self.dialog_about.set_program_name(_("Pardus About"))

        self.bayrak = self.builder.get_object("bayrak")
        self.img_bayrak = self.builder.get_object("img_bayrak")

        self.lbl_distro_codename.grab_focus()

        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.dialog_about.set_version(version)
        except:
            pass

    def addTurkishFlag(self):
        self.click_count = 0
        self.last_click_timestamp = 0
        
        pixbuf = GdkPixbuf.PixbufAnimation.new_from_file(os.path.dirname(os.path.abspath(__file__)) + "/../bayrak.gif")

        def waving_flag(it):
            # it is iterator
            self.img_bayrak.props.pixbuf = it.get_pixbuf()
            it.advance()

            GLib.timeout_add(it.get_delay_time(), waving_flag, it)
        
        GLib.timeout_add(0, waving_flag, pixbuf.get_iter())

    def readSystemInfo(self):
        output = subprocess.check_output([os.path.dirname(os.path.abspath(__file__)) + "/get_system_info.sh"]).decode("utf-8")
        lines = output.splitlines()
        
        self.lbl_distro.set_label(lines[0])
        self.lbl_distro_version.set_label(lines[1])
        if lines[2] == "yirmibir":
            lines[2] =  "Dolunay"
        self.lbl_distro_codename.set_label(lines[2])

        self.lbl_user_host.set_label(lines[3])
        self.lbl_kernel.set_label(lines[4])
        self.lbl_desktop.set_label(lines[5])
        # if lines[7] == "0":
        #     self.lbl_cpu.set_label(lines[6])
        # else:
        #     ghz = "{:.2f}".format(float(lines[7])/1000000)
        #     self.lbl_cpu.set_label(lines[6] + " (" + ghz  + "GHz)")

        self.lbl_cpu.set_label("{}".format(self.get_cpu()))

        total_physical_ram, total_ram = self.get_ram_size()
        self.lbl_ram.set_label(self.beauty_size(total_ram))
        self.lbl_ram_phy.set_markup("( {}:  {} )".format(_("Physical RAM"), self.beauty_size(total_physical_ram)))

    def add_gpus_to_ui(self, gpus):

        default_gpu, extra_gpu = gpus

        self.lbl_gpu.set_markup("{} ( {} )".format(default_gpu[0]["name"], default_gpu[0]["driver"]))

        if extra_gpu:
            self.lbl_title_gpu.set_markup("<b>GPU 1:</b>")
            GLib.idle_add(self.box_extra_gpu.set_visible, True)
            count = 2
            for extra in extra_gpu:
                box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
                gputitle = Gtk.Label.new()
                gputitle.set_selectable(True)
                gputitle.set_markup("<b>GPU {}:</b>".format(count))
                count += 1
                gpulabel = Gtk.Label.new()
                gpulabel.set_line_wrap(True)
                gpulabel.set_line_wrap_mode(Gtk.WrapMode.WORD)
                gpulabel.set_max_width_chars(55)
                gpulabel.set_selectable(True)
                gpulabel.set_markup("{} ( {} )".format(extra["name"], extra["driver"]))

                box.pack_start(gputitle, False, True, 0)
                box.pack_start(gpulabel, False, True, 0)

                self.box_extra_gpu.pack_start(box, False, True, 0)

            # self.box_extra_gpu.show_all()
            GLib.idle_add(self.box_extra_gpu.show_all)
        else:
            GLib.idle_add(self.box_extra_gpu.set_visible, False)


    def add_ip_to_ui(self, ip):

        local, public = ip
        self.lbl_ip_public.set_label("{}".format(public.strip()))
        lan = ""
        for lip in local:
            if lip[1] != "lo":
                lan += "{} ({})\n".format(lip[0], lip[1])
        lan = lan.rstrip("\n")
        self.lbl_ip_local.set_markup("{}".format(lan))

    def beauty_size(self, size):
        if type(size) is int:
            size = size / 1024
            if size > 1048576:
                size = "{:.1f} GiB".format(float(size / 1048576))
            elif size > 1024:
                size = "{:.1f} MiB".format(float(size / 1024))
            else:
                size = "{:.1f} KiB".format(float(size))
            return size
        return "size not found"

    def get_ram_size(self):
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
                if os.path.isdir("/sys/devices/system/memory/" + file) and file.startswith("memory"):
                    with open("/sys/devices/system/memory/" + file + "/online") as online:
                        memory_on_off = online.read().strip()
                    if memory_on_off == "1":
                        total_online_mem = total_online_mem + block_size
                    if memory_on_off == "0":
                        total_offline_mem = total_offline_mem + block_size
            total_physical_ram = (total_online_mem + total_offline_mem)
        except Exception as e:
            print("Exception on /sys/devices/system/memory/block_size_bytes : {}".format(e))

        # total ram size
        try:
            with open("/proc/meminfo") as meminfo:
                meminfo_lines = meminfo.read().split("\n")
            for line in meminfo_lines:
                if "MemTotal:" in line:
                    total_ram = int(line.split()[1]) * 1024
        except Exception as e:
            print("Exception on /proc/meminfo : {}".format(e))

        return total_physical_ram, total_ram

    def get_gpu(self):

        self.GPU = GPU()

        default_gpu, extra_gpu, glx_gpu, all_gpu = self.GPU.get_gpu()

        print(default_gpu)
        print(extra_gpu)
        print(glx_gpu)
        print(all_gpu)

        return default_gpu, extra_gpu

    def get_cpu(self):

        file = self.readfile("/proc/cpuinfo")
        name = ""
        core = 0
        for line in file.splitlines():
            if line.startswith("model name"):
                name = line.split(":")[1].strip()
            if line.startswith("processor"):
                core += 1
        if core != 0:
            core = "x{}".format(core)
        if name != "":
            name = "{} {}".format(name, core)
        else:
            lscpu_command = json.loads(subprocess.check_output(["lscpu", "-J"]).decode("utf-8"))
            model = ""
            vendor = ""
            core = ""
            arch = ""
            mhz = ""
            for fields in lscpu_command["lscpu"]:
                if fields["field"] == "Model name:":
                    model = fields["data"]
                if fields["field"] == "Vendor ID:":
                    vendor = fields["data"]
                if fields["field"] == "CPU(s):":
                    core = fields["data"]
                if fields["field"] == "Architecture:":
                    arch = fields["data"]
                if fields["field"] == "CPU max MHz:":
                    mhz = fields["data"]
            try:
                if "," in mhz:
                    if "." in mhz:
                        mhz = mhz.replace(",","")
                    else:
                        mhz = mhz.replace(",",".")
                mhz = "@ {:.2f} GHz".format(float(mhz) / 1000) if mhz != "" else ""
            except Exception as e:
                print("{}".format(e))
                mhz = ""

            core = "x{}".format(core) if core != "" else ""
            arch = "({})".format(arch) if arch != "" else ""

            if "ghz" not in model.lower() and mhz != "":
                name = "{} {} {} {} {}".format(vendor, model, mhz, core, arch)
            else:
                name = "{} {} {} {}".format(vendor, model, core, arch)
        return name

    def readfile(self, filename):
        if not os.path.exists(filename):
            return ""
        file = open(filename, "r")
        data = file.read()
        file.close()
        return data

    def get_ip(self):
        try:
            import requests
        except Exception:
            return '0.0.0.0'
        # Check internet connection from server list

        servers = open(os.path.dirname(os.path.abspath(__file__)) + "/../data/servers.txt", "r").read().split("\n")
        for server in servers:
            try:
                r = requests.get(server)
                if r.content:
                    return r.content.decode("utf-8")
            except:
                continue
        return '0.0.0.0'

    # https://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-from-a-nic-network-interface-controller-in-python
    def get_local_ip(self):
        ret = []
        for ifname in os.listdir("/sys/class/net"):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                ip = socket.inet_ntoa(fcntl.ioctl(
                    s.fileno(),
                    0x8915,  # SIOCGIFADDR
                    struct.pack('256s', ifname[:15].encode("utf-8"))
                )[20:24])
                ret.append((ip, ifname))
            except Exception as e:
                print("{}: {}".format(ifname, e))
        return ret

    def get_ips(self):
        return self.get_local_ip(), self.get_ip()

    # Signals:
    def on_menu_aboutapp_clicked(self, button):
        self.popover_menu.popdown()
        self.dialog_about.run()
        self.dialog_about.hide()

    def on_menu_btn_export_clicked(self, btn):
        self.popover_menu.popdown()
        self.dialog_gathering_logs.show_all()
        currentPath = os.path.dirname(os.path.abspath(__file__))

        self.finishedProcesses = 0

        def onFinished(source, condition):
            self.dialog_gathering_logs.hide()
            self.dialog_report_exported.run()
            self.dialog_report_exported.hide()

        def onLogsDumped(source, condition):
            if condition != 0:
                self.dialog_gathering_logs.hide()
                return
            pid3, _, _, _ = GLib.spawn_async([currentPath + "/copy_to_desktop.sh"],
                                    flags=GLib.SPAWN_LEAVE_DESCRIPTORS_OPEN | GLib.SPAWN_DO_NOT_REAP_CHILD)
            GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid3, onFinished)
        
        def onSystemInfoDumped(source, condition):
            pid2, _, _, _ = GLib.spawn_async(["pkexec", currentPath + "/dump_logs.sh"],
                                    flags=GLib.SPAWN_SEARCH_PATH | GLib.SPAWN_LEAVE_DESCRIPTORS_OPEN | GLib.SPAWN_DO_NOT_REAP_CHILD)
            GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid2, onLogsDumped)

        pid1, _, _, _ = GLib.spawn_async([currentPath + "/dump_system_info.sh"],
                                    flags=GLib.SPAWN_LEAVE_DESCRIPTORS_OPEN | GLib.SPAWN_DO_NOT_REAP_CHILD)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid1, onSystemInfoDumped)
    
    def on_btn_pardus_logo_button_press_event(self, btn, event):
        timestamp = lambda: int(round(time.time() * 1000)) # milliseconds

        if event.type == Gdk.EventType._2BUTTON_PRESS:

            if timestamp() - self.last_click_timestamp < 800:
                self.click_count += 1
            else:
                self.click_count = 1
            
            self.last_click_timestamp = timestamp()
        
        if self.click_count >= 2:
            self.click_count = 0

            self.bayrak.popup()
    
