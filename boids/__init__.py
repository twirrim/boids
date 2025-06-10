import random
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


def calculate_flee_velocity(
    boid: Boid,
    predators: list[Boid],
    flee_speed: float,
    safe_distance: float = 1.0,  # To prevent division by zero
) -> Vector2:
    """
    Calculates a velocity vector to move away from a list of other positions.

    Args:
        boid: The boid that will be fleeing.
        predators: A list of predator boids to flee from.
        flee_speed: The desired speed of the fleeing object.
        safe_distance: A small value to avoid division by zero if objects are on top of each other.

    Returns:
        A Vector2 representing the velocity to move away.
    """
    if not predators:
        return Vector2(0, 0)

    # This will hold the sum of all repulsion vectors.
    total_repulsion_vector = Vector2(0, 0)

    for predator in predators:
        # Vector pointing from the other object to us
        diff = boid.position - predator.position

        # We use distance_squared_to for performance and to weight closer objects more heavily.
        dist_sq = boid.position.distance_squared_to(predator.position)

        # Avoid division by zero and extreme forces at very close range
        if dist_sq < safe_distance * safe_distance:
            dist_sq = safe_distance * safe_distance

        # Add the weighted vector: (difference / distance^2)
        # This makes closer objects have a much stronger repulsion effect.
        total_repulsion_vector += diff / dist_sq

    # Check if the total vector is not a zero vector
    if total_repulsion_vector.length() > 0:
        flee_direction = total_repulsion_vector.normalize()
    else:
        # Cannot normalize a zero vector. Stay put.
        return Vector2(0, 0)

    flee_velocity = flee_direction * flee_speed

    return flee_velocity


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
    boid: "Boid",
    grid: defaultdict[tuple[int, int], list["Boid"]],
    cell_size: float,
    # Boid rule parameters
    visible_range: float,
    protected_range: float,
    centering_factor: float,
    matching_factor: float,
    avoid_factor: float,
    # World parameters
    turn_factor: float,
    height: int,
    width: int,
    margin: int,
    # Speed parameters
    min_speed: float,
    max_speed: float,
) -> tuple[int, Vector2, Vector2, float, bool]:
    position_avg = Vector2(0.0, 0.0)
    velocity_avg = Vector2(0.0, 0.0)
    close_diff = Vector2(0.0, 0.0)
    neighboring_prey_count = 0
    nearby_predators = []

    boid_cell_x = int(boid.position.x // cell_size)
    boid_cell_y = int(boid.position.y // cell_size)

    # Iterate through the 3x3 grid of cells around the boid
    for cell_x_offset in range(-1, 2):
        for cell_y_offset in range(-1, 2):
            cell = (boid_cell_x + cell_x_offset, boid_cell_y + cell_y_offset)
            if cell in grid:
                for other_boid in grid[cell]:
                    if other_boid is boid:
                        continue

                    if not other_boid.alive:
                        continue

                    dist_sq = boid.position.distance_squared_to(other_boid.position)

                    if other_boid.predator:
                        # If I'm prey, check if I get eaten and note the predator's presence
                        if (
                            not boid.predator and dist_sq < 2**2
                        ):  # A small radius for being eaten
                            boid.alive = False
                            return boid.idx, Vector2(0, 0), Vector2(0, 0), 0.0, False
                        nearby_predators.append(other_boid)
                    else:  # other_boid is prey
                        # If I am a predator, I only care about prey within my visible range
                        if boid.predator:
                            if dist_sq < visible_range**2:
                                neighboring_prey_count += 1
                                position_avg += other_boid.position
                        # If I am prey, I follow boid rules with other prey
                        else:
                            if dist_sq < visible_range**2:
                                if dist_sq < protected_range**2:
                                    close_diff += boid.position - other_boid.position
                                else:
                                    position_avg += other_boid.position
                                    velocity_avg += other_boid.velocity
                                    neighboring_prey_count += 1

    # Start with the boid's current velocity and add forces to it
    next_velocity = boid.velocity

    # Prey logic
    if not boid.predator:
        # PRIORITY 1: Flee from predators if any are nearby
        if nearby_predators:
            predator_positions = [p for p in nearby_predators]
            flee_vector = calculate_flee_velocity(boid, predator_positions, max_speed)
            # Fleeing overrides all other flocking behaviors
            next_velocity = flee_vector
        # PRIORITY 2: Follow boid rules if no predators are around
        elif neighboring_prey_count > 0:
            position_avg /= neighboring_prey_count
            velocity_avg /= neighboring_prey_count

            # Cohesion Force (move toward center of mass)
            cohesion = (position_avg - boid.position) * centering_factor
            # Alignment Force (match velocity with neighbors)
            alignment = (velocity_avg - boid.velocity) * matching_factor
            # Separation Force (already calculated as close_diff)
            separation = close_diff * avoid_factor

            next_velocity += cohesion + alignment + separation

    # predator behaviour
    else:
        # If prey is visible, chase the center of the flock
        if neighboring_prey_count > 0:
            position_avg /= neighboring_prey_count
            # Simple "seek" behavior toward the average position of the flock
            chase_vector = position_avg - boid.position
            if chase_vector.length() > 0:
                next_velocity += chase_vector.normalize() * (
                    max_speed * 0.5
                )  # Move towards flock
        else:
            # No prey in sight, wander a bit to avoid standing still
            next_velocity += Vector2(random.uniform(-1, 1), random.uniform(-1, 1))

    if turn_factor > 0.0:
        if boid.position.y < margin:
            next_velocity.y += turn_factor
        elif boid.position.y > height - margin:
            next_velocity.y -= turn_factor
        if boid.position.x < margin:
            next_velocity.x += turn_factor
        elif boid.position.x > width - margin:
            next_velocity.x -= turn_factor

    final_velocity: Vector2
    speed = next_velocity.length()
    if speed > 0:
        # Use a single check to clamp speed between min and max
        final_speed = max(min_speed, min(speed, max_speed))
        # pygame.math.Vector2.scale_to_length is perfect for this!
        next_velocity.scale_to_length(final_speed)
        final_velocity = next_velocity
    else:
        # If velocity is zero, give it a nudge in a default direction
        final_velocity = Vector2(min_speed, 0)
        final_speed = min_speed

    final_position = boid.position + final_velocity

    return (boid.idx, final_position, final_velocity, final_speed, boid.alive)


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
        if not alive:
            boids[idx].colour = (0, 0, 0)
        boids[idx].position = final_position
        boids[idx].velocity = final_velocity
        boids[idx].current_speed = final_speed

        # Clamp to within borders
        boids[idx].position.x = max(0.0, min(float(width - 1), boids[idx].position.x))
        boids[idx].position.y = max(0.0, min(float(height - 1), boids[idx].position.y))
