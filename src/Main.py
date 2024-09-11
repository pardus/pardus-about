#!/usr/bin/env python3

import sys
import gi
import cli

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gio, Gtk

from MainWindow import MainWindow


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id="tr.org.pardus.about",
            flags=Gio.ApplicationFlags.NON_UNIQUE | Gio.ApplicationFlags(8),
            **kwargs
        )
        self.window = None
        self.add_main_option(
            "nogui",
            ord("n"),
            GLib.OptionFlags(0),
            GLib.OptionArg.NONE,  # Adjusted for boolean flag (no argument expected)
            "No GUI mode",
            None,
        )
        GLib.set_prgname("tr.org.pardus.about")

    def do_activate(self):
        if not self.args or "nogui" not in self.args:
            self.window = MainWindow(self)
        else:
            cli.CLI()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        options = options.end().unpack()
        self.args = options
        self.activate()
        return 0


app = Application()
app.run(sys.argv)
