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
    desktop_key = next(
        (item for item in str(desktop).lower().split(":") 
         if item in de_version_command),
        None,
    )

    if not desktop_key:
        return ""

    try:
        result = subprocess.run(
            de_version_command[desktop_key],
            capture_output=True,
            text=True,
            check=False
        )
        
        output = result.stdout.strip()
        if not output:
            return ""

        if desktop_key == "xfce":
            for line in output.splitlines():
                if line.startswith("xfce4-session "):
                    return line.split()[-1].strip("()")

        elif desktop_key == "gnome":
            for line in output.splitlines():
                if "GNOME Shell" in line:
                    return line.split()[-1]

        elif desktop_key in ("cinnamon", "mate", "kde"):
            return output.split()[-1]

        elif desktop_key == "lxqt":
            for line in output.splitlines():
                if "liblxqt" in line:
                    return line.split()[1].strip()

        elif desktop_key == "budgie":
            return output.splitlines()[0].strip().split()[-1]

    except Exception:
        pass

    return ""
