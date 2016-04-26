#!/bin/python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from gui_handler import Handler

settings = Gtk.Settings.get_default()
settings.set_property("gtk-application-prefer-dark-theme", True)

builder = Gtk.Builder()
builder.add_from_file("glade/2ndgui.glade")

main_window = builder.get_object("main_window")
main_window.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)

builder.connect_signals(Handler(builder))

main_window.show_all()

Gtk.main()
