#!/usr/bin/env python3

import sys, gi
from gi.repository import Gio, Gtk
from MainWindow import MainWindow

gi.require_version("Gtk", "3.0")


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="tr.org.pardus.about",
            flags=Gio.ApplicationFlags.NON_UNIQUE,
            **kwargs
        )
        self.window = None

    def do_activate(self):
        self.window = MainWindow(self)


if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)
