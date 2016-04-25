import colorsys
import math


class Color:
    white = [1, 1, 1]

    red = [1, 0, 0]
    green = [0, 1, 0]
    blue = [0, 0, 1]

    orange = [0.5266666666666667, 0.2974521739130435, 0.04739999999999999]
    violet = [0.5803921568627451, 0.0, 0.8274509803921568]
    pink = [0.3471789855072465, 0.04223333333333337, 0.6033333333333334]

    brown = [0.5450980392156862, 0.27058823529411763, 0.07450980392156863]
    cyan = [0.0, 1.0, 1.0]
    gold = [0.8549019607843137, 0.6470588235294118, 0.12549019607843137]

    dark_green = [0.13333333333333333, 0.5450980392156862, 0.13333333333333333]
    dark_blue = [0.0, 0.0, 0.5019607843137255]
    light_blue = [0.0, 0.7490196078431373, 1.0]

    def alpha(self, color, alpha):
        """Return a color with set alpha."""
        return [alpha * c for c in color]

    def pseudocolor(self, start, end, val, minval=0, maxval=100):
        hmin = colorsys.rgb_to_hsv(*start)[0]
        hmax = colorsys.rgb_to_hsv(*end)[0]
        h = hmin + ((float(val - minval) / (maxval - minval)) * (hmax - hmin))
        # print(h, (val-minval), (maxval+1-val) )
        return colorsys.hsv_to_rgb(h, 1., 1.)

    def hsv_gradient(self, steps, start, end, minval=0, maxval=100):
        colors = []
        for val in range(minval, maxval, int((maxval - minval) / steps)):
            colors.append(self.pseudocolor(start, end, val, minval, maxval))
        return colors

    def black_to_color_map(self, steps, color, minval=0, maxval=100):
        colors = []
        for val in range(minval, maxval, (maxval - minval) // steps):
            colors.append(self.alpha(color, (val - minval) / (maxval)))
        return colors

    def rainbow_colors(self, num=2000, freq=.03):
        """Return list of rainbow colors with num elements"""
        colors = []
        for i in range(num):
            colors.append([math.sin(freq * i + offset) * 0.5 + 0.5 for offset in range(0, 6, 2)])
        return colors

    def heat_colors(self, num=100, freq=.05):
        """Return list of rainbow colors with num elements"""
        colors = []
        for i in range(num):
            color = []
            color.append(-math.sin(freq * i + 1) * 0.5 + 0.5)
            color.append(0)
            color.append(math.sin(freq * i) * 0.5 + 0.5)
            colors.append(color)
        return colors
