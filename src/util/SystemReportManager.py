import json
import os
import pwd
import shutil
import subprocess
import tempfile
from pathlib import Path

from util import ComputerManager

# Private dir of the current report, generate_report() creates it
ARCHIVE_DIR = None


def detect_pkexec_user():
    # pwd goes through nss, domain users are not in /etc/passwd
    try:
        return pwd.getpwuid(int(os.environ.get("PKEXEC_UID", "0"))).pw_name
    except (KeyError, ValueError):
        return "root"


pkexec_user = detect_pkexec_user()


def run_and_save(command, command_name=None):
    """Usage: run_and_save(["journalctl", "-q", "-n", 1000]), it will be saved in ARCHIVE_DIR/journalctl"""

    if not command:
        return

    if command_name is None:
        command_name = "_".join(command)
        command_name = command_name.replace("_/", "")

    try:
        target_file = f"{ARCHIVE_DIR}/{pkexec_user}/{command_name}"
        if os.path.exists(target_file):
            os.unlink(target_file)
        with open(target_file, "w") as f:
            subprocess.run(command, stdout=f, stderr=f)
    except:
        # ignore fails
        pass


def copy(path):
    new_path = Path(f"{ARCHIVE_DIR}/{pkexec_user}/{path}")

    if os.path.isfile(path):
        # Create parents
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, new_path, follow_symlinks=False)
    elif os.path.isdir(path):
        new_path.mkdir(parents=True, exist_ok=True)
        shutil.copytree(path, new_path, symlinks=False, dirs_exist_ok=True)
    else:
        print("Not a file, nor a directory:", path)


def generate_report():
    global ARCHIVE_DIR
    # This runs as root: a fixed name in /tmp can be created by another user
    # first. mkdtemp makes a new 0700 dir with a random name.
    ARCHIVE_DIR = tempfile.mkdtemp(prefix="pardus_system_report_")
    os.makedirs(f"{ARCHIVE_DIR}/{pkexec_user}", exist_ok=True)

    # Program outputs
    run_and_save(
        ["env", "-i", "/bin/bash", "-c", "source /etc/profile ; env"],
        command_name="env_root",
    )
    run_and_save(["dmesg"])
    run_and_save(
        ["journalctl", "-q", "--since", "7 day ago"], command_name="journal_system"
    )
    run_and_save(["timedatectl"])
    run_and_save(["lsblk", "-J", "-f"])
    run_and_save(["df", "-al", "-x", "autofs"])
    run_and_save(["dmidecode"])
    run_and_save(["free"])
    run_and_save(["hostname"])
    run_and_save(["dpkg", "-l"])
    run_and_save(["ip", "-o", "addr"])
    run_and_save(["ip", "route", "show", "table", "all"])
    run_and_save(["lsb_release", "-a"])
    run_and_save(["lsusb"])
    run_and_save(["top", "-b", "-n", "1"])
    run_and_save(["lsmod"])
    run_and_save(["blkid"])
    run_and_save(["fdisk", "-l", "-x"])
    run_and_save(["lspci", "-nnvv"])
    run_and_save(["mount", "-l"])
    run_and_save(["nmcli", "dev", "show"])
    run_and_save(["nmcli", "con", "show"])
    run_and_save(["netstat", "-W", "-neopa"])
    run_and_save(["ps", "auxwwwm"])
    run_and_save(["pstree", "-lp"])
    run_and_save(["find", "/", "-maxdepth", "2", "-type", "l", "-ls"])
    run_and_save(["uname", "-a"])
    run_and_save(["apt", "list"])
    run_and_save(["sysctl", "--all"])
    run_and_save(["docker", "ps", "-a"])
    run_and_save(["uptime"])

    # Copy Logs
    copy("/var/log/apt")
    copy("/var/log/auth.log")
    copy("/var/log/boot.log")
    copy("/var/log/daemon.log")
    copy("/var/log/dpkg.log")
    copy("/var/log/kern.log")
    copy("/var/log/syslog")
    copy("/var/log/user.log")
    copy("/var/log/pardus-installer.log")

    # Copy configs
    copy("/etc/hosts")
    copy("/boot/grub/grub.cfg")
    copy("/boot/config-{}".format(os.uname().release))
    copy("/etc/resolv.conf")
    copy("/etc/environment")
    copy("/etc/apt/sources.list")
    copy("/etc/apt/sources.list.d")

    # set permission and owner, the logs here are not for other users
    subprocess.run(["chown", pkexec_user, "-R", ARCHIVE_DIR])
    subprocess.run(["chmod", "go-rwx", "-R", ARCHIVE_DIR])

    return ARCHIVE_DIR


def generate_user_report():
    # General System Hardware Report
    hardware_info = json.dumps(
        ComputerManager.ComputerManager().get_all_device_info(), indent=2
    )

    # Make dir
    os.makedirs(f"{ARCHIVE_DIR}/{pkexec_user}", exist_ok=True)

    with open(f"{ARCHIVE_DIR}/{pkexec_user}/system_info.json", "w") as f:
        f.write(hardware_info)

    # Program outputs
    run_and_save(["env"], command_name="env_user")
    run_and_save(["dconf", "dump", "/"])
    run_and_save(
        ["journalctl", "--user", "-q", "--since", "7 day ago"],
        command_name="journal_user",
    )
    run_and_save(["flatpak", "list"])


def archive_and_copy_to_desktop(desktop_path, archive_name):
    archive_path = f"{desktop_path}/{archive_name}"
    process = subprocess.run(
        [
            "tar",
            "-czf",
            archive_path,
            "--ignore-failed-read",
            f"--directory={ARCHIVE_DIR}",
            ".",
        ]
    )
    if os.path.exists(archive_path):
        os.chmod(archive_path, 0o600)
    shutil.rmtree(ARCHIVE_DIR, ignore_errors=True)
    return process
