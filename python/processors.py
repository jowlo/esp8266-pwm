import abc


class Processor(metaclass=abc.ABCMeta):
    def __init__(self, controller, source):
        self.source = source
        self.controller = controller

    @abc.abstractmethod
    def process(self):
        pass

    def set_source(self, source):
        self.source = source


class ToStateProcessor(Processor, metaclass=abc.ABCMeta):
    pass


class MoveColor(ToStateProcessor):
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
                intensity = [((((self.scale * i) / 100)**2) if i > self.threshold else 0) for i in source_data]
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
                                                  self.controller.color.alpha(color, intensity[self.channel]))
                    state = nextstate[:]
                yield state
        return generator()


class PulseColor(ToStateProcessor):
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

                intensity = [((((self.scale * i) / 100)**2) if i > self.threshold else 0) for i in source_data]
                if self.channel < len(intensity):
                    state = self.controller.state_factory.full_color(
                        self.controller.color.alpha(color, self.scale * intensity[self.channel])
                    )
                yield state
        return generator()


class Equalizer(ToStateProcessor):
    def __init__(self, controller, source, base):
        super(Equalizer, self).__init__(controller, source)
        self.base = base
        self.scale = 1
        self.threshold = 0

    def process(self, color_provider=None):
        def generator():
            state = self.base()
            source_data = self.source()
            bucket_size = (len(source_data) // len(self.controller.groups))
            if bucket_size < 1:
                bucket_size = 1
            print(bucket_size)
            while True:
                color = color_provider()
                source_data = self.source()
                intensity = [((((self.scale * i) / 100)**2) if i > self.threshold else 0) for i in source_data]
                for i, group in enumerate(self.controller.groups):
                    bucket_intensity = sum(intensity[i * bucket_size: (i + 1) * bucket_size]) / bucket_size
                    state = self.controller.state_factory.set_strips(
                        state, group, self.controller.color.alpha(color, bucket_intensity)
                    )
                yield state
        return generator()


class HeatEqualizer(ToStateProcessor):
    def __init__(self, controller, source, base):
        super(HeatEqualizer, self).__init__(controller, source)
        self.base = base
        self.scale = 1
        self.threshold = 0

    def process(self, color_provider=None):
        def generator():
            state = self.base()
            colors = self.controller.color.heat_colors()
            state = self.controller.state_factory.state_off()

            source_data = self.source()
            bucket_size = (len(source_data) // len(self.controller.groups))
            if bucket_size < 1:
                bucket_size = 1
            while True:
                source_data = self.source()
                intensity = [((((self.scale * i) / 100)) if i > self.threshold else 0) for i in source_data]
                for i, group in enumerate(self.controller.groups):
                    bucket_intensity = sum(intensity[i * bucket_size: (i + 1) * bucket_size]) / bucket_size
                    # bucket_intensity = max(0, min(bucket_intensity, 99))
                    self.controller.state_factory.set_strips(state, group, colors[
                        int(bucket_intensity * 100 if bucket_intensity * 100 < len(colors) else len(colors) - 1)
                    ])
                yield state

        return generator()


class Relaxation(Processor):
    def __init__(self, controller, source, relaxation):
        super(Relaxation, self).__init__(controller, source)
        self.relaxation = relaxation
        self.history = []
        self.history = self.source()

    def process(self):
        def generate():
            data = self.source()
            if len(data) == 0:
                return data
            if len(self.history) < len(data):
                zipper = [data, data]
            else:
                zipper = [self.history, data]
            self.history = [(self.relaxation * old + new) // (self.relaxation + 1)
                            for old, new in zip(*zipper)]
            return self.history

        return generate()


class TurnColor(ToStateProcessor):
    def __init__(self, controller, source, base):
        super(TurnColor, self).__init__(controller, source)
        self.base = base
        self.decay = 0.8
        self.threshold = 0
        self.channel = 0
        self.scale = 1

    def process(self, color_provider=None):
        def generator():
            group_count = 0
            delay_count = 0
            state = 0
            while True:
                real_delay = self.decay * 10 # TODO: remove hack...
                if delay_count < 1:
                    delay_count = real_delay
                    color = color_provider()
                    source_data = self.source()
                    state = self.controller.state_factory.state_off()
                    intensity = [((((self.scale * i) / 100)**2) if i > self.threshold else 0) for i in source_data]
                    if self.channel < len(intensity) and intensity[self.channel] > 0:
                        self.controller.state_factory.set_strips(state,
                                                                self.controller.groups[group_count],
                                                                # [[0], [1], [2], [3], [7], [4], [5], [6], [8], [9]][group_count],
                                                                # self.controller.color.alpha(color, intensity[self.channel]))
                                                                color)
                    group_count = (group_count + 1) % len(self.controller.groups)
                else:
                    delay_count -= 1
                yield state
        return generator()
