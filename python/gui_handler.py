import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf, Gdk
from ledctrl import LED_Controller
from processors import Processor, ToStateProcessor, Relaxation
from fft import FFT


class BarChart:
    def __init__(self, bars, ctx, width, height):
        self.bars = bars
        self.width = width
        self.height = height
        self.ctx = ctx
        self.ctx.scale(width, height)
        self.ctx.set_source_rgba(.2, .2, .2, 0)
        self.ctx.rectangle(0, 0, 1, 1)
        self.ctx.fill()
        self.threshold = 0

    def bar(self, i, value):
        barwidth = 1 / (2*self.bars)
        # self.ctx.rectangle(1 - value/100, i * self.barwidth, 1, (i+1) * self.barwidth) # 1 - abs(value)/100)
        self.ctx.move_to(2 * i * barwidth, 1-(value/100))
        self.ctx.line_to(2* (i * barwidth) + barwidth, 1-(value/100))
        self.ctx.set_line_width(.01)

    def draw_test(self):
        for i in range(self.bars):
            self.bar(i, i)

    def draw_threshold(self):
        self.ctx.set_source_rgba(0, 0, 0, .3)
        self.ctx.rectangle(0, 1 - (self.threshold/100), 1, (self.threshold/100))
        # self.ctx.move_to(0, 1 - (self.threshold/100))
        # self.ctx.line_to(1, 1 - (self.threshold/100))
        self.ctx.set_line_width(0.00)
        self.ctx.fill()

    def draw(self, values):
        self.bars = len(values)
        self.ctx.set_line_width(.01)
        self.ctx.move_to(0, 1)
        for i, value in enumerate(values):
            self.bar(i, value)
        self.ctx.set_source_rgb(.8, 0, 0)
        self.ctx.stroke()
        self.ctx.set_line_width(.001)
        for i, value in enumerate(values):
            self.ctx.line_to((i+0.5) * 1/self.bars, 1-(value/100))
        self.ctx.set_source_rgb(.4, .6, .9)
        self.ctx.stroke()
        self.draw_threshold()


class StripDisplay():
    def __init__(self, bars, source, ctx):
        self.bars = bars
        self.ctx = ctx
        self.source = source
        self.width = 20
        self.spacing = 25
        self.draw()

    def draw(self):
        if not self.source:
            return True
        for i, value in enumerate(self.source): # self.controller.network.state):
            self.ctx.set_source_rgb(value[0], value[1], value[2])
            self.ctx.rectangle(0, (i * self.spacing), self.width, self.width)
            self.ctx.fill()
        return True


class Grouper:
    def __init__(self, strips, handler):
        self.handler = handler
        grouping_area = handler.builder.get_object("grouping_area")
        self.box = Gtk.Grid()
        grouping_area.add(self.box)

        self.groups = dict()
        self.combos = list()

        group_store = Gtk.ListStore(int, str)
        for i in range(strips):
            group_store.append([i, "Group " + str(i + 1)])


        for i in range(strips):
            label = Gtk.Label()
            label.set_text("Strip " + str(i))
            label.set_justify(Gtk.Justification.LEFT)
            self.box.attach(label, 0, i, 1, 1)
            group_combo = Gtk.ComboBox.new_with_model_and_entry(group_store)
            self.combos.append(group_combo)
            group_combo.connect("changed", self.update_groups)
            group_combo.set_entry_text_column(1)
            group_combo.set_active(i)
            self.box.attach(group_combo, 1, i, 1, 1)

    def update_groups(self, combo):
        self.groups = [list() for _ in range(self.handler.controller.strips)]
        for i, box in enumerate(self.combos):
            self.groups[box.get_active()].append(i)

        self.handler.controller.groups = [group for group in self.groups if group != []]
        return True


