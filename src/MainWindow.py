import json
import os
import gi
import re
import requests
import pwd
import grp

gi.require_version("Gtk", "3.0")
import locale
from locale import gettext as _

from gi.repository import Gdk, Gio, GLib, Gtk

from util import (
    ComputerManager,
    HardwareDetector,
    OSManager,
    network,
    SystemReportManager,
    HostnameManager,
)
from widget.HardwareDetailRow import HardwareDetailRow
from widget.HardwareGridCell import HardwareGridCell

import ActionsAsk

# Translation Constants:
APPNAME = "pardus-about"
TRANSLATIONS_PATH = "/usr/share/locale"

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)

HARDWARE_API_DOMAIN = "https://donanim.pardus.org.tr"
HARDWARE_API = f"{HARDWARE_API_DOMAIN}/api/v1"


class MainWindow:
    is_hardware_details_visible = False

    def __init__(self, application):
        self.define_variables()

        # Gtk Builder
        self.builder = Gtk.Builder()

        self.load_css(os.path.dirname(os.path.abspath(__file__)) + "/../css/about.css")

        # Translate things on glade:
        self.builder.set_translation_domain(APPNAME)

        # Import UI file:
        self.builder.add_from_file(
            os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        )
        self.builder.connect_signals(self)

        # Window
        self.window = self.builder.get_object("ui_main_window")
        self.window.set_application(application)

        # Set application:
        self.application = application

        # Global Definitions:
        self.define_components()

        self.read_pardus_info()

        task = Gio.Task.new(callback=self.on_read_hardware_info_finish)
        task.run_in_thread(self.read_hardware_info)

        self.define_version()

        self.control_args()

        # Show Screen:
        self.window.show_all()

    def define_version(self):
        version = "0.0.0"
        try:
            with open(
                os.path.dirname(os.path.abspath(__file__)) + "/../__version__"
            ) as f:
                version = f.readline().strip()
        except:
            print("Failed to fetch version")

        self.ui_about_dialog.set_version(version)

    @staticmethod
    def load_css(css_file_path):
        css_provider = Gtk.CssProvider()

        try:
            css_provider.load_from_path(css_file_path)
        except GLib.Error as e:
            print(f"Error loading CSS file '{css_file_path}': {e}")
            return

        screen = Gdk.Screen.get_default()

        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def define_components(self):
        def UI(str):
            return self.builder.get_object(str)

        self.ui_main_window = UI("ui_main_window")
        self.ui_main_stack = UI("ui_main_stack")
        self.ui_info_stack = UI("ui_info_stack")
        self.ui_report_box = UI("ui_report_box")
        self.ui_hardware_info_button = UI("ui_hardware_info_button")
        self.ui_display_report_button = UI("ui_display_report_button")
        self.ui_copy_report_btn = UI("ui_copy_report_btn")
        self.ui_submit_report_btn = UI("ui_submit_report_btn")
        self.ui_hardware_grid = UI("ui_hardware_grid")
        self.ui_hardware_details_box = UI("ui_hardware_details_box")

        # Hostname Edit
        self.ui_edit_hostname_popover_title_label = UI(
            "ui_edit_hostname_popover_title_label"
        )
        self.ui_edit_hostname_popover = UI("ui_edit_hostname_popover")
        self.ui_edit_hostname_entry = UI("ui_edit_hostname_entry")
        self.ui_edit_hostname_btn = UI("ui_edit_hostname_btn")
        self.ui_edit_hostname_ok_btn = UI("ui_edit_hostname_ok_btn")
        self.ui_edit_hostname_btn.set_sensitive(self.is_user_in_sudo_group())

        self.ui_about_dialog = UI("ui_about_dialog")
        self.ui_popover_menu = UI("ui_popover_menu")
        self.ui_notification_popover = UI("ui_notification_popover")

        self.ui_distro_id_label = UI("ui_distro_id_label")
        self.ui_distro_version_label = UI("ui_distro_version_label")
        self.ui_distro_codename_label = UI("ui_distro_codename_label")
        self.ui_computer_name_label = UI("ui_computer_name_label")
        self.ui_username_label = UI("ui_username_label")
        self.ui_hostname_label = UI("ui_hostname_label")

        # Submit
        self.ui_submit_window = UI("ui_submit_window")
        # prevent destroying the window on close clicked
        self.ui_submit_window.connect("delete-event", lambda w, e: w.hide() or True)
        self.ui_submit_lbl = UI("ui_submit_lbl")
        self.ui_submit_stack = UI("ui_submit_stack")

        # Gathering Logs Popup
        self.ui_gathering_logs_popup = UI("ui_gathering_logs_popup")
        self.ui_gathering_logs_popup.connect(
            "delete-event", lambda w, e: w.hide() or True
        )
        self.ui_gathering_logs_stack = UI("ui_gathering_logs_stack")

    def define_variables(self):
        self.computer_manager = None

    def control_args(self):
        if "hardware" in self.application.args.keys():
            self.is_hardware_details_visible = True

        self.window.present()

    def get_user_groups(self, username):
        try:
            user_info = pwd.getpwnam(username)
            primary_gid = user_info.pw_gid
            group_ids = os.getgrouplist(username, primary_gid)
            group_names = [grp.getgrgid(id).gr_name for id in group_ids]

            return group_names
        except KeyError:
            print(f"User {username} not found")
            return []
        except PermissionError:
            print("Permission denied")
            return []

    def is_user_in_sudo_group(self):
        username = os.getlogin()
        groups = self.get_user_groups(username)
        return "sudo" in groups

    def read_pardus_info(self):
        self.os_info = OSManager.get_os_info()
        self.ui_distro_id_label.set_text(self.os_info["os_id"].title())
        self.ui_distro_version_label.set_text(self.os_info["os_version_id"])
        codename_map = {
            "yirmibir": "Dolunay",
            "yirmiuc": "Ay Yıldız",
            "yirmibes": "Bilge",
        }
        raw_name = self.os_info.get("os_codename", "")
        display_name = codename_map.get(raw_name, raw_name)
        self.ui_distro_codename_label.set_text(f"{display_name}")

        self.ui_username_label.set_text(f"{GLib.get_user_name()}")
        self.ui_username_label.set_tooltip_text(f"{GLib.get_user_name()}")

        self.ui_hostname_label.set_text(self.os_info["hostname"].lower())
        self.ui_hostname_label.set_tooltip_text(self.os_info["hostname"].lower())
        return

    def read_hardware_info(self, task, source_object, task_data, cancellable):
        # Lazy Init PCI & USB devices information singleton
        self.computer_manager = ComputerManager.ComputerManager()
        self.hardware_info = HardwareDetector.get_hardware_info()

        task.return_boolean(True)

    def fetch_public_ip(self, task, source_object, task_data, cancellable):
        self.public_ip = network.get_wan_ip()

        task.return_boolean(True)

    def validate_hostname(self, old_hostname, new_hostname):
        # is empty or unchanged
        if not new_hostname or old_hostname == new_hostname:
            return False

        # is valid hostname
        if (
            not re.match(r"^[A-Za-z0-9][A-Za-z0-9-]*$", new_hostname)
            or len(new_hostname) > 64
        ):
            return False

        return True

    # === Fill Pages ===
    def fill_main_page(self):
        def label_from_fields(devices, fields, skip_if_type_none=False):
            """Builds text safely without trailing newline."""
            if not devices:
                return _("Device not found")

            items = []

            for device in devices:
                if skip_if_type_none and device.get("type") is None:
                    continue

                values = []
                for f in fields:
                    values.append(str(device.get(f, "")))

                text = " ".join(values).strip()
                if text:
                    items.append(text)

            if not items:
                return _("Device not found")

            return "\n".join(items)

        def sanitize_local_ip(ip_list):
            """Formats list of (ip, iface) tuples"""
            try:
                if not ip_list:
                    return _("Unknown")

                items = []
                for ip, iface in ip_list:
                    # Skip loopback
                    if iface == "lo":
                        continue

                    iface_str = str(iface) if iface else ""
                    ip_str = str(ip) if ip else ""

                    line = f"{iface_str} {ip_str}".strip()
                    if line:
                        items.append(line)

                # If everything was filtered out → not found
                if not items:
                    return _("Unknown")

                return "\n".join(items)

            except Exception as e:
                print("ip list error:", e)
                return _("Unknown")

        # grid loop indexes
        ix = 0
        iy = 0
        max_x = 2

        def add_to_grid(child):
            nonlocal ix, iy, max_x
            self.ui_hardware_grid.attach(child, ix, iy, 1, 1)

            ix = ix + 1
            if ix >= max_x:
                iy = iy + 1
                ix = 0

        hw = self.hardware_info
        pc = self.computer_manager

        cells = [
            # format: ["icon", "title", "value"]
            # Kernel
            ["tux", _("Kernel"), self.os_info["kernel"]],
            # Desktop
            [
                "pardus-about-desktop",
                _("Desktop"),
                f"{self.os_info['desktop']} {self.os_info['desktop_version']} ({self.os_info['display']})",
            ],
            # Processor
            ["pardus-about-processor", _("Processor"), pc.get_processor_info()["name"]],
            # Graphics
            [
                "pardus-about-graphics",
                _("Graphics"),
                label_from_fields(hw.get("graphics", []), ["vendor", "name"]),
            ],
            # Memory
            ["pardus-about-memory", _("Memory"), pc.get_memory_summary()],
            # Storage
            [
                "pardus-about-storage",
                _("Storage"),
                label_from_fields(
                    hw.get("storage", []), ["size", "model"], skip_if_type_none=True
                ),
            ],
            # Bluetooth
            [
                "pardus-about-bluetooth",
                _("Bluetooth"),
                label_from_fields(hw.get("bluetooth", []), ["vendor", "name"]),
            ],
            # Audio
            [
                "pardus-about-audio",
                _("Audio"),
                label_from_fields(hw.get("audio", []), ["vendor", "name"]),
            ],
            # Wifi
            [
                "pardus-about-wifi",
                _("Wifi"),
                label_from_fields(hw.get("wifi", []), ["name"]),
            ],
            # Ethernet
            [
                "pardus-about-ethernet",
                _("Ethernet"),
                label_from_fields(hw.get("ethernet", []), ["name"]),
            ],
        ]

        for i in cells:
            add_to_grid(HardwareGridCell(i[0], i[1], i[2]))

        # Private IP
        add_to_grid(
            HardwareGridCell(
                "pardus-about-ethernet",
                _("Private IP"),
                sanitize_local_ip(network.get_local_ip()),
                can_hide=True,
            )
        )

        # Public IP
        # Fill IP address later with: fetch_public_ip
        self.public_ip_cell = HardwareGridCell(
            "pardus-about-publicip",
            _("Public IP"),
            "...",
            can_hide=True,
            value_loading=True,
        )
        add_to_grid(self.public_ip_cell)

        # Set computer name
        self.ui_computer_name_label.set_label(pc.get_computer_info()["model"])
        self.ui_computer_name_label.set_tooltip_text(pc.get_computer_info()["model"])

        self.ui_hardware_grid.show_all()

    def fill_details_page(self):
        # === Computer ===
        computer_info = self.computer_manager.get_computer_info()
        computer_info_row = HardwareDetailRow(
            icon_name="pardus-about-computer",
            title=_("Computer Info"),
            headers=[_("Vendor"), _("Model"), _("Family")],
            table=[
                [
                    computer_info["vendor"],
                    computer_info["model"],
                    computer_info["family"],
                ]
            ],
        )
        self.ui_hardware_details_box.add(computer_info_row)

        # === Operating System ===
        os_info_row = HardwareDetailRow(
            icon_name="pardus-about-symbolic",
            title=_("Operating System"),
            headers=[_("Name"), _("Version"), _("Kernel"), _("Desktop"), _("Display")],
            table=[
                [
                    self.os_info["os_name"],
                    self.os_info["os_version"],
                    self.os_info["kernel"],
                    self.os_info["desktop"],
                    self.os_info["display"],
                ]
            ],
        )
        self.ui_hardware_details_box.add(os_info_row)

        # === Processor ===
        processor_info = self.computer_manager.get_processor_info()
        processor_info_row = HardwareDetailRow(
            icon_name="pardus-about-processor",
            title=_("Processor"),
            headers=[_("Vendor"), _("Model"), _("Cores / Threads")],
            table=[
                [
                    processor_info["vendor"],
                    processor_info["name"],
                    f"{processor_info['core_count']} / {processor_info['thread_count']}",
                ]
            ],
        )
        self.ui_hardware_details_box.add(processor_info_row)

        # === Memory ===
        memory_info = self.computer_manager.get_memory_info()
        memory_info_table = []
        for i, slot in enumerate(memory_info, start=1):
            size = slot.get("size", 0.0)

            if int(size) == 0:
                # Empty Slot
                memory_info_table.append([i, _("Empty"), "", "", ""])
            else:
                # Size formatting (16 -> "16 GB")
                size_text = f"{int(size)} GB"

                mem_type = slot.get("type", _("Unknown"))
                vendor = slot.get("vendor", _("Unknown"))
                speed = slot.get("speed", "")

                memory_info_table.append([i, vendor, size_text, mem_type, speed])

        memory_info_row = HardwareDetailRow(
            icon_name="pardus-about-memory",
            title=_("Memory"),
            headers=[_("Slot"), _("Vendor"), _("Size"), _("Type"), _("Speed")],
            table=memory_info_table,
        )
        self.ui_hardware_details_box.add(memory_info_row)

        # === Storage ===
        storage_info = self.hardware_info.get("storage", [])
        valid_storage = [dev for dev in storage_info if dev.get("type")]

        storage_info_table = [
            [device.get("size", ""), device.get("type", ""), device.get("model", "")]
            for device in valid_storage
        ]

        if storage_info_table == []:
            storage_info_table = [[_("Device not found"), "", ""]]

        storage_info_row = HardwareDetailRow(
            icon_name="pardus-about-storage",
            title=_("Storage"),
            headers=[_("Size"), _("Type"), _("Model")],
            table=storage_info_table,
        )
        self.ui_hardware_details_box.add(storage_info_row)

        # === Graphics ===
        graphics_info_table = [
            [
                device.get("vendor", ""),
                device.get("driver", ""),
                device.get("name", ""),
            ]
            for device in self.hardware_info.get("graphics", [])
        ]

        if graphics_info_table == []:
            graphics_info_table = [[_("Device not found"), "", ""]]

        graphics_info_row = HardwareDetailRow(
            icon_name="pardus-about-graphics",
            title=_("Graphics"),
            headers=[_("Vendor"), _("Driver"), _("Model")],
            table=graphics_info_table,
        )
        self.ui_hardware_details_box.add(graphics_info_row)

        # === Display ===
        display_info_table = [
            [
                device.get("vendor", ""),
                device.get("resolution", ""),
                device.get("name", ""),
            ]
            for device in self.hardware_info.get("display", [])
        ]

        if display_info_table == []:
            display_info_table = [[_("Device not found"), "", ""]]

        display_info_row = HardwareDetailRow(
            icon_name="pardus-about-monitor",
            title=_("Display"),
            headers=[_("Vendor"), _("Resolution"), _("Model")],
            table=display_info_table,
        )
        self.ui_hardware_details_box.add(display_info_row)

        # === Ethernet ==
        ethernet_info_table = [
            [
                device.get("vendor", ""),
                device.get("driver", ""),
                device.get("name", ""),
            ]
            for device in self.hardware_info.get("ethernet", [])
        ]
        if ethernet_info_table == []:
            ethernet_info_table = [[_("Device not found"), "", ""]]

        ethernet_info_row = HardwareDetailRow(
            icon_name="pardus-about-ethernet",
            title=_("Ethernet"),
            headers=[_("Vendor"), _("Driver"), _("Model")],
            table=ethernet_info_table,
        )
        self.ui_hardware_details_box.add(ethernet_info_row)

        # === Wifi ==
        wifi_info_table = [
            [
                device.get("vendor", ""),
                device.get("driver", ""),
                device.get("name", ""),
            ]
            for device in self.hardware_info.get("wifi", [])
        ]
        if wifi_info_table == []:
            wifi_info_table = [[_("Device not found"), "", ""]]

        wifi_info_row = HardwareDetailRow(
            icon_name="pardus-about-wifi",
            title=_("Wifi"),
            headers=[_("Vendor"), _("Driver"), _("Model")],
            table=wifi_info_table,
        )
        self.ui_hardware_details_box.add(wifi_info_row)

        # === Bluetooth ==
        bluetooth_info_table = [
            [
                device.get("vendor", ""),
                device.get("driver", ""),
                device.get("name", ""),
            ]
            for device in self.hardware_info.get("bluetooth", [])
        ]
        if bluetooth_info_table == []:
            bluetooth_info_table = [[_("Device not found"), "", ""]]
        bluetooth_info_row = HardwareDetailRow(
            icon_name="pardus-about-bluetooth",
            title=_("Bluetooth"),
            headers=[_("Vendor"), _("Driver"), _("Model")],
            table=bluetooth_info_table,
        )
        self.ui_hardware_details_box.add(bluetooth_info_row)

        # === Audio ==
        audio_info_table = [
            [
                device.get("vendor", ""),
                device.get("driver", ""),
                device.get("name", ""),
            ]
            for device in self.hardware_info.get("audio", [])
        ]
        if audio_info_table == []:
            audio_info_table = [[_("Device not found"), "", ""]]
        audio_info_row = HardwareDetailRow(
            icon_name="pardus-about-audio",
            title=_("Audio"),
            headers=[_("Vendor"), _("Driver"), _("Model")],
            table=audio_info_table,
        )
        self.ui_hardware_details_box.add(audio_info_row)

        # === Camera ==
        camera_info_table = [
            [
                device.get("vendor", ""),
                device.get("driver", ""),
                device.get("name", ""),
            ]
            for device in self.hardware_info.get("camera", [])
        ]
        if camera_info_table == []:
            camera_info_table = [[_("Device not found"), "", ""]]
        camera_info_row = HardwareDetailRow(
            icon_name="pardus-about-camera",
            title=_("Camera"),
            headers=[_("Vendor"), _("Driver"), _("Model")],
            table=camera_info_table,
        )
        self.ui_hardware_details_box.add(camera_info_row)

        # === Keyboard ==
        keyboard_info_table = [
            [
                device.get("name", ""),
                device.get("driver", ""),
                device.get("bus", ""),
            ]
            for device in self.hardware_info.get("keyboard", [])
        ]
        if keyboard_info_table == []:
            keyboard_info_table = [[_("Device not found"), "", ""]]

        keyboard_info_row = HardwareDetailRow(
            icon_name="pardus-about-keyboard",
            title=_("Keyboard"),
            headers=[_("Name"), _("Driver"), _("Connection")],
            table=keyboard_info_table,
        )
        self.ui_hardware_details_box.add(keyboard_info_row)

        # === Mouse ==
        mouse_info_table = [
            [
                device.get("name", ""),
                device.get("driver", ""),
                device.get("bus", ""),
            ]
            for device in self.hardware_info.get("mouse", [])
        ]
        if mouse_info_table == []:
            mouse_info_table = [[_("Device not found"), "", ""]]

        mouse_info_row = HardwareDetailRow(
            icon_name="pardus-about-mouse",
            title=_("Mouse"),
            headers=[_("Name"), _("Driver"), _("Connection")],
            table=mouse_info_table,
        )
        self.ui_hardware_details_box.add(mouse_info_row)

        # === fingerprint ==
        fingerprint_info_table = [
            [
                device.get("vendor", ""),
                device.get("name", ""),
            ]
            for device in self.hardware_info.get("fingerprint", [])
        ]
        if fingerprint_info_table == []:
            fingerprint_info_table = [[_("Device not found"), "", ""]]

        fingerprint_info_row = HardwareDetailRow(
            icon_name="pardus-about-fingerprint",
            title=_("Fingerprint"),
            headers=[_("Vendor"), _("Model")],
            table=fingerprint_info_table,
        )
        self.ui_hardware_details_box.add(fingerprint_info_row)

        # === Printer ==
        printer_info_table = [
            [
                device.get("name", ""),
                device.get("bus", ""),
            ]
            for device in self.hardware_info.get("printer", [])
        ]
        if printer_info_table == []:
            printer_info_table = [[_("Device not found"), "", ""]]

        printer_info_row = HardwareDetailRow(
            icon_name="pardus-about-printer",
            title=_("Printer"),
            headers=[_("Vendor"), _("Connection")],
            table=printer_info_table,
        )
        self.ui_hardware_details_box.add(printer_info_row)

        self.ui_hardware_details_box.show_all()

    # Send Hardware Report Tasks
    def send_hardware_data(self, task, source_object, task_data, cancellable):
        try:
            all_info = self.computer_manager.get_all_device_info()
            response = requests.post(HARDWARE_API, json=all_info, timeout=3)

            task.return_value(response)
        except requests.Timeout as r:
            print("timeout!")
            task.return_value(r)
        except Exception as e:
            print("exception:", e)
            task.return_value(e)

    def send_hardware_data_completed(self, source, task):
        task_finished, data = task.propagate_value()

        self.ui_submit_stack.set_visible_child_name("main")

        if task_finished:
            if isinstance(data, requests.Response):
                if str(data.status_code)[0] == "2":
                    report_id = data.json()["data"]["link"]
                    url = f"{HARDWARE_API_DOMAIN}{report_id}"
                    markup = f'<a href="{url}">{report_id}</a>'

                    self.ui_submit_window.hide()

                    self.show_info_dialog(
                        title=_("Thank you for your contribution."),
                        subtitle=_("You can find your submission here:")
                        + "\n"
                        + markup,
                        use_markup=True,
                    )

                    self.ui_submit_report_btn.set_sensitive(False)
                else:
                    message = data.json()["message"]

                    print("Response:", json.dumps(data.json(), indent=2))
                    print(data.status_code)

                    self.show_info_dialog(
                        title=_("An error occured while sending the data."),
                        subtitle=_("Returned message from the server:")
                        + f"\n{data.status_code}\n{message}",
                    )

            else:
                self.show_info_dialog(
                    title=_("Connection Failed"),
                    subtitle=_(
                        "If you are connected to the internet, then our servers have some problem."
                    ),
                )

    # Export System report tasks:
    def export_system_report(self, task, source_object, task_data, cancellable):
        desktop_path = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP)

        p = ActionsAsk.run("report")
        if p.returncode == 0:
            SystemReportManager.pkexec_user = os.environ["USER"]
            SystemReportManager.generate_user_report()

            p2 = SystemReportManager.archive_and_copy_to_desktop(desktop_path)
            if p2.returncode == 0:
                task.return_boolean(True)
                return

        task.return_boolean(False)

    def export_system_report_completed(self, source, task):
        result = task.propagate_boolean()

        if result:
            self.ui_gathering_logs_stack.set_visible_child_name("success")
        else:
            self.ui_gathering_logs_stack.set_visible_child_name("failed")

        self.ui_gathering_logs_popup.show_all()

    def show_info_dialog(self, title, subtitle, use_markup=False):
        dialog = Gtk.MessageDialog(
            buttons=Gtk.ButtonsType.OK,
            text=title,
            secondary_use_markup=use_markup,
            secondary_text=subtitle,
        )
        dialog.run()
        dialog.hide()

    def on_ui_edit_hostname_btn_clicked(self, btn):
        current_hostname = self.ui_hostname_label.get_text()

        self.ui_edit_hostname_entry.set_text(current_hostname)
        self.ui_edit_hostname_popover_title_label.set_text(_("Change Hostname:"))
        self.ui_edit_hostname_popover.popup()

    def on_read_hardware_info_finish(self, source, task):
        self.ui_report_box.set_sensitive(True)

        # Fill Main Page
        self.fill_main_page()

        # Fetch network ip addresses after main page setup
        ip_task = Gio.Task.new(callback=self.on_fetch_public_ip_finish)
        ip_task.run_in_thread(self.fetch_public_ip)

        self.ui_hardware_grid.show_all()

        # Fill Hardware Details Page
        self.fill_details_page()

        self.toggle_hardware_details_pane()

    def on_fetch_public_ip_finish(self, source, task):
        self.public_ip_cell.set_value(self.public_ip)

        self.ui_hardware_grid.show_all()

    def on_menu_about_button_clicked(self, btn):
        self.ui_popover_menu.popdown()
        self.ui_about_dialog.run()
        self.ui_about_dialog.hide()

    def on_menu_export_report_button_clicked(self, btn):
        self.ui_popover_menu.popdown()

        self.ui_gathering_logs_stack.set_visible_child_name("wait")
        self.ui_gathering_logs_popup.show_all()

        task = Gio.Task.new(callback=self.export_system_report_completed)
        task.run_in_thread(self.export_system_report)

    def on_hardware_info_button_clicked(self, btn):
        self.is_hardware_details_visible = not self.is_hardware_details_visible
        self.toggle_hardware_details_pane()

    def on_display_report_button_clicked(self, btn):
        device_list = self.computer_manager.get_all_device_info()
        print(json.dumps(device_list, indent=2))
        self.ui_submit_lbl.set_text(json.dumps(device_list, indent=2))
        self.ui_submit_stack.set_visible_child_name("main")
        self.ui_submit_window.show_all()

    def on_copy_report_btn_clicked(self, btn):
        clipboard = Gtk.Clipboard.get_default(Gdk.Display.get_default())
        clipboard.set_text(self.ui_submit_lbl.get_text(), -1)
        self.ui_notification_popover.popup()

    def on_submit_report_btn_clicked(self, btn):
        self.ui_submit_stack.set_visible_child_name("spinner")
        task = Gio.Task.new(callback=self.send_hardware_data_completed)
        task.run_in_thread(self.send_hardware_data)

    def toggle_hardware_details_pane(self):
        if self.is_hardware_details_visible:
            self.ui_info_stack.set_visible_child_name("hardware_details")
            self.ui_hardware_info_button.set_label(_("Show Summary"))
        else:
            self.ui_info_stack.set_visible_child_name("hardware_grid")
            self.ui_hardware_info_button.set_label(_("Show Hardware Details"))

    def on_ui_hardware_list_computer_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_computer_revealer.get_reveal_child()
        self.ui_hardware_list_computer_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_computer_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_os_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_os_revealer.get_reveal_child()
        self.ui_hardware_list_os_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_os_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_processor_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_processor_revealer.get_reveal_child()
        self.ui_hardware_list_processor_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_processor_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_memory_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_memory_revealer.get_reveal_child()
        self.ui_hardware_list_memory_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_memory_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_storage_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_storage_revealer.get_reveal_child()
        self.ui_hardware_list_storage_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_storage_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_graphics_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_graphics_revealer.get_reveal_child()
        self.ui_hardware_list_graphics_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_graphics_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_display_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_display_revealer.get_reveal_child()
        self.ui_hardware_list_display_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_display_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_ethernet_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_ethernet_revealer.get_reveal_child()
        self.ui_hardware_list_ethernet_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_ethernet_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_wifi_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_wifi_revealer.get_reveal_child()
        self.ui_hardware_list_wifi_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_wifi_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_bluetooth_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_bluetooth_revealer.get_reveal_child()
        self.ui_hardware_list_bluetooth_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_bluetooth_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_audio_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_audio_revealer.get_reveal_child()
        self.ui_hardware_list_audio_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_audio_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_camera_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_camera_revealer.get_reveal_child()
        self.ui_hardware_list_camera_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_camera_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_keyboard_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_keyboard_revealer.get_reveal_child()
        self.ui_hardware_list_keyboard_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_keyboard_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_mouse_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_mouse_revealer.get_reveal_child()
        self.ui_hardware_list_mouse_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_mouse_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_fingerprint_eventbox_button_press_event(
        self, widget, event
    ):
        state = not self.ui_hardware_list_fingerprint_revealer.get_reveal_child()
        self.ui_hardware_list_fingerprint_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_fingerprint_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_hardware_list_printer_eventbox_button_press_event(self, widget, event):
        state = not self.ui_hardware_list_printer_revealer.get_reveal_child()
        self.ui_hardware_list_printer_revealer.set_reveal_child(state)
        icon = "go-up-symbolic" if state else "go-down-symbolic"
        self.ui_hardware_list_printer_revealer_image.set_from_icon_name(
            icon, Gtk.IconSize.BUTTON
        )

    def on_ui_edit_hostname_entry_changed(self, entry):
        current_hostname = self.ui_hostname_label.get_text()
        value = entry.get_text()

        is_sensitive = self.validate_hostname(current_hostname, value)
        self.ui_edit_hostname_ok_btn.set_sensitive(is_sensitive)

    def on_ui_edit_hostname_ok_btn_clicked(self, btn):
        current_hostname = self.ui_hostname_label.get_text()
        new_hostname = self.ui_edit_hostname_entry.get_text()

        if not self.validate_hostname(current_hostname, new_hostname):
            if current_hostname == new_hostname:
                return  # wrote this again to prevent the next false error message show to the user

            self.ui_edit_hostname_popover_title_label.set_text(
                _("Hostname is invalid. Use only letters, numbers and '-'.")
            )
            return

        # Change
        if HostnameManager.set_hostname(new_hostname):
            self.ui_hostname_label.set_text(new_hostname)
            self.ui_hostname_label.set_tooltip_text(new_hostname)
            self.ui_edit_hostname_popover.popdown()
        else:
            self.ui_edit_hostname_popover_title_label.set_text(
                _("Hostname change failed! Please check the terminal output.")
            )
            print("Hostname change failed!")

    def on_ui_edit_hostname_entry_activate(self, entry):
        self.on_ui_edit_hostname_ok_btn_clicked(None)

    def on_ui_edit_hostname_cancel_btn_clicked(self, btn):
        self.ui_edit_hostname_popover.popdown()
