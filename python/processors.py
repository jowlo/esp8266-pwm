import abc
import sys
import numpy as np

class Processor(metaclass=abc.ABCMeta):
    def __init__(self, controller, source):
        self.source = source
        self.controller = controller

    @abc.abstractmethod
    def process(self):
        pass

    def set_source(self, source):
        self.source = source


class MoveColor(Processor):
    def __init__(self, controller, source, base):
        super(MoveColor, self).__init__(controller, source)
        self.base = base
        self.decay = 0.8
        self.threshold = 0
        self.channel = 0
        self.scale = 1

    def process(self, color_provider=None):
        def generator():
            state = self.base()
            while True:
                color = color_provider()
                source_data = self.source()
                nextstate = self.base()
                intensity = [((self.scale * i) if i > self.threshold else 0) for i in source_data]
                if self.channel < len(intensity):
                    for i, group in enumerate(self.controller.groups):
                        self.controller.state_factory.set_strips(nextstate,
                                                                 group,
                                                                 self.controller.color.alpha(
                                                                     state[self.controller.groups[i - 1][0]],
                                                                     self.decay)
                                                                 )
                    self.controller.state_factory.set_strips(nextstate,
                                                  self.controller.groups[0],
                                                  self.controller.color.alpha(color, intensity[self.channel] / 100))
                    state = nextstate[:]
                yield state
        return generator()


class PulseColor(Processor):
    def __init__(self, controller, source, base):
        super(PulseColor, self).__init__(controller, source)
        self.base = base
        self.threshold = 0
        self.channel = 0
        self.scale = 1

    def process(self, color_provider=None):
        def generator():
            while True:
                color = color_provider()
                source_data = self.source()
                state = self.base()

                intensity = [((self.scale * i) if i > self.threshold else 0) for i in source_data]
                if self.channel < len(intensity):
                    state = self.controller.state_factory.full_color(
                        self.controller.color.alpha(color, self.scale * intensity[self.channel] / 100)
                    )
                yield state
        return generator()


class Relaxation(Processor):
    def __init__(self, controller, source, relaxation):
        super(Relaxation, self).__init__(controller, source)
        self.relaxation = relaxation
        self.history = [] * self.relaxation
        self.history = self.source()

    def process(self):
        def generate():
            if len(self.history) < len(self.source()):
                zipper = [self.source(), self.source()]
            else:
                zipper = [self.source(), self.history]
            return [(old + new)/2 for old, new in zip(*zipper)]

        return generate()

