from gi.repository import Gtk, GObject, GdkPixbuf, Gdk


class Strobe:
    def __init__(self, handler):
        self.handler = handler
        self.builder = handler.builder
        self.strobes_box = self.builder.get_object("strobes_box")
        self.groups = []
        self.color_provider = None
        self.delay = 1
        self.smoothness = 0
        self.duty = 0
        self.runner = None
        self.rainbow_freq = .3

        self.expander = Gtk.Expander()
        self.expander.set_label("Strobe")

        self.grid = Gtk.Grid()

        # Color chooser buttons
        button_box = Gtk.Box(spacing=6)
        self.white_button = Gtk.RadioButton.new_with_label_from_widget(None, "White")
        self.white_button.connect("toggled", self.color_chosen, "white")
        button_box.pack_start(self.white_button, False, False, 0)
        self.color_button = Gtk.RadioButton.new_from_widget(self.white_button)
        self.color_button.set_label("Colorpicker")
        self.color_button.connect("toggled", self.color_chosen, "color")
        button_box.pack_start(self.color_button, False, False, 0)
        self.rainbow_button = Gtk.RadioButton.new_from_widget(self.white_button)
        self.rainbow_button.set_label("Rainbow")
        self.rainbow_button.connect("toggled", self.color_chosen, "rainbow")
        button_box.pack_start(self.rainbow_button, False, False, 0)
        # Initialize to white
        self.color_chosen(self.white_button, "white")
        self.grid.attach(button_box, 0, 0, 2, 1)

        # Scales for delay and smoothness
        # value, lower, upper, step_increment, page_increment, page_size
        self.smoothness_adjustment = Gtk.Adjustment(1, 1, 100, 0, 0, 0)
        self.smoothness_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.smoothness_adjustment)
        self.smoothness_scale.set_sensitive(True)
        self.smoothness_adjustment.connect("value_changed", self.smoothness_cb)
        self.smoothness_scale.set_draw_value(False)

        self.delay_adjustment = Gtk.Adjustment(1, 1, 300, 0, 0.0, 0)
        self.delay_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.delay_adjustment)
        self.delay_scale.set_sensitive(True)
        self.delay_adjustment.connect("value_changed", self.delay_cb)
        self.delay_scale.set_draw_value(False)

        self.duty_adjustment = Gtk.Adjustment(1, 1, 100, 0, 0, 0)
        self.duty_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.duty_adjustment)
        self.duty_scale.set_sensitive(True)
        self.duty_adjustment.connect("value_changed", self.duty_cb)
        self.duty_scale.set_draw_value(False)

        self.rainbow_freq_adjustment = Gtk.Adjustment(1, 1, 100, 0, 0, 0)
        self.rainbow_freq_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.rainbow_freq_adjustment)
        self.rainbow_freq_scale.set_sensitive(True)
        self.rainbow_freq_scale.set_hexpand(True)
        self.rainbow_freq_scale.set_draw_value(False)

        self.rainbow_freq_adjustment.connect("value_changed", self.rainbow_cb)

        self.grid.attach(Gtk.Label("Rainbow Frequency"), 0, 1, 1, 1)
        self.grid.attach(self.rainbow_freq_scale, 1, 1, 1, 1)
        self.grid.attach(Gtk.Label("Smooth (n/a)"), 0, 2, 1, 1)
        self.grid.attach(self.smoothness_scale, 1, 2, 1, 1)
        self.grid.attach(Gtk.Label("Delay"), 0, 3, 1, 1)
        self.grid.attach(self.delay_scale, 1, 3, 1, 1)
        self.grid.attach(Gtk.Label("Duty"), 0, 4, 1, 1)
        self.grid.attach(self.duty_scale, 1, 4, 1, 1)



        # Group select
        group_grid = Gtk.Grid()
        for i in range(handler.controller.strips):
            checkbox = Gtk.CheckButton(str(i + 1))
            checkbox.set_active(True)
            checkbox.connect("toggled", self.group_selected_cb, i)
            self.group_selected_cb(checkbox, i)
            group_grid.attach(checkbox, i % 5, i // 5, 1, 1)

        self.grid.attach(group_grid, 0, 5, 2, 1)

        remove_button = Gtk.Button("Remove")
        remove_button.connect("clicked", self.remove_button_cb)
        self.grid.attach(remove_button, 0, 6, 1, 1)

        self.switch = Gtk.Switch()
        self.switch.connect("state-set", self.switch_clicked_cb)
        self.grid.attach(self.switch, 1, 6, 1, 1)

        self.grid.set_hexpand(True)
        self.expander.set_hexpand(True)
        self.expander.add(self.grid)
        self.expander.set_expanded(True)
        self.strobes_box.pack_start(self.expander, False, False, 0)
        self.expander.show_all()

    def group_selected_cb(self, checkbox, group):
        if checkbox.get_active() and group not in self.groups:
            self.groups.append(group)
        else:
            self.groups = [i for i in self.groups if i != group]

        print("Group ", group, "selected: ", self.groups)
        pass

    def switch_clicked_cb(self, switch, data):
        if switch.get_active():
            self.start()
        else:
            self.kill()
        print("Switch clicked")
        pass

    def color_chosen(self, button, name):
        def color_provider():
            c = self.builder.get_object("color_static").get_rgba()
            return [c.red, c.green, c.blue]

        self.color_index = 0
        self.rainbow_cycle = self.handler.controller.color.rainbow_colors(freq=self.rainbow_freq)
        def rainbow_provider():
                self.color_index = (self.color_index + 1) % len(self.rainbow_cycle)
                return self.rainbow_cycle[self.color_index]

        def white():
            return [1, 1, 1]

        if name == "color":
            self.color_provider = color_provider
        elif name == "white":
            self.color_provider = white
        elif name == "rainbow":
            self.color_provider = rainbow_provider

        self.restart()

    def delay_cb(self, scale):
        self.delay = scale.get_value() / 100
        self.restart()
        print("Delay set to: " + str(self.delay))

    def duty_cb(self, scale):
        self.duty = scale.get_value() / 100
        self.restart()
        print("Duty set to: " + str(self.duty))

    def smoothness_cb(self, scale):
        self.smoothness = scale.get_value() / 100
        print("Smoothness set to: " + str(self.smoothness))

    def rainbow_cb(self, scale):
        self.rainbow_freq = scale.get_value() / 100
        print("Smoothness set to: " + str(self.rainbow_freq))

    def remove_button_cb(self, button):
        self.kill()
        self.expander.destroy()

    def start(self):
        self.runner = GObject.timeout_add(1000 * self.delay, self.send_strobe, None)
        self.handler.controller.network.start_sender_thread()

    def send_strobe(self, _):
        print("sending strobe")

        # Save old generator
        restore_generator = self.handler.controller.network.generator

        def restore(_):
            self.handler.controller.network.generator = restore_generator
            self.handler.state_update(None)
            return False

        # Set new generator
        def generator():
            color = self.color_provider()
            state = self.handler.controller.state_factory.full_color([0, 0, 0])
            state = self.handler.controller.state_factory.set_strips(state, self.groups, color)
            while True:
                # if self.handler.strip_display:
                #    self.handler.strip_display.draw()
                yield state
        self.handler.controller.network.generator = generator()

        GObject.timeout_add(1000 * self.duty, restore, None)
        return True

    def restart(self):
        if self.runner:
            self.kill()
            self.start()

    def kill(self):
        if self.runner:
            GObject.source_remove(self.runner)
        self.runner = None
