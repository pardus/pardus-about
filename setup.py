#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os, subprocess


def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            os.makedirs("{}/{}/LC_MESSAGES".format(podir, po.split(".po")[0]), exist_ok=True)
            mo_file = "{}/{}/LC_MESSAGES/{}".format(podir, po.split(".po")[0], "pardus-about.mo")
            msgfmt_cmd = 'msgfmt {} -o {}'.format(podir + "/" + po, mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(("/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                       ["po/" + po.split(".po")[0] + "/LC_MESSAGES/pardus-about.mo"]))
    return mo

data_files = [
    ("/usr/share/applications/", ["tr.org.pardus.about.desktop"]),
    ("/usr/share/pardus/pardus-about/", ["pardus-about.svg", "bluebackground.png", "bayrak.gif"]),
    ("/usr/share/pardus/pardus-about/src", ["src/main.py", "src/MainWindow.py", "src/dump_system_info.sh", "src/get_system_info.sh", "src/copy_to_desktop.sh", "src/dump_logs.sh"]),
    ("/usr/share/pardus/pardus-about/ui", ["ui/MainWindow.glade"]),
    ("/usr/share/pardus/pardus-about/data", ["data/pci.ids", "servers.txt"]),
    ("/usr/share/polkit-1/actions", ["tr.org.pardus.pkexec.pardus-about.policy"]),
    ("/usr/bin/", ["pardus-about"]),
    ("/usr/share/icons/hicolor/scalable/apps/", ["pardus-about.svg"])
] + create_mo_files()

setup(
    name="pardus-about",
    version="0.2.0",
    packages=find_packages(),
    scripts=["pardus-about"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Emin Fedar",
    author_email="emin.fedar@pardus.org.tr",
    description="Get info about your Pardus system.",
    license="GPLv3",
    keywords="about",
    url="https://www.pardus.org.tr",
)
