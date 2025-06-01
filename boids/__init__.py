import math
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Boid:
    """Representation of a boid."""

    idx: int
    x: float
    y: float
    xv: float
    yv: float
    current_speed: float = 0.0


def get_colour_by_speed(
    speed: float, min_speed: float, max_speed: float
) -> tuple[int, int, int]:
    """
    Calculates a colour based on speed,
    transitioning from red (slow) to blue (fast).
    """

    normalised_speed = (speed - min_speed) / (max_speed - min_speed)
    t = max(0.0, min(1.0, normalised_speed))  # Clamp t to [0, 1]

    red_val = int(255 * (1 - t))
    blue_val = int(255 * t)

    return (red_val, 0, blue_val)


def populate_grid(
    boids: list[Boid], cell_s: float
) -> defaultdict[tuple[int, int], list[Boid]]:
    """Splits the display area into a grid, and identifies which square each boid should be in.
    This enables us to dramatically reduce comparisons between boids later on.
    """
    grid_dict = defaultdict(list)
    for boid in boids:
        # Determine which cell the boid belongs to.
        # I think I need floor division here
        cell_x = int(boid.x // cell_s)
        cell_y = int(boid.y // cell_s)

        grid_dict[(cell_x, cell_y)].append(boid)
    return grid_dict


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

    new_states_to_apply = []  # List of tuples: (idx, final_x, final_y, final_xv, final_yv, final_current_speed)
    for boid_readonly in boids:
        xpos_avg, ypos_avg, xvel_avg, yvel_avg = 0.0, 0.0, 0.0, 0.0
        neighboring_boids_count = 0
        close_dx, close_dy = 0.0, 0.0

        current_boid_x = boid_readonly.x
        current_boid_y = boid_readonly.y
        current_boid_xv = boid_readonly.xv
        current_boid_yv = boid_readonly.yv

        boid_cell_x = int(current_boid_x // cell_size)
        boid_cell_y = int(current_boid_y // cell_size)

        for cell_x_offset in range(-1, 2):
            for cell_y_offset in range(-1, 2):
                check_cell_x = boid_cell_x + cell_x_offset
                check_cell_y = boid_cell_y + cell_y_offset
                if (check_cell_x, check_cell_y) in grid:
                    for otherboid_readonly in grid[(check_cell_x, check_cell_y)]:
                        if otherboid_readonly is boid_readonly:
                            continue

                        dx = current_boid_x - otherboid_readonly.x
                        dy = current_boid_y - otherboid_readonly.y

                        if abs(dx) < visible_range and abs(dy) < visible_range:
                            squared_distance = dx * dx + dy * dy
                            if squared_distance < protected_range**2:
                                close_dx += dx
                                close_dy += dy
                            elif squared_distance < visible_range**2:
                                xpos_avg += otherboid_readonly.x
                                ypos_avg += otherboid_readonly.y
                                xvel_avg += otherboid_readonly.xv
                                yvel_avg += otherboid_readonly.yv
                                neighboring_boids_count += 1

        # Start with the boid's original velocity for this frame's calculation
        calc_next_xv = current_boid_xv
        calc_next_yv = current_boid_yv

        if neighboring_boids_count:
            xpos_avg /= neighboring_boids_count
            ypos_avg /= neighboring_boids_count
            xvel_avg /= neighboring_boids_count
            yvel_avg /= neighboring_boids_count

            calc_next_xv += (xpos_avg - current_boid_x) * centering_factor + (
                xvel_avg - current_boid_xv
            ) * matching_factor
            calc_next_yv += (ypos_avg - current_boid_y) * centering_factor + (
                yvel_avg - current_boid_yv
            ) * matching_factor

        calc_next_xv += close_dx * avoid_factor
        calc_next_yv += close_dy * avoid_factor

        if turn_factor > 0.0:  # Don't bother turning if we don't have a turn factor
            if current_boid_y > height - margin:
                calc_next_yv -= turn_factor
            if current_boid_x > width - margin:
                calc_next_xv -= turn_factor
            if current_boid_x < margin:
                calc_next_xv += turn_factor
            if current_boid_y < margin:
                calc_next_yv += turn_factor

        current_calculated_speed = math.sqrt(calc_next_xv**2 + calc_next_yv**2)

        final_xv = calc_next_xv
        final_yv = calc_next_yv
        final_current_speed = 0.0

        if current_calculated_speed > 0.0:
            if current_calculated_speed < min_speed:
                factor = min_speed / current_calculated_speed
                final_xv = calc_next_xv * factor
                final_yv = calc_next_yv * factor
                final_current_speed = min_speed
            elif current_calculated_speed > max_speed:
                factor = max_speed / current_calculated_speed
                final_xv = calc_next_xv * factor
                final_yv = calc_next_yv * factor
                final_current_speed = max_speed
            else:
                final_current_speed = current_calculated_speed
                # final_xv, final_yv already correctly set from calc_next_xv/yv
        elif min_speed > 0.0:  # Nudge if calculated speed is zero but min_speed is not
            angle = math.pi / 4
            final_xv = min_speed * math.cos(angle)
            final_yv = min_speed * math.sin(angle)
            final_current_speed = min_speed

        final_x = current_boid_x + final_xv
        final_y = current_boid_y + final_yv

        new_states_to_apply.append(
            (
                boid_readonly.idx,
                final_x,
                final_y,
                final_xv,
                final_yv,
                final_current_speed,
            )
        )

    # Then apply
    for new_state in new_states_to_apply:
        idx, final_x, final_y, final_xv, final_yv, final_current_speed = new_state
        boids[idx].x = final_x
        boids[idx].y = final_y
        boids[idx].xv = final_xv
        boids[idx].yv = final_yv
        boids[idx].current_speed = final_current_speed

        # Clamp to within borders
        boids[idx].x = max(0.0, min(float(width - 1), boids[idx].x))
        boids[idx].y = max(0.0, min(float(height - 1), boids[idx].y))
