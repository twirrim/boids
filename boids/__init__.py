import math
import random
from dataclasses import dataclass
from collections import defaultdict

VISIBLE_RANGE = 20.0  # Value TBD
VISIBLE_RANGE_SQUARED = VISIBLE_RANGE * VISIBLE_RANGE
PROTECTED_RANGE = 2  # Value TBD
PROTECTED_RANGE_SQUARED = PROTECTED_RANGE * PROTECTED_RANGE
AVOID_FACTOR = 0.05  # Value TBD
MATCHING_FACTOR = 0.05  # Value TBD
CENTERING_FACTOR = 0.0005  # Value TBD
TURN_FACTOR = 0.2  # Value TBD

# To make update_boids more efficient, we'll break things up into cells
CELL_SIZE = VISIBLE_RANGE * 1.1


@dataclass
class Boid:
    """Representation of a boid."""

    x: float
    y: float
    xv: float
    yv: float
    current_speed: float = 0.0

def get_colour_by_speed(speed: float, min_speed: float, max_speed: float) -> tuple[int, int, int]:
    """
    Calculates a colour based on speed,
    transitioning from red (slow) to blue (fast).
    """

    normalised_speed = (speed - min_speed) / (max_speed - min_speed)
    t = max(0.0, min(1.0, normalised_speed))  # Clamp t to [0, 1]

    red_val = int(255 * (1 - t))
    blue_val = int(255 * t)

    return (red_val, 0, blue_val)

def populate_grid(boids: list[Boid], cell_s: float) -> defaultdict[tuple[int,int], list[Boid]]:
    grid_dict = defaultdict(list)
    for boid in boids:
        # Determine which cell the boid belongs to.
        # I think I need floor division here
        cell_x = int(boid.x // cell_s)
        cell_y = int(boid.y // cell_s)

        grid_dict[(cell_x, cell_y)].append(boid)
    return grid_dict

def update_boids(boids: list[Boid], height, width, margin, min_speed, max_speed) -> None:
    """Update the location and velocity of every boid."""

    grid: defaultdict[tuple[int, int], list[Boid]] = populate_grid(boids, CELL_SIZE)

    for boid in boids:
        xpos_avg: float = 0.0
        ypos_avg: float = 0.0
        xvel_avg: float = 0.0
        yvel_avg: float = 0.0
        neighboring_boids: int = 0
        close_dx: float = 0.0
        close_dy: float = 0.0

        # find out our what cell we're in
        boid_cell_x = int(boid.x // CELL_SIZE)
        boid_cell_y = int(boid.y // CELL_SIZE)

        for cell_x_offset in range(-1, 2):
            for cell_y_offset in range(-1, 2):
                check_cell_x = boid_cell_x + cell_x_offset
                check_cell_y = boid_cell_y + cell_y_offset
                # check if it is in the grid (also eliminates cases where we'd go out of bounds)
                if (check_cell_x, check_cell_y) in grid:
                    for otherboid in grid[(check_cell_x, check_cell_y)]:
                        if otherboid is boid:
                            continue
                        dx = boid.x - otherboid.x
                        dy = boid.y - otherboid.y

                        if abs(dx) < VISIBLE_RANGE and abs(dy) < VISIBLE_RANGE:
                            squared_distance = dx * dx + dy * dy
                            if squared_distance < PROTECTED_RANGE_SQUARED:
                                close_dx += dx
                                close_dy += dy
                            elif squared_distance < VISIBLE_RANGE_SQUARED:
                                xpos_avg += otherboid.x
                                ypos_avg += otherboid.y
                                xvel_avg += otherboid.xv
                                yvel_avg += otherboid.yv
                                neighboring_boids += 1
        if neighboring_boids:
            xpos_avg = xpos_avg / neighboring_boids
            ypos_avg = ypos_avg / neighboring_boids
            xvel_avg = xvel_avg / neighboring_boids
            yvel_avg = yvel_avg / neighboring_boids

            boid.xv += (xpos_avg - boid.x) * CENTERING_FACTOR + \
                       (xvel_avg - boid.xv) * MATCHING_FACTOR

            boid.yv += (ypos_avg - boid.y) * CENTERING_FACTOR + \
                       (yvel_avg - boid.yv) * MATCHING_FACTOR

        boid.xv += close_dx * AVOID_FACTOR
        boid.yv += close_dy * AVOID_FACTOR

        # Keep them in the screen
        if boid.y > height - margin:
            boid.yv = boid.yv - TURN_FACTOR
        if boid.x > width - margin:
            boid.xv = boid.xv - TURN_FACTOR
        if boid.x < margin:
            boid.xv = boid.xv + TURN_FACTOR
        if boid.y < margin:
            boid.yv = boid.yv + TURN_FACTOR

        # Make sure we're within speed limits
        speed = math.sqrt(boid.xv * boid.xv + boid.yv * boid.yv)
        if speed > 0:  # Avoid division by 0
            if speed < min_speed:
                factor = min_speed / speed
                boid.xv *= factor
                boid.yv *= factor
                boid.current_speed = min_speed
            elif speed > max_speed:
                factor = max_speed / speed
                boid.xv *= factor
                boid.yv *= factor
                boid.current_speed = max_speed
            else:
                boid.current_speed = speed
        elif min_speed > 0:  # If speed is 0 give it a nudge
            boid.xv = random.uniform(-min_speed, min_speed)
            boid.yv = random.uniform(-min_speed, min_speed)
            boid.current_speed = min_speed

        # Update boid's position
        boid.x = boid.x + boid.xv
        boid.y = boid.y + boid.yv
