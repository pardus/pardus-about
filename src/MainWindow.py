import os, subprocess, time
import queue
import platform

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Soup", "2.4")
from gi.repository import GLib, Gio, Gtk, Gdk, GdkPixbuf, Soup

import locale
from locale import gettext as _

import socket
import fcntl
import struct
import threading
import utils

# Translation Constants:
APPNAME = "pardus-about"
TRANSLATIONS_PATH = "/usr/share/locale"
# SYSTEM_LANGUAGE = os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)
# locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)

print(utils.get_os_info())


class MainWindow:
    def __init__(self, application):
        # Gtk Builder
        self.builder = Gtk.Builder()

        # Translate things on glade:
        # self.builder.set_translation_domain(APPNAME)

        # Import UI file:
        self.builder.add_from_file(
            os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        )
        self.builder.connect_signals(self)

        # Window
        self.window = self.builder.get_object("window")
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_application(application)
        self.window.connect("destroy", self.onDestroy)
        self.defineComponents()

        # self.stack_main.set_visible_child_name("loading")

        self.addTurkishFlag()
        self.add_gpus_to_ui()

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

        self.img_llvm = self.builder.get_object("img_llvm")

        self.img_publicip = self.builder.get_object("img_publicip")

        self.box_extra_gpu = self.builder.get_object("box_extra_gpu")

        self.popover_menu = self.builder.get_object("popover_menu")

        self.dialog_about = self.builder.get_object("dialog_about")
        self.dialog_about.set_program_name(_("Pardus About"))
        if self.dialog_about.get_titlebar() is None:
            about_headerbar = Gtk.HeaderBar.new()
            about_headerbar.set_show_close_button(True)
            about_headerbar.set_title(_("About Pardus About"))
            about_headerbar.pack_start(
                Gtk.Image.new_from_icon_name("pardus-about", Gtk.IconSize.LARGE_TOOLBAR)
            )
            about_headerbar.show_all()
            self.dialog_about.set_titlebar(about_headerbar)

        self.bayrak = self.builder.get_object("bayrak")
        self.img_bayrak = self.builder.get_object("img_bayrak")

        self.img_background = self.builder.get_object("img_background")
        self.img_distro = self.builder.get_object("img_distro")

        self.lbl_distro_codename.grab_focus()

        self.public_ip = "0.0.0.0"
        self.urls = queue.Queue()
        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(
                os.path.dirname(os.path.abspath(__file__)) + "/__version__"
            ).readline()
            self.dialog_about.set_version(version)
        except:
            pass

    def addTurkishFlag(self):
        self.click_count = 0
        self.last_click_timestamp = 0

        pixbuf = GdkPixbuf.PixbufAnimation.new_from_file(
            os.path.dirname(os.path.abspath(__file__)) + "/../bayrak.gif"
        )

        def waving_flag(it):
            # it is iterator
            self.img_bayrak.props.pixbuf = it.get_pixbuf()
            it.advance()

            GLib.timeout_add(it.get_delay_time(), waving_flag, it)

        GLib.timeout_add(0, waving_flag, pixbuf.get_iter())

    def readSystemInfo(self):
        output = subprocess.check_output(
            [os.path.dirname(os.path.abspath(__file__)) + "/get_system_info.sh"]
        ).decode("utf-8")
        lines = output.splitlines()

        self.lbl_distro.set_label(lines[0])

        if lines[0].lower() != "pardus":
            try:
                pixbuf = Gtk.IconTheme.get_default().load_icon(
                    "emblem-{}".format(lines[0].lower()), 120, Gtk.IconLookupFlags(16)
                )
            except Exception as e:
                try:
                    pixbuf = Gtk.IconTheme.get_default().load_icon(
                        "distributor-logo", 120, Gtk.IconLookupFlags(16)
                    )
                except Exception as e:
                    try:
                        pixbuf = Gtk.IconTheme.get_default().load_icon(
                            "image-missing", 120, Gtk.IconLookupFlags(16)
                        )
                    except Exception as e:
                        pixbuf = None

            if pixbuf is not None:
                self.img_distro.set_from_pixbuf(pixbuf)

        self.lbl_distro_version.set_label(lines[1])
        if lines[2] == "yirmibir":
            lines[2] = "Dolunay"
            self.img_background.set_from_file(
                os.path.dirname(os.path.abspath(__file__)) + "/../bluebackground-21.png"
            )
        elif lines[2] == "yirmiuc":
            lines[2] = "Ay Yıldız"
        self.lbl_distro_codename.set_label(lines[2])

        self.lbl_user_host.set_label(lines[3])
        kernel, release = utils.get_kernel()
        self.lbl_kernel.set_label(f"{kernel} {release}")
        desktop_environment, desktop_environment_version = (
            utils.get_desktop_environment()
        )

        self.lbl_desktop.set_label(
            f"{desktop_environment} {desktop_environment_version}"
        )
        # if lines[7] == "0":
        #     self.lbl_cpu.set_label(lines[6])
        # else:
        #     ghz = "{:.2f}".format(float(lines[7])/1000000)
        #     self.lbl_cpu.set_label(lines[6] + " (" + ghz  + "GHz)")
        cpu, cores = utils.get_cpu()
        self.lbl_cpu.set_label("{} x{}".format(cpu, cores))

        total_physical_ram, total_ram = utils.get_ram_size()
        self.lbl_ram.set_label(self.beauty_size(total_ram))
        if total_physical_ram != 0:
            self.lbl_ram_phy.set_markup(
                "({}:  {})".format(
                    _("Physical RAM"), self.beauty_size(total_physical_ram)
                )
            )
        else:
            self.lbl_ram_phy.set_label("")

    def add_gpus_to_ui(self):
        gpus = utils.get_gpu()
        self.lbl_gpu.set_markup("{} ({})".format(gpus[0]["device"], gpus[0]["driver"]))
        try:
            if "llvmpipe" in gpus[0]["driver"].lower():
                llvm = True
            else:
                llvm = False
        except Exception as e:
            print("llvmpipe detect err: {}".format(e))
            llvm = False

        self.lbl_gpu.set_markup("{} ({})".format(gpus[0]["device"], gpus[0]["driver"]))

        GLib.idle_add(self.img_llvm.set_visible, llvm)
        if len(gpus) > 1:
            self.lbl_title_gpu.set_markup("<b>GPU 1:</b>")
            GLib.idle_add(self.box_extra_gpu.set_visible, True)
            count = 2
            for index, extra in enumerate(gpus[1:]):
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
                gpulabel.set_markup("{} ({})".format(extra["device"], extra["driver"]))

                box.pack_start(gputitle, False, True, 0)
                box.pack_start(gpulabel, False, True, 0)

                self.box_extra_gpu.pack_start(box, False, True, 0)

            # self.box_extra_gpu.show_all()
            GLib.idle_add(self.box_extra_gpu.show_all)
        else:
            GLib.idle_add(self.box_extra_gpu.set_visible, False)

    def add_ip_to_ui(self, ip):

        local, public = ip
        self.lbl_ip_public.set_text("{}".format(len(public.strip()) * "*"))
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

    def readfile(self, filename):
        if not os.path.exists(filename):
            return ""
        file = open(filename, "r")
        data = file.read()
        file.close()
        return data

    def get_ip(self):
        servers = (
            open(
                os.path.dirname(os.path.abspath(__file__)) + "/../data/servers.txt", "r"
            )
            .read()
            .split("\n")
        )
        for server in servers:
            self.urls.put(server)
        self.process_next()
        return self.public_ip

    def process_next(self):
        if not self.urls.empty():
            url = self.urls.get()
            self.get(url)

    def on_message_finished(self, session, message, user_data):
        response_body = message.response_body.flatten().get_data()
        url = response_body.decode("utf-8").strip()
        if self.is_valid_ip(url):
            self.public_ip = url
            # print(response_body)
        else:
            self.process_next()  # Proceed to the next download

    def get(self, url):
        session = Soup.Session.new()
        message = Soup.Message.new("GET", url)
        session.queue_message(message, self.on_message_finished, None)

    def is_valid_ip(self, address):
        parts = address.split(".")
        if len(parts) != 4:
            return False

        for part in parts:
            if not part.isdigit():
                return False
            num = int(part)
            if num < 0 or num > 255:
                return False
        return True

    # https://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-from-a-nic-network-interface-controller-in-python
    def get_local_ip(self):
        ret = []
        for ifname in os.listdir("/sys/class/net"):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                ip = socket.inet_ntoa(
                    fcntl.ioctl(
                        s.fileno(),
                        0x8915,  # SIOCGIFADDR
                        struct.pack("256s", ifname[:15].encode("utf-8")),
                    )[20:24]
                )
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
            pid3, _, _, _ = GLib.spawn_async(
                [currentPath + "/copy_to_desktop.sh"],
                flags=GLib.SPAWN_LEAVE_DESCRIPTORS_OPEN | GLib.SPAWN_DO_NOT_REAP_CHILD,
            )
            GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid3, onFinished)

        def onSystemInfoDumped(source, condition):
            pid2, _, _, _ = GLib.spawn_async(
                ["pkexec", currentPath + "/dump_logs.sh"],
                flags=GLib.SPAWN_SEARCH_PATH
                | GLib.SPAWN_LEAVE_DESCRIPTORS_OPEN
                | GLib.SPAWN_DO_NOT_REAP_CHILD,
            )
            GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid2, onLogsDumped)

        pid1, _, _, _ = GLib.spawn_async(
            [currentPath + "/dump_system_info.sh"],
            flags=GLib.SPAWN_LEAVE_DESCRIPTORS_OPEN | GLib.SPAWN_DO_NOT_REAP_CHILD,
        )
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid1, onSystemInfoDumped)

    def on_btn_pardus_logo_button_press_event(self, btn, event):
        timestamp = lambda: int(round(time.time() * 1000))  # milliseconds

        if event.type == Gdk.EventType._2BUTTON_PRESS:

            if timestamp() - self.last_click_timestamp < 800:
                self.click_count += 1
            else:
                self.click_count = 1

            self.last_click_timestamp = timestamp()

        if self.click_count >= 2:
            self.click_count = 0

            self.bayrak.popup()

    def on_event_publicip_button_press_event(self, widget, event):
        if self.img_publicip.get_icon_name().icon_name == "view-conceal-symbolic":
            self.img_publicip.set_from_icon_name(
                "view-reveal-symbolic", Gtk.IconSize.BUTTON
            )
            self.lbl_ip_public.set_text("{}".format(len(self.public_ip) * "*"))
        else:
            self.img_publicip.set_from_icon_name(
                "view-conceal-symbolic", Gtk.IconSize.BUTTON
            )
            self.lbl_ip_public.set_text(self.public_ip)
