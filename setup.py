#!/usr/bin/env python3
from setuptools import setup, find_packages
from shutil import copyfile

copyfile("icon.svg", "pardus-about.svg")

data_files = [
    ("/usr/share/applications/", ["tr.org.pardus.about.desktop"]),
    ("/usr/share/locale/tr/LC_MESSAGES/", ["translations/tr/LC_MESSAGES/pardus-about.mo"]),
    ("/usr/share/locale/pt/LC_MESSAGES/", ["translations/pt/LC_MESSAGES/pardus-about.mo"]),
    ("/usr/share/pardus/pardus-about/", ["icon.svg", "bluebackground.png", "bayrak.gif"]),
    ("/usr/share/pardus/pardus-about/src", ["src/main.py", "src/MainWindow.py", "src/dump_system_info.sh", "src/get_system_info.sh", "src/copy_to_desktop.sh", "src/dump_logs.sh"]),
    ("/usr/share/pardus/pardus-about/ui", ["ui/MainWindow.glade"]),
    ("/usr/share/polkit-1/actions", ["tr.org.pardus.pkexec.pardus-about.policy"]),
    ("/usr/bin/", ["pardus-about"]),
    ("/usr/share/icons/hicolor/scalable/apps/", ["pardus-about.svg"])
]

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
