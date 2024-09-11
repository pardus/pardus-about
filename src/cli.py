import gi
import os
import cairosvg
import io
import utils


gi.require_version("GLib", "2.0")
from gi.repository import GLib
import PIL.Image

emblem_path = "/usr/share/icons/vendor/scalable/emblems"
emblem_fn = "emblem-vendor.svg"


class CLI(object):
    def __init__(self):
        self.run()
        pass

    def run(self):
        terminal_size = os.get_terminal_size()
        terminal_height = terminal_size.lines
        terminal_width = terminal_size.columns
        logo_path = os.path.abspath(os.path.join(emblem_path, emblem_fn))
        img = None
        if os.path.exists(logo_path):
            try:
                img = self.svg2png(logo_path)
                img = self.image2ascii(img, int(terminal_width / 3))

            except Exception as e:
                print(e)
        info = self.info_lines()
        if img:
            # check if img or info has higher length
            length = len(info)
            if len(img) > len(info):
                length = len(img)
            for index in range(length):
                # print img line with info line if there is img line. otherwise put some blank spaces as terminal width / 3
                if index < len(img):
                    img_line = img[index]
                else:
                    img_line = " " * int(terminal_width / 3)
                if index < len(info):
                    info_line = info[index]
                else:
                    info_line = ""
                print(f"{self.colored_text(img_line,'yellow')} {info_line}")
        else:
            for line in info:
                print(line)

    def svg2png(self, svg_path):
        png_data = cairosvg.svg2png(url=svg_path)
        return PIL.Image.open(io.BytesIO(png_data))

    def image2ascii(self, image, width=100):
        aspect_ratio = image.height / image.width
        new_height = int(aspect_ratio * width * 0.55)
        image = image.resize((width, new_height))
        image = image.convert("L")
        ascii_str = ""
        for pixel in image.getdata():
            ascii_str += " .:-=+*#%@"[pixel // 32]

        ascii_lines = [
            ascii_str[i : i + width] for i in range(0, len(ascii_str), width)
        ]
        return ascii_lines

    def info_lines(self):
        info = []
        username, hostname = utils.get_credentials()
        _, _, os_pretty = utils.get_os_info()
        kernel, release = utils.get_kernel()
        uptime = utils.get_uptime()
        total_packages = utils.get_total_installed_packages()
        shell = utils.get_shell()
        desktop_env, desktop_env_ver = utils.get_desktop_environment()
        window_manager = utils.get_window_manager()
        window_manager_theme = utils.get_wm_theme()
        cpu_model, cpu_thread = utils.get_cpu()
        total_physical_ram, total_ram = utils.get_ram_size()
        gpus = utils.get_gpu()

        info.append(
            f"{self.colored_text(username, 'green')}{self.colored_text('@','red')}{self.colored_text(hostname, 'yellow')}"
        )
        info.append(self.colored_text(f"----------------", "blue"))
        info.append(self.colored_info("OS", os_pretty))
        info.append(self.colored_info("Kernel", f"{kernel} {release}"))
        info.append(self.colored_info("Uptime", uptime))
        info.append(self.colored_info("Total Packages", total_packages))
        info.append(self.colored_info("Shell", shell))

        info.append(
            self.colored_info(
                "Desktop Environment", desktop_env + " " + desktop_env_ver
            )
        )
        info.append(self.colored_info("Window Manager", window_manager))
        info.append(self.colored_info("Theme", window_manager_theme))
        info.append(self.colored_info("CPU", f"{cpu_model} x{cpu_thread}"))
        info.append(
            self.colored_info(
                "RAM",
                f"{utils.beauty_size(total_ram)} (Physical RAM:{utils.beauty_size(total_physical_ram)})",
            )
        )
        for index, gpu in enumerate(gpus):
            info.append(self.colored_info(f"GPU{index} Vendor", gpu["vendor"]))
            info.append(self.colored_info(f"GPU{index} Device", gpu["device"]))
            info.append(self.colored_info(f"GPU{index} Driver", gpu["driver"]))

        return info

    def colored_text(self, text, color):
        linux_terminal_colors = {
            "black": 0,
            "red": 1,
            "green": 2,
            "yellow": 3,
            "blue": 4,
            "magenta": 5,
            "cyan": 6,
            "white": 7,
        }
        color_code = linux_terminal_colors.get(color, 7)
        return f"\033[3{color_code}m{text}\033[0m"

    def colored_info(self, label, text, color="yellow"):
        lbl = self.colored_text(label, color)
        return f"{lbl}: {text}"
