QUALITY_MONO: str = "mono"
QUALITY_ANTI: str = "anti"
QUALITY_CONS: str = "constant"
QUALITY_ARB: str = "arbitrary"

ADD: dict = {
    QUALITY_MONO: {QUALITY_MONO: QUALITY_MONO,
                   QUALITY_ANTI: QUALITY_ARB,
                   QUALITY_CONS: QUALITY_MONO,
                   QUALITY_ARB: QUALITY_ARB},
    QUALITY_ANTI: {QUALITY_MONO: QUALITY_ARB,
                   QUALITY_ANTI: QUALITY_ANTI,
                   QUALITY_CONS: QUALITY_ANTI,
                   QUALITY_ARB: QUALITY_ARB},
    QUALITY_CONS: {QUALITY_MONO: QUALITY_MONO,
                   QUALITY_ANTI: QUALITY_ANTI,
                   QUALITY_CONS: QUALITY_CONS,
                   QUALITY_ARB: QUALITY_ARB},
    QUALITY_ARB: {QUALITY_MONO: QUALITY_ARB,
                  QUALITY_ANTI: QUALITY_ARB,
                  QUALITY_CONS: QUALITY_ARB,
                  QUALITY_ARB: QUALITY_ARB},
}

TIMES: dict = {
    QUALITY_MONO: {QUALITY_MONO: QUALITY_MONO,
                   QUALITY_ANTI: QUALITY_ANTI,
                   QUALITY_CONS: QUALITY_CONS,
                   QUALITY_ARB: QUALITY_ARB},
    QUALITY_ANTI: {QUALITY_MONO: QUALITY_ANTI,
                   QUALITY_ANTI: QUALITY_MONO,
                   QUALITY_CONS: QUALITY_CONS,
                   QUALITY_ARB: QUALITY_ARB},
    QUALITY_CONS: {QUALITY_MONO: QUALITY_CONS,
                   QUALITY_ANTI: QUALITY_CONS,
                   QUALITY_CONS: QUALITY_CONS,
                   QUALITY_ARB: QUALITY_ARB},
    QUALITY_ARB: {QUALITY_MONO: QUALITY_ARB,
                  QUALITY_ANTI: QUALITY_ARB,
                  QUALITY_CONS: QUALITY_ARB,
                  QUALITY_ARB: QUALITY_ARB},
}

SEARCH_LEFT: str = "left"
SEARCH_RIGHT: str = "right"
CORRECT_UPPER: str = "upper"
CORRECT_LOWER: str = "lower"
