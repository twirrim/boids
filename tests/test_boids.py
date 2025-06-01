from boids import get_colour_by_speed

# def get_colour_by_speed(speed: float, min_s: float, max_s: float)

MAX_SPEED = 3.0
MIN_SPEED = 0.5


def test_speed_at_min():
    assert get_colour_by_speed(MIN_SPEED, MIN_SPEED, MAX_SPEED) == (255, 0, 0)


def test_speed_below_min():
    assert get_colour_by_speed(MIN_SPEED - 0.1, MIN_SPEED, MAX_SPEED) == (255, 0, 0)
    assert get_colour_by_speed(-MIN_SPEED, MIN_SPEED, MAX_SPEED) == (255, 0, 0)


def test_speed_at_max():
    assert get_colour_by_speed(MAX_SPEED, MIN_SPEED, MAX_SPEED) == (0, 0, 255)


def test_speed_above_max():
    assert get_colour_by_speed(MAX_SPEED + 1.0, MIN_SPEED, MAX_SPEED) == (0, 0, 255)


def test_speed_mid_point():
    mid = (MIN_SPEED + MAX_SPEED) / 2.0
    assert get_colour_by_speed(mid, MIN_SPEED, MAX_SPEED) == (127, 0, 127)


def test_speed_quarter_point():
    speed_range = MAX_SPEED - MIN_SPEED
    quarter_speed = MIN_SPEED + 0.25 * speed_range
    assert get_colour_by_speed(quarter_speed, MIN_SPEED, MAX_SPEED) == (191, 0, 63)


def test_speed_three_quarter_point():
    speed_range = MAX_SPEED - MIN_SPEED
    three_quarter_speed = MIN_SPEED + 0.75 * speed_range
    assert get_colour_by_speed(three_quarter_speed, MIN_SPEED, MAX_SPEED) == (
        63,
        0,
        191,
    )
