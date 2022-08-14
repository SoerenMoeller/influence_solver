import bisect

from .constants import *


def fetch_image_name(quality: str, color: str):
    if quality == QUALITY_ANTI:
        return f"anti_{color}.png"
    elif quality == QUALITY_ARB:
        return f"arbitrary_{color}.png"
    elif quality == QUALITY_MONO:
        return f"mono_{color}.png"
    elif quality == QUALITY_CONS:
        return f"const_{color}.png"
    else:
        assert False, f"Checked for unknown quality image name: {quality}"


def min_quality(quality_a: str, quality_b: str) -> str:
    if quality_a == quality_b:
        return quality_a
    elif quality_a == QUALITY_CONS or quality_b == QUALITY_CONS:
        return QUALITY_CONS
    elif quality_a == QUALITY_ARB and quality_b != QUALITY_ARB:
        return quality_b
    elif quality_b == QUALITY_ARB and quality_a != QUALITY_ARB:
        return quality_a
    elif quality_a == QUALITY_MONO and quality_b in QUALITY_ANTI or \
            quality_b == QUALITY_MONO and quality_a == QUALITY_ANTI:
        return QUALITY_CONS
    elif (quality_a == QUALITY_ANTI or quality_a == QUALITY_ANTI) and quality_b == QUALITY_CONS:
        return quality_a
    elif (quality_b == QUALITY_ANTI or quality_b == QUALITY_ANTI) and quality_a == QUALITY_CONS:
        return quality_b
    else:
        assert False, f"Tried to minimize unknown quality pair: {quality_a}, {quality_b}"


def quality_add(quality_a: str, quality_b: str) -> str:
    return ADD[quality_a][quality_b]


def quality_times(quality_a: str, quality_b: str) -> str:
    return TIMES[quality_a][quality_b]


def is_stronger_as(quality_a: str, quality_b: str) -> bool:
    if quality_b == QUALITY_ARB or quality_a == QUALITY_CONS:
        return True
    elif quality_a == QUALITY_ARB:
        return True if quality_b == QUALITY_ARB else False
    elif quality_a == QUALITY_MONO:
        return True if quality_b in [QUALITY_MONO, QUALITY_ARB] else False
    elif quality_a == QUALITY_ANTI:
        return True if quality_b in [QUALITY_ANTI, QUALITY_ARB] else False
    else:
        assert False, f"Tried to strengthen unknown quality pair: {quality_a}, {quality_b}"


def get_overlap_index(boundaries: list[float], begin, end=None) -> tuple[int, int]:
    if end is None:
        return get_overlap_index(boundaries, begin.begin, begin.end)

    left: int = bisect.bisect_left(boundaries, begin)
    right: int = bisect.bisect_right(boundaries, end)
    return left, right
