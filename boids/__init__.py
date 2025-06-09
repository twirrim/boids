import math
import sys
from collections import defaultdict
from colorsys import hls_to_rgb
from dataclasses import dataclass

from pygame.math import Vector2


@dataclass
class Boid:
    """Representation of a boid."""

    idx: int
    position: Vector2
    velocity: Vector2
    current_speed: float = 0.0
    colour: tuple[int, int, int] = (0, 0, 0)
    predator: bool = False
    alive: bool = True


def get_colour_by_speed(
    speed: float,
    min_speed: float,
    max_speed: float,
) -> tuple[int, int, int]:
    """Calculates a colour based on speed,
    transitioning from red (slow) to blue (fast).
    """
    normalised_speed = (speed - min_speed) / (max_speed - min_speed)
    t = max(0.0, min(1.0, normalised_speed))  # Clamp t to [0, 1]

    red_val = int(255 * (1 - t))
    blue_val = int(255 * t)

    return (red_val, 0, blue_val)


def get_color_for_x(x: float, width: int) -> tuple[int, int, int]:
    """Calculates a vibrant RGB color based on a horizontal position."""
    hue = x / width
    lightness = 0.5
    saturation = 1.0
    r, g, b = hls_to_rgb(hue, lightness, saturation)
    return (int(r * 255), int(g * 255), int(b * 255))


