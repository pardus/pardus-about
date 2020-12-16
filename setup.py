#!/usr/bin/env python3
from setuptools import setup, find_packages

data_files = [
    ("/usr/share/applications/", ["tr.org.pardus.about.desktop"]),
    ("/usr/share/locale/tr/LC_MESSAGES/", ["translations/tr/LC_MESSAGES/pardus-about.mo"]),
    ("/usr/share/pardus/pardus-about/", ["icon.svg", "pardus-logo.svg"]),
    ("/usr/share/pardus/pardus-about/src", ["src/main.py", "src/MainWindow.py", "src/dump_system_info.py", "src/copy_to_home.py", "src/dump_logs.py"]),
    ("/usr/share/pardus/pardus-about/ui", ["ui/MainWindow.glade"]),
    ("/usr/bin/", ["pardus-about"])
]

setup(
    name="About Pardus",
    version="0.1.0",
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
