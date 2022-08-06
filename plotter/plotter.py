import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from intervallist.interval import Interval
from solver.util import fetch_image_name


def plot_statements(intervals: dict, influences: list[tuple[str, str]], statement: tuple = None):
    # setup amount of plots
    figure, axis = plt.subplots(max(len(influences), 2))  # when using subplots, at least 2 are needed

    # setup distance of the plots
    plt.subplots_adjust(left=0.1,
                        bottom=0.1,
                        right=0.9,
                        top=0.95,
                        wspace=0.4,
                        hspace=1)

    for index, influence in enumerate(influences):
        if influence not in intervals:
            continue

        statements: list[Interval] = sorted(intervals[influence].all_intervals())
        turned: list[Interval] = sorted(intervals[influence].all_intervals())

        if len(statements) == 0:
            continue

        # setup axis
        min_x, max_x, min_y, max_y = statements[0].begin, statements[-1].end, turned[0].begin, turned[-1].end
        axis[index].axis([min_x, max_x, min_y, max_y])
        axis[index].set(xlabel=influence[0], ylabel=influence[1])

        # plot the statements
        for interval in statements:
            plot_statement(axis[index], interval)

        # plot optional statement
        if statement is not None and (statement[0], statement[4]) == influence:
            quality: str = statement[2]
            interval_x: tuple[float, float] = statement[1]
            interval_y: tuple[float, float] = statement[3]

            statement_interval: Interval = Interval(interval_x[0], interval_x[1], quality,
                                                    interval_y[0], interval_y[1])
            plot_statement(axis[index], statement_interval, "red")


def plot_statement(ax, statement: Interval, color="black"):
    bottom: float = statement.begin_other
    left: float = statement.begin
    width: float = statement.end - statement.begin
    height: float = statement.end_other - statement.begin_other

    rect = mpatches.Rectangle((left, bottom), width, height,
                              fill=False,
                              alpha=1,
                              color=color,
                              linewidth=0.5)
    ax.add_patch(rect)

    # plot the image of the symbol
    position_x: float = left + width / 2
    position_y: float = bottom + height / 2
    arr_lena = mpimg.imread(f"./plotter/{fetch_image_name(statement.quality, color)}")
    image_box = OffsetImage(arr_lena, zoom=0.2)
    ab = AnnotationBbox(image_box, (position_x, position_y), frameon=False, pad=0)
    ax.add_artist(ab)


def show_plot():
    plt.show()