class Handler:
    def __init__(self, builder):
        self.builder = builder
        self.cardstring = "front:CARD=CODEC,DEV=0"

        self.controller = LED_Controller(10, "192.168.4.1", 5555)

        self.fft_bars = [builder.get_object("fft_bar_" + str(i)) for i in range(40)]

        self.fft_timeout = GObject.timeout_add(50, self.fft_callback, None)
        self.state_timeout = GObject.timeout_add(30, self.state_update, None)

        self.fft_darea = self.builder.get_object("fft_drawing_area")
        self.state_darea = self.builder.get_object("state_drawing_area")
        self.chart = None
        self.strip_display = None

        self.provider = None

        self.relaxation_box = self.builder.get_object("relaxation_frame_count")

        self.pcm_chooser = builder.get_object("pcm_combo_box")
        for pcm in FFT.available_pcms():
            self.pcm_chooser.append_text(pcm)

        self.grouper = Grouper(self.controller.strips, self)

        self.fft_effect_chooser = builder.get_object("fft_effect_combo")
        self.effects = {cls.__name__: cls for cls in ToStateProcessor.__subclasses__()}
        # self.effects = {
        #     "PulseColor": PulseColor,
        #     "MoveColor": MoveColor,
        #     "Equalizer": Equalizer
        # }
        for effect in self.effects.keys():
            self.fft_effect_chooser.append_text(effect)
        self.fft_effect_chooser.set_entry_text_column(0)
        self.fft_effect_chooser.set_active(0)
        self.builder.get_object("fft_rescale_button").set_sensitive(False)

    def fft_draw(self, wid, ctx):
        if self.controller.fft is None:
            self.fft_darea.set_size_request(600, 400)
            self.chart = BarChart(40, ctx, 600, 400)
            self.chart.draw([0] * 40)
            return
        self.fft_darea.set_size_request(600, 400)
        self.chart = BarChart(40, ctx, 600, 400)
        self.chart.threshold = self.provider.threshold
        self.chart.draw([self.provider.scale * i for i in self.controller.fft.intensity()])
        wid.queue_draw()

    def gtk_main_quit(self, *args):
        self.controller.stop_all_threads()
        Gtk.main_quit(*args)

    def pcm_chooser_clicked(self, button):
        for pcm in FFT.available_pcms():
            self.pcm_chooser.append_text(pcm)

    def nav_change(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter != None:
            print("You selected", model[treeiter][0])

    def send_static(self, *args):
        colorchooser = self.builder.get_object("color_static")
        color = colorchooser.get_rgba()
        color = [color.red, color.green, color.blue]
        self.controller.full_color(color)
        print(color)

    def fft_callback(self, user_data):
        if self.controller.fft is None:
            return True
        intensity = self.controller.fft.intensity()
        for bar, value in zip(self.fft_bars, intensity):
            bar.set_value(max(0.1, value/100))
        if self.chart:
            self.chart.draw([self.provider.scale * i for i in intensity])
        return True

    def state_draw(self, wid, ctx):
        self.state_darea.set_size_request(20, 200)
        self.strip_display = StripDisplay(10, self.controller.network.state, ctx)
        self.strip_display.draw()
        wid.queue_draw()

    def state_update(self, data):
        if self.strip_display:
            self.strip_display.draw()

    def update_groups(self):
        pass

    def fft_state(self, button, none):
        if self.builder.get_object("fft_state_switch").get_active():
            self.cardstring = self.pcm_chooser.get_active_text()
            if self.controller.fft is None:
                self.controller.fft = FFT(self.cardstring)
                self.pcm_chooser.set_sensitive(False)
            self.controller.fft.start_analyse_thread()
            self.fft_start(button)
            self.fft_darea.queue_draw()
            self.builder.get_object("fft_rescale_button").set_sensitive(True)
        else:
            self.controller.network.stop_sender_thread()
            self.controller.fft.stop_analyse_thread()
            self.pcm_chooser.set_sensitive(True)
            self.builder.get_object("fft_rescale_button").set_sensitive(False)

    def fft_start(self, button):
        self.builder.get_object("fft_rescale_button").set_sensitive(True)
        self.update_fft_effect()

    def update_fft_effect(self):
        def color_provider():
            c = self.builder.get_object("color_static").get_rgba()
            return [c.red, c.green, c.blue]

        def rainbow_provider():
            for i in self.controller.color.rainbow_colors():
                print(i)
                yield i

        relax_value = int(self.relaxation_box.get_text())

        relax = Relaxation(self.controller, self.controller.fft.intensity, relax_value)
        print(relax)
        print(str(self.fft_effect_chooser.get_active_text()))
        effect_class = self.effects[self.fft_effect_chooser.get_active_text()] # i.e. PulseColor
        self.provider = effect_class(self.controller, relax.process, self.controller.state_factory.state_off)
        self.controller.network.generator = self.provider.process(color_provider)
        self.controller.network.start_sender_thread()
        # time.sleep(1)

    def relax_value_changed_cb(self, text):
        if self.relaxation_box.get_text() != '':
            self.update_fft_effect()
        return True

    def fft_decay_value_changed_cb(self, scale):
        self.provider.decay = scale.get_value()
        return True

    def fft_scale_value_changed_cb(self, scale):
        self.provider.scale = scale.get_value()
        return True

    def fft_threshold_value_changed_cb(self, scale):
        self.provider.threshold = scale.get_value()
        self.chart.threshold = scale.get_value()
        return True

    def fft_channel_changed(self, scale):
        if self.provider:
            self.provider.channel = int(scale.get_value())
        return True

    def fft_effect_changed(self, effect):
        if self.builder.get_object("fft_state_switch").get_active():
            self.update_fft_effect()
        return True

    def fft_rescale_button_clicked_cb(self, button):
        print("Rescaling FFT...")
        self.controller.fft.rescale()
        return True



