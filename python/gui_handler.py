import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from ledctrl import full_color
from fft import FFT
import cairo



class Barchart:
    def __init__(self, bars, ctx, width, height):
        self.bars = bars
        self.width = width
        self.height = height
        self.ctx = ctx

        self.ctx.scale(width, height)
        self.ctx.rectangle(0,0,1,1)


    def bar(self, i, value):
        barwidth = 1 / self.bars
        # self.ctx.rectangle(1 - value/100, i * self.barwidth, 1, (i+1) * self.barwidth) # 1 - abs(value)/100)
        self.ctx.move_to(i * barwidth, 1-(value/100))
        self.ctx.line_to((i+1) * barwidth, 1-(value/100))
        self.ctx.set_line_width(.01)

    def draw_test(self):
        for i in range(self.bars):
            self.bar(i, i)

    def fft_draw(self, values):
        barwidth = 1 / self.bars
        self.bars = len(values)
        self.ctx.set_line_width(.01)
        self.ctx.move_to(0, 1)
        for i, value in enumerate(values):
            # self.bar(i, value)
            self.ctx.line_to((i+1) * barwidth, 1-(value/100))
        self.ctx.set_source_rgb(.8, 0, 0)
        self.ctx.stroke()


class Handler:
    def __init__(self, builder):
        self.builder = builder
        self.fft_bars = [builder.get_object("fft_" + str(i)) for i in range(40)]
        self.fft = FFT("front:CARD=CODEC,DEV=0")
        self.fft.start_analyse_thread()
        self.fft_timeout = GObject.timeout_add(50, self.fft_callback, None)
        self.fft_bars[0].set_value(1)
        self.style_provider = Gtk.CssProvider()
        # self.style_provider.load_from_path("glade/fft.css")

        self.fft_darea = self.builder.get_object("fft_drawing_area")


        self.chart = None

    def fft_draw(self, wid, ctx):
        size = wid.get_allocation()
        # cr.translate(size.x, size.y)
        self.chart = Barchart(40, ctx, 900, 400)
        # self.chart.ctx.set_source_rgb(0.7, 0.2, 0.0)
        self.chart.fft_draw(self.fft.intensity())
        wid.queue_draw()


    def gtk_main_quit(self, *args):
        self.fft.stop_analyse_thread()
        Gtk.main_quit(*args)

    def nav_change(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter != None:
            print("You selected", model[treeiter][0])

    def send_static(self, button):
        colorchooser = self.builder.get_object("color_static")
        color = colorchooser.get_rgba()
        color = [color.red, color.green, color.blue]
        full_color(color)
        print(color)

    def fft_callback(self, user_data):
        intensity = self.fft.intensity()
        for bar, value in zip(self.fft_bars, intensity):
            bar.set_value(value/100)
        if self.chart:
            self.chart.fft_draw(intensity)
        return True

    def fft_state(self, button, none):
        if self.builder.get_object("fft_state_switch").get_active():
            self.fft.start_analyse_thread()
        else:
            self.fft.stop_analyse_thread()


