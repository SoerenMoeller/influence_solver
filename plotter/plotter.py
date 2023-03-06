import os

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib import image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from solver.util import fetch_image_name
from statement_containers.statement import Statement
from statement_containers.statement_list_dynamic import StatementListDynamic


def plot_statements(intervals: dict, influences: list[tuple[str, str]]):
    """
    Plots model using matplotlib. This only builds the plots, they are shown using the show_plot method

    Parameters:
        intervals (dict): contains statements accesseble via its pair of variables
        influences (list): list of variable pairs, whose statements should be plotted
    """

    # setup amount of plots
    _, axis = plt.subplots(max(len(influences), 2))  # when using subplots, at least 2 are needed

    # setup distance of the plots
    plt.subplots_adjust(left=0.1,
                        bottom=0.1,
                        right=0.9,
                        top=0.95,
                        wspace=0.4,
                        hspace=1)

    hypothesis = StatementListDynamic.get_instance().hypothesis
    for index, influence in enumerate(influences):
        if influence not in intervals:
            continue

        _plot_axis(axis, index, hypothesis, intervals, influence)


def _plot_axis(axis, index: int, hypothesis: tuple, intervals: dict, influence: tuple[str, str]):
    """
    Sets up the axis range as needed and plots the statements onto them

    Parameters:
        index (int): index of the axis
        hypothesis (tuple): hypothesis that should be highlighted
        intervals (dict): contains statements accesseble via its pair of variables
        influences (list): list of variable pairs, whose statements should be plotted
    """

    if type(intervals[influence]) == set:
        statements: list[Statement] = sorted(intervals[influence])
    else:
        statements: list[Statement] = intervals[influence].get_statements()

    if len(statements) == 0:
        return

    # get min/max values
    min_x, max_x = min(iv.begin for iv in statements), max(iv.end for iv in statements)
    min_y, max_y = min(iv.begin_y for iv in statements), max(iv.end_y for iv in statements)
    if hypothesis is not None and (hypothesis[0], hypothesis[4]) == influence:
        min_x = min(min_x, hypothesis[1][0])
        max_x = max(max_x, hypothesis[1][1])
        min_y = min(min_y, hypothesis[3][0])
        max_y = max(max_y, hypothesis[3][1])

    # build axis and add offset to prevent statements from overlapping it
    offset_x: float = abs(max_x - min_x) if abs(max_x - min_x) != 0 else 10
    offset_y: float = abs(max_y - min_y) if abs(max_y - min_y) != 0 else 10
    margin_x: float = offset_x / 30
    margin_y: float = offset_y / 6
    axis[index].axis([min_x - margin_x, max_x + margin_x, min_y - margin_y, max_y + margin_y])
    axis[index].set(xlabel=influence[0], ylabel=influence[1])

    # plot the statements
    for interval in statements:
        plot_statement(axis[index], interval)

    # plot highlighted hypothesis
    if hypothesis is not None and (hypothesis[0], hypothesis[4]) == influence:
        quality: str = hypothesis[2]
        interval_x: tuple[float, float] = hypothesis[1]
        interval_y: tuple[float, float] = hypothesis[3]

        statement_interval: Statement = Statement(interval_x[0], interval_x[1], quality,
                                                  interval_y[0], interval_y[1])
        plot_statement(axis[index], statement_interval, "red")


def plot_statement(ax, statement: Statement, offset_x: float, color="black"):
    """
    Plots a given statement by drawing its borders and inserting the quality in the center

    Parameters:
        ax: current axis
        statement (Statement): statement to draw
        color (str): color of the statement
    """
    bottom: float = statement.begin_y
    left: float = statement.begin
    width: float = statement.end - statement.begin
    height: float = statement.end_y - statement.begin_y

    # create window
    rect = mpatches.Rectangle((left, bottom), width, height,
                              fill=False,
                              alpha=1,
                              color=color,
                              linewidth=0.5)
    ax.add_patch(rect)

    # plot the image of the symbol
    position_x: float = left + width / 2
    position_y: float = bottom + height / 2
    dir_name = os.path.dirname
    parent_dir: str = dir_name(dir_name(os.path.realpath(__file__)))
    path: str = os.path.join(parent_dir, "plotter", fetch_image_name(statement.quality, color))
    arr_lena = mpimg.imread(path)

    # scale the image
    zoom: float = 0.2
    if width < 0.2:
        zoom = 0.1

    image_box = OffsetImage(arr_lena, zoom=zoom)
    ab = AnnotationBbox(image_box, (position_x, position_y), frameon=False, pad=0)
    ax.add_artist(ab)


def show_plot():
    """
    Show all previously created plots
    """

    plt.show()
