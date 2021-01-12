import os, subprocess

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk

import locale
from locale import gettext as tr

# Translation Constants:
APPNAME = "pardus-about"
TRANSLATIONS_PATH = "/usr/share/locale"
SYSTEM_LANGUAGE = os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)
locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)

class MainWindow:
    def __init__(self, application):
        # Gtk Builder
        self.builder = Gtk.Builder()

        # Translate things on glade:
        self.builder.set_translation_domain(APPNAME)

        # Import UI file:
        self.builder.add_from_file(os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade")
        self.builder.connect_signals(self)

        # Window
        self.window = self.builder.get_object("window")
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_application(application)
        self.window.connect("destroy", self.onDestroy)
        self.defineComponents()

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
        self.lbl_ram = self.builder.get_object("lbl_ram")

    def readSystemInfo(self):
        output = subprocess.check_output([os.path.dirname(os.path.abspath(__file__)) + "/get_system_info.sh"]).decode("utf-8")
        lines = output.splitlines()
        
        self.lbl_distro.set_label(lines[0])
        self.lbl_distro_version.set_label(lines[1])
        self.lbl_distro_codename.set_label(lines[2])

        self.lbl_user_host.set_label(lines[3])
        self.lbl_kernel.set_label(lines[4])
        self.lbl_desktop.set_label(lines[5])
        if lines[7] == "0":
            self.lbl_cpu.set_label(lines[6])
        else:
            ghz = "{:.2f}".format(float(lines[7])/1000000)
            self.lbl_cpu.set_label(lines[6] + " (" + ghz  + "GHz)")
        self.lbl_gpu.set_label(lines[8])
        self.lbl_ram.set_label(lines[9] + "GB")

    # Signals:
    def on_btn_export_report_clicked(self, btn):
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

        

        
        
