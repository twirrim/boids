"""Simulation of Boids, written in python, and leveraging PyGame."""

import math
import random
import sys
from dataclasses import dataclass

import pygame


@dataclass
class Boid:
    """Representation of a boid."""

    x: float
    y: float
    xv: float
    yv: float
    current_speed: float = 0.0


# Set up our constants
FPS = 60
BOID_COUNT = 1000
AVOID_FACTOR = 0.05  # Value TBD
MATCHING_FACTOR = 0.05  # Value TBD
CENTERING_FACTOR = 0.0005  # Value TBD
TURN_FACTOR = 0.2  # Value TBD
VISIBLE_RANGE = 20.0  # Value TBD
VISIBLE_RANGE_SQUARED = VISIBLE_RANGE * VISIBLE_RANGE
MAX_SPEED = 3.0  # Value TBD
MIN_SPEED = 0.5  # Value TBD
PROTECTED_RANGE = 2
PROTECTED_RANGE_SQUARED = PROTECTED_RANGE * PROTECTED_RANGE
MARGIN = 10  # Value TBD

# Colours (RGB tuples)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def get_colour_by_speed(speed: float) -> tuple[int, int, int]:
    """
    Calculates a colour based on speed,
    transitioning from red (slow) to blue (fast).
    """

    normalized_speed = (speed - MIN_SPEED) / (MAX_SPEED - MIN_SPEED)
    t = max(0.0, min(1.0, normalized_speed))  # Clamp t to [0, 1]

    red_val = int(255 * (1 - t))
    blue_val = int(255 * t)

    return (red_val, 0, blue_val)


def update_boids(boids: list[Boid]) -> None:
    """Update the location and velocity of every boid."""

    for bidx, boid in enumerate(boids):
        xpos_avg: float = 0.0
        ypos_avg: float = 0.0
        xvel_avg: float = 0.0
        yvel_avg: float = 0.0
        neighboring_boids: int = 0
        close_dx: float = 0.0
        close_dy: float = 0.0
        for cidx, otherboid in enumerate(boids):
            if cidx == bidx:
                continue
            dx = boid.x - otherboid.x
            dy = boid.y - otherboid.y
            if abs(dx) < VISIBLE_RANGE and abs(dy) < VISIBLE_RANGE:
                squared_distance = dx * dx + dy * dy
                if squared_distance < PROTECTED_RANGE_SQUARED:
                    close_dx += boid.x - otherboid.x
                    close_dy += boid.y - otherboid.y
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

            boid.xv = (
                boid.xv
                + (xpos_avg - boid.x) * CENTERING_FACTOR
                + (xvel_avg - boid.xv) * MATCHING_FACTOR
            )

            boid.yv = (
                boid.yv
                + (ypos_avg - boid.y) * CENTERING_FACTOR
                + (yvel_avg - boid.yv) * MATCHING_FACTOR
            )
        boid.xv = boid.xv + (close_dx * AVOID_FACTOR)
        boid.yv = boid.yv + (close_dy * AVOID_FACTOR)

        # Keep them in the screen
        if boid.y > screen.get_height() - MARGIN:
            boid.yv = boid.yv - TURN_FACTOR
        if boid.x > screen.get_width() - MARGIN:
            boid.xv = boid.xv - TURN_FACTOR
        if boid.x < MARGIN:
            boid.xv = boid.xv + TURN_FACTOR
        if boid.y < MARGIN:
            boid.yv = boid.yv + TURN_FACTOR

        # Make sure we're within speed limits
        speed = math.sqrt(boid.xv * boid.xv + boid.yv * boid.yv)
        if speed > 0:  # Avoid division by 0
            if speed < MIN_SPEED:
                factor = MIN_SPEED / speed
                boid.xv *= factor
                boid.yv *= factor
                boid.current_speed = MIN_SPEED
            elif speed > MAX_SPEED:
                factor = MAX_SPEED / speed
                boid.xv *= factor
                boid.yv *= factor
                boid.current_speed = MAX_SPEED
            else:
                boid.current_speed = speed
        elif MIN_SPEED > 0:  # If speed is 0 give it a nudge
            boid.xv = random.uniform(-MIN_SPEED, MIN_SPEED)
            boid.yv = random.uniform(-MIN_SPEED, MIN_SPEED)
            boid.current_speed = MIN_SPEED

        # Update boid's position
        boid.x = boid.x + boid.xv
        boid.y = boid.y + boid.yv


# Set up pygame
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Boidy")
clock = pygame.time.Clock()

# Create our initial BOIDS
random.seed()

boids: list[Boid] = [
    Boid(
        random.uniform(0.0, float(screen.get_width() - MARGIN)),
        random.uniform(0.0, float(screen.get_height() - MARGIN)),
        random.uniform(-MAX_SPEED / 2.0, MAX_SPEED / 2.0),
        random.uniform(-MAX_SPEED / 2.0, MAX_SPEED / 2.0),
    )
    for _ in range(BOID_COUNT)
]


# main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    screen.fill(BLACK)  # Clear the screen / set background
    update_boids(boids)

    for boid in boids:
        # Figure out the colour
        colour = get_colour_by_speed(boid.current_speed)
        # Draw the boids
        pygame.draw.circle(screen, colour, (int(boid.x), int(boid.y)), 2)

    pygame.display.flip()  # Updates the entire screen

    clock.tick(FPS)

pygame.quit()
sys.exit()
