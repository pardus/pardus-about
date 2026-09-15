import subprocess

de_version_command = {
    "xfce": ["xfce4-session", "--version"],
    "gnome": ["gnome-shell", "--version"],
    "cinnamon": ["cinnamon", "--version"],
    "mate": ["mate-about", "--version"],
    "kde": ["plasmashell", "--version"],
    "lxqt": ["lxqt-about", "--version"],
    "budgie": ["budgie-desktop", "--version"],
}


def get_desktop_version(desktop):
    version = ""
    desktop = next(
        (item for item in str(desktop).lower().split(":")
         if item in de_version_command),
        "",
    )
    try:
        if desktop in de_version_command:
            output = (
                (
                    subprocess.run(
                        de_version_command[desktop],
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                )
                .stdout.decode()
                .strip()
            )
        else:
            return ""
        # print(output, desktop)
        if "xfce" in desktop:
            for line in output.split("\n"):
                if line.startswith("xfce4-session "):
                    version = line.split(" ")[-1].strip("()")
                    break

        elif "gnome" in desktop:
            for line in output.split("\n"):
                if "GNOME Shell" in line:
                    version = line.split(" ")[-1]

        elif "cinnamon" in desktop:
            version = output.split(" ")[-1]

        elif "mate" in desktop:
            version = output.split(" ")[-1]

        elif "kde" in desktop:
            version = output.split(" ")[-1]

        elif "lxqt" in desktop:
            for line in output:
                if "liblxqt" in line:
                    version = line.split()[1].strip()

        elif "budgie" in desktop:
            version = output.split("\n")[0].strip().split(" ")[-1]
    except Exception as e:
        version = ""

    return version