def populate_grid(
    boids: list[Boid],
    cell_s: float,
) -> defaultdict[tuple[int, int], list[Boid]]:
    """Splits the display area into a grid, and identifies which square each boid should be in.
    This enables us to dramatically reduce comparisons between boids later on.
    """
    grid_dict = defaultdict(list)
    for boid in boids:
        # Determine which cell the boid belongs to.
        # I think I need floor division here?
        cell_x = int(boid.position.x // cell_s)
        cell_y = int(boid.position.y // cell_s)

        grid_dict[(cell_x, cell_y)].append(boid)
    return grid_dict


def get_change(
    boid: Boid,
    grid: defaultdict[tuple[int, int], list[Boid]],
    cell_size: float,
    visible_range: float,
    protected_range: float,
    centering_factor: float,
    matching_factor: float,
    avoid_factor: float,
    turn_factor: float,
    height,
    width,
    margin,
    min_speed: float,
    max_speed: float,
) -> tuple[int, Vector2, Vector2, float, bool]:
    position_avg = Vector2(0.0, 0.0)
    velocity_avg = Vector2(0.0, 0.0)
    close_diff = Vector2(0.0, 0.0)
    neighboring_boids_count = 0

    current_boid_position = boid.position
    current_boid_velocity = boid.velocity

    boid_cell_x = int(current_boid_position.x // cell_size)
    boid_cell_y = int(current_boid_position.y // cell_size)

    if boid.predator:
        # Predator specific behaviour
        nearest = Vector2(sys.float_info.max, sys.float_info.max)
        nearest_velocity = Vector2(0.0, 0.0)
        for cell_x_offset in range(-1, 2):
            for cell_y_offset in range(-1, 2):
                check_cell_x = boid_cell_x + cell_x_offset
                check_cell_y = boid_cell_y + cell_y_offset
                if (check_cell_x, check_cell_y) in grid:
                    for otherboid in grid[(check_cell_x, check_cell_y)]:
                        if otherboid is boid:
                            continue
                        if otherboid.alive and not otherboid.predator:
                            if boid.position.distance_to(
                                otherboid.position
                            ) < boid.position.distance_to(nearest):
                                nearest = otherboid.position
                                nearest_velocity = otherboid.velocity
        position_avg += nearest
        velocity_avg += nearest_velocity
        neighboring_boids_count = 1
    else:
        # Non-predator behaviour
        for cell_x_offset in range(-1, 2):
            for cell_y_offset in range(-1, 2):
                check_cell_x = boid_cell_x + cell_x_offset
                check_cell_y = boid_cell_y + cell_y_offset
                if (check_cell_x, check_cell_y) in grid:
                    for otherboid in grid[(check_cell_x, check_cell_y)]:
                        if otherboid is boid:
                            continue

                        if otherboid.predator and otherboid.position == boid.position:
                            boid.alive = False
                            return (boid.idx, Vector2(0.0, 0.0), Vector2(0.0, 0.0), 0.0, False)

                        diff = current_boid_position - otherboid.position
                        squared_distance = diff.length_squared()
                        if squared_distance < visible_range:
                            if squared_distance < protected_range**2:
                                close_diff += diff
                            elif squared_distance < visible_range**2:
                                position_avg += otherboid.position
                                velocity_avg += otherboid.velocity
                                neighboring_boids_count += 1

    # Start with the boid's original velocity for this frame's calculation
    next_velocity = current_boid_velocity

    if neighboring_boids_count:
        position_avg /= neighboring_boids_count
        velocity_avg /= neighboring_boids_count
        if not boid.predator:
            next_velocity += Vector2(
                (position_avg.x - current_boid_position.x) * centering_factor
                + (velocity_avg.x - current_boid_velocity.x) * matching_factor,
                (position_avg.y - current_boid_position.y) * centering_factor
                + (velocity_avg.y - current_boid_velocity.y) * matching_factor,
            )
            next_velocity += close_diff * avoid_factor
        else:
            next_velocity += Vector2(
                (position_avg.x - current_boid_position.x)
                + (velocity_avg.x - current_boid_velocity.x),
                (position_avg.y - current_boid_position.y)
                + (velocity_avg.y - current_boid_velocity.y),
            )

    if turn_factor > 0.0:  # Don't bother turning if we don't have a turn factor
        if current_boid_position.y > height - margin:
            next_velocity.y -= turn_factor
        elif current_boid_position.y < margin:
            next_velocity.y += turn_factor

        if current_boid_position.x > width - margin:
            next_velocity.x -= turn_factor
        elif current_boid_position.x < margin:
            next_velocity.x += turn_factor

    current_calculated_speed = current_boid_velocity.length()

    final_current_speed = 0.0
    final_velocity = next_velocity

    if current_calculated_speed > 0.0:
        if current_calculated_speed < min_speed:
            factor = min_speed / current_calculated_speed
            final_velocity = next_velocity * factor
            final_current_speed = min_speed
        elif current_calculated_speed > max_speed:
            factor = max_speed / current_calculated_speed
            final_velocity = next_velocity * factor
            final_current_speed = max_speed
        else:
            final_current_speed = current_calculated_speed
            # final_xv, final_yv already correctly set from calc_next_xv/yv
    elif min_speed > 0.0:  # Nudge if calculated speed is zero but min_speed is not
        angle = math.pi / 4
        final_velocity.x = min_speed * math.cos(angle)
        final_velocity.y = min_speed * math.sin(angle)
        final_current_speed = min_speed

    final_position = current_boid_position + final_velocity

    return (boid.idx, final_position, final_velocity, final_current_speed, boid.alive)


def update_boids(
    boids: list[Boid],
    height: int,
    width: int,
    margin: int,
    min_speed: float,
    max_speed: float,
    visible_range: float,
    protected_range: float,
    avoid_factor: float,
    matching_factor: float,
    centering_factor: float,
    turn_factor: float,
) -> None:
    """Update the location and velocity of every boid."""
    cell_size = visible_range * 1.1
    grid: defaultdict[tuple[int, int], list[Boid]] = populate_grid(boids, cell_size)

    new_states_to_apply: list[tuple[int, Vector2, Vector2, float, bool]] = [
        get_change(
            boid,
            grid,
            cell_size,
            visible_range,
            protected_range,
            centering_factor,
            matching_factor,
            avoid_factor,
            turn_factor,
            height,
            width,
            margin,
            min_speed,
            max_speed,
        )
        for boid in boids
        if boid.alive
    ]

    # Then apply
    for new_state in new_states_to_apply:
        idx, final_position, final_velocity, final_speed, alive = new_state
        boids[idx].position = final_position
        boids[idx].velocity = final_velocity
        boids[idx].current_speed = final_speed

        # Clamp to within borders
        boids[idx].position.x = max(0.0, min(float(width - 1), boids[idx].position.x))
        boids[idx].position.y = max(0.0, min(float(height - 1), boids[idx].position.y))
