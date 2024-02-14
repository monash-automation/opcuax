import random
from time import time

from benchmark._models import Printer, PrinterJob, Temperature

__states = ["Ready", "Printing", "Finished"]
__files = ["A.gcode", "B.gcode", "C.gcode", "D.gcode"]


def __random_temp() -> float:
    return random.uniform(70, 100)


def __random_pos() -> float:
    return random.uniform(-200, 200)


def _random_temperature() -> Temperature:
    return Temperature(target=__random_temp(), actual=__random_temp())


def _random_job() -> PrinterJob:
    tot = random.uniform(100, 500)
    used = random.uniform(0, tot)
    prog = used / tot
    left = tot - used
    approx = left + random.uniform(0, 20)
    return PrinterJob(
        file=random.choice(__files),
        progress=prog,
        time_used=used,
        time_left=left,
        time_left_approx=approx,
    )


def random_printer() -> Printer:
    return Printer(
        state=random.choice(__states),
        bed=_random_temperature(),
        nozzle=_random_temperature(),
    )


class Timer:
    _start: float
    lib: str
    api: str
    printers: int
    n: int

    def __init__(self, lib: str, api: str, printers: int, n: int) -> None:
        self.lib = lib
        self.api = api
        self.printers = printers
        self.n = n

    def start(self) -> None:
        self._start = time()

    def end(self) -> None:
        t = time() - self._start
        print(
            "%s %s %d printer %d times %2.3f sec"
            % (self.lib, self.api, self.printers, self.n, t)
        )
