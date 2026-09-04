import os
import subprocess
import json


def list_parts():
    ret = []
    for disk in os.listdir("/sys/block"):
        for part in os.listdir(f"/sys/block/{disk}"):
            if not part.startswith(disk):
                continue
            ret.append(part)
    return ret


def get_root_part():
    with open("/proc/mounts", "r") as f:
        for line in f.read().split("\n"):
            if "/" == line.split(" ")[1]:
                return line.split(" ")[0]
    return None


win_table = {
    "10.": "10",
    "6.4": "10",
    "6.3": "8.1",
    "6.2": "8",
    "6.1": "7",
    "6.0": "Vista",
    "5.2": "XP Pro x64",
    "5.1": "XP",
    "5.0": "2000",
    "4.9": "ME",
    "4.1": "98",
    "4.0": "95",
}


def get_windows_version():
    if not os.path.isdir("/run/winroot/Windows/servicing/Version"):
        return ""
    for item in os.listdir("/run/winroot/Windows/servicing/Version"):
        if len(item) < 3:
            continue
        item = item[:3]
        if item in win_table.keys():
            return win_table[item]
    return ""


def get_dualboot_oses():
    dualboot = {}
    winroot_dir = "/run/winroot"
    if os.path.islink(winroot_dir):
        os.unlink(winroot_dir)
    os.makedirs(winroot_dir, mode=0o700, exist_ok=True)
    try:
        os.chmod(winroot_dir, 0o700)
    except OSError:
        pass
    root_part = get_root_part()
    for part in list_parts():
        if f"/dev/{part}" == root_part:
            continue
        sp = subprocess.run(
            ["mount", "-o", "ro,nosuid,nodev,noexec", f"/dev/{part}", winroot_dir],
            capture_output=True,
        )
        if 0 == sp.returncode:
            # Windows
            if os.path.exists(f"{winroot_dir}/Windows/System32/ntoskrnl.exe"):
                dualboot[part] = "Windows " + get_windows_version()
            # Mac OS X
            if os.path.exists(
                f"{winroot_dir}/System/Library/CoreServices/SystemVersion.plist"
            ):
                dualboot[part] = "Mac OS X"
            # Linux
            if os.path.exists(f"{winroot_dir}/etc/os-release"):
                with open(f"{winroot_dir}/etc/os-release", "r") as f:
                    for line in f.read().split("\n"):
                        if line.startswith("NAME="):
                            dualboot[part] = line[6:-1]
            subprocess.run(["umount", "-lf", winroot_dir], check=False)

    try:
        os.rmdir(winroot_dir)
    except OSError:
        pass
    return json.dumps(dualboot)


if __name__ == "__main__":
    print(get_dualboot_oses())
