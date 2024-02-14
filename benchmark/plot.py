from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from pydantic import BaseModel

Library = Literal["asyncua", "opcuax"]
Api = Literal["server-write", "server-read", "client-write", "client-read"]


class Result(BaseModel):
    library: Library
    api: Api
    printers: int
    n: int
    seconds: float


def parse_result(line: str) -> Result:
    [lib, api, printers, _, n, __, seconds, ___] = line.split(" ")
    return Result(library=lib, api=api, printers=printers, n=n, seconds=float(seconds))


def parse_results(text: str) -> list[Result]:
    return [parse_result(line) for line in text.split("\n") if len(line) > 0]


def sub_plot(ax: Axes, results: list[Result], api: Api) -> None:
    results = [result for result in results if result.api == api]
    ua = [
        result
        for result in results
        if result.library == "asyncua" and result.printers == 10
    ]
    uax = [
        result
        for result in results
        if result.library == "opcuax" and result.printers == 10
    ]

    ua = sorted(ua, key=lambda result: (result.printers, result.n))
    uax = sorted(uax, key=lambda result: (result.printers, result.n))

    assert len(ua) == len(uax)
    assert all(_ua.n == _uax.n for _ua, _uax in zip(ua, uax))

    species = [str(result.n) for result in ua]
    data = {
        "opcua-asyncio": [result.seconds for result in ua],
        "opcuax": [result.seconds for result in uax],
    }

    x = np.arange(len(species))  # the label locations
    width = 0.4  # the width of the bars
    multiplier = 0

    for attribute, measurement in data.items():
        offset = width * multiplier
        rects = ax.bar(x + offset, measurement, width, label=attribute)
        ax.bar_label(rects, padding=4)
        multiplier += 1

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel("Seconds (s)")
    ax.set_title(plot_title(api, 10))
    ax.set_xticks(x + 0.2, species)
    ax.legend(loc="upper left", ncols=1)
    # ax.set_ylim(0, 12)


def plot(results: list[Result]) -> None:
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, layout="constrained")

    sub_plot(ax1, results, "server-read")
    sub_plot(ax2, results, "client-read")
    sub_plot(ax3, results, "server-write")
    sub_plot(ax4, results, "client-write")

    fig.set_figwidth(12)
    fig.set_figheight(9)

    # plt.show()
    plt.savefig("benchmark.png", dpi=900)
    plt.close()


def plot_title(api: Api, n: int) -> str:
    title = api.replace("-", " ")
    title += f" {n} printers n times"
    return title.title()


if __name__ == "__main__":
    with open("./result.txt") as f:
        _results = [parse_result(line) for line in f.readlines()]
        plot(_results)
