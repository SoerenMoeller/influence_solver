import bisect
import csv
import os

from solver.constants import QUALITY_CONS, QUALITY_ANTI, QUALITY_MONO
from solver.util import quality_add


def build_model_from_csv(file_name: str, amount_of_statements_mapping: dict = {}, statement_height_mapping: dict = {}, 
                         overlap_mapping: dict = {}, default_amount_of_statements: int = None, 
                         default_statement_height: float = None, default_overlap: float = 0) -> list[tuple]:
    """
    Create a model of a given experiment, using data points collected in a csv file.
    These points are orded on one axis and linear functions are created between them. 
    Then statements will be inserted centered on these linear functions with equal width
    and distributed over the whole domain of the experiment.

    The file should contain two coloums with the name of the variables in the first row. 
    The rows below are intepreted as the data points and both columns should have equal 
    length. Multiple influences can be joined by added further pairs of columns. 
    Examples are in the 'data' folder.

    Parameters: 
        file_name (str): 
            Name of the csv file
        amount_of_statements_mapping: (dict[tuple[str, str], int]):
            Assigns the amount of statements in the model with the given variable pair
        standard_amount_of_statements (int):    
            Assigns the amount of statements in the model, if no suitable entry is given
            in the mapping. If not present, uses the amount of data points in the csv entry
        statement_height_mapping (dict[tuple[str, str], float]):
            Assigns the height of each statement in the model belonging to a given variable 
            pair. If adjacent statements are not overlapping, the height will be stretched 
            as needed
        standard_statement_height (float):
            Assigns the height of each statement in the model, if no suitable entry is given
            in the mapping. If not present, use 10% of the range of the experiment
        overlap_mapping (dict[tuple[str, str], float]):
            Assigns the relative overlapping of adjacent statements in the model belonging to 
            a given variable pair. Overlapping should be in range [0, 1)
        default_overlap (float):
            Assigns the relative overlapping [0, 1) of adjacent statements in the model, if no suitable
            entry is given in the mapping

    Returns:
        model (list[tuple]):
            List containing the generated statements with the pattern
            tuple[str, tuple[float, float], str, tuple[float, float], str]
    """
    assert 0 <= default_overlap < 1, "Default overlap not in range [0, 1)"
    assert all(0 <= overlap_mapping[influence] < 1 for influence in overlap_mapping), "Overlap not in range [0, 1)"

    data: dict[tuple, list[tuple]] =_read_csv(file_name)
    model: list[tuple] = []

    # create statements for each variable pair
    for a, b in data:
        local_default_amount_of_statements = default_amount_of_statements
        local_default_statement_height = default_statement_height

        points: list[tuple] = data[(a, b)]
        assert points, "Empty data"

        # setup default values
        if default_amount_of_statements is None:
            local_default_amount_of_statements: int = len(points)
        if default_statement_height is None:
            y_points: list[float] = sorted([y for _, y in points])
            greatest_y, lowest_y = y_points[-1], y_points[0]
            local_default_statement_height: float = (greatest_y - lowest_y) * 0.1

        overlap_value: float = overlap_mapping[(a, b)] if (a, b) in overlap_mapping \
            else default_overlap
        amount_of_statements = amount_of_statements_mapping[(a, b)] if (a, b) in amount_of_statements_mapping \
            else local_default_amount_of_statements
        statement_height: float = statement_height_mapping[(a, b)] if (a, b) in statement_height_mapping \
            else local_default_statement_height

        # calc the statement width needed to have the overlapping and the (given) amount of statements in the model
        greatest_x, lowest_x = points[-1][0], points[0][0]
        statement_width: float = (greatest_x - lowest_x) / amount_of_statements
        statement_width_with_overlap: float = statement_width + overlap_value * statement_width

        # create statements with the given width until the end of the data points is reached
        x_current: float = lowest_x
        statements: list[tuple] = []
        while True:
            x_end: float = x_current + statement_width_with_overlap
            if x_end > greatest_x:
                x_end = greatest_x
            if x_current > greatest_x or x_current == x_end:
                break

            # get the corresponding y coordinate and the quality the statement to create
            y, quality = _get_y(points, x_current, x_end)
            half_height: float = statement_height // 2
            y_start = y - half_height
            y_end = y + half_height

            # check if predecessor statement does not overlap on y-axis and fix height if needed
            if len(statements) > 1:
                predecessor_y_start, predecessor_y_end = statements[-1][3]
                if predecessor_y_start > y_end:
                    y_end = predecessor_y_end
                if predecessor_y_end < y_start:
                    y_start = predecessor_y_end

            statement: tuple = (a, (x_current, x_end), quality, (y_start, y_end), b)
            statements.append(statement)

            # add overlapping to the statements by advancing the bounds only partly
            x_current += statement_width
        model.extend(statements)
    return model


def _read_csv(file_name: str) -> dict:
    """
    Read a csv file and extract the data point entries

    Parameters:
        file_name (str): Name of the csv file

    Returns:
        data (dict): 
            Contains the read data points. Mapping from the variable pairs 
            to the (list) of related statements
    """

    # get the (full) file name
    dir_name = os.path.dirname
    parent_dir: str = dir_name(dir_name(os.path.realpath(__file__)))
    path: str = os.path.join(parent_dir, "data", f"{file_name}.csv")

    # save data in list first, to store data under specific index
    data: list[tuple[tuple[str, str], list[tuple[float, float]]]] = []
    with open(path, encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')

        # read data row per row
        for i, row in enumerate(reader):
            clean_row: list[str] = [elem.strip() for elem in row]
            assert len(clean_row) % 2 == 0, "Could not read csv correctly"

            # iterate over the columns and add the data 
            for j in range(0, len(clean_row), 2):
                if i == 0:
                    data.append(((clean_row[j], clean_row[j + 1]), []))
                    continue

                index = j // 2
                data[index][1].append((float(clean_row[j]), float(clean_row[j + 1])))


    # sort the data points and convert it into a list
    return {variable_pair: sorted(data_points) for variable_pair, data_points in data}


def _create_linear_function(x_1: float, y_1: float, x_2: float, y_2: float):
    """
    Create linar function from two given data points
    """

    pitch: float = (y_2 - y_1) / (x_2 - x_1)

    def f(x: float) -> float:
        return pitch * x + y_2 - pitch * x_2

    return f, pitch


def _get_quality_from_pitch(pitch: float) -> str:
    """
    Map the pitch of a function to a statement quality
    """
    if pitch == 0:
        return QUALITY_CONS
    elif pitch < 0:
        return QUALITY_ANTI
    return QUALITY_MONO


def _get_y(points: list[tuple[float, float]], current: float, end: float) -> tuple[float, str]:
    """
    Calcluate the y-coordinate to the given middle of current point and end point, by determining the closest data 
    points, creating a linear function between them and calculating the y-coordinate from that. Additionally, extract
    the pitch of the function

    Returns:
        y-coordinate of the center of the statement to build and quality of the statement
    """

    # get clostest data points 
    lower_bound: int = bisect.bisect_left(points, current, key=lambda e: e[0])
    upper_bound: int = bisect.bisect_right(points, end, key=lambda e: e[0])
    x: float = (current + end) / 2
    index: int = bisect.bisect_left(points, x, key=lambda e: e[0])

    # correct bounds for edge cases
    if x != points[lower_bound][0] and lower_bound > 0:
        lower_bound -= 1
    if x != points[index][0] and index > 0:
        index -= 1
    if end == points[upper_bound - 1][0] and upper_bound - 1 > 0:
        upper_bound -= 1

    # build quality by creating linear function and checking its pitch
    quality: str = QUALITY_CONS
    for i in range(lower_bound, upper_bound):
        x_1, y_1 = points[i]
        x_2, y_2 = points[i + 1]
        f, pitch = _create_linear_function(x_1, y_1, x_2, y_2)

        other_quality: str = _get_quality_from_pitch(pitch)
        quality = quality_add(quality, other_quality)

    x_1, y_1 = points[index]
    x_2, y_2 = points[index + 1]
    f, pitch = _create_linear_function(x_1, y_1, x_2, y_2)

    return f(x), quality
