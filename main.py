"""Simulation of Boids, written in python, and leveraging PyGame."""

import argparse
import os
import random
import sys
from pathlib import Path


import pygame
from tqdm import tqdm

from boids import Boid, update_boids, get_color_for_x


# Set up our constants
FPS = 60
MAX_SPEED = 3.0  # Value TBD
MIN_SPEED = 0.5  # Value TBD
MARGIN = 10  # Value TBD
VISIBLE_RANGE = 40.0  # Value TBD
VISIBLE_RANGE_SQUARED = VISIBLE_RANGE * VISIBLE_RANGE
PROTECTED_RANGE = 2  # Value TBD
PROTECTED_RANGE_SQUARED = PROTECTED_RANGE * PROTECTED_RANGE
AVOID_FACTOR = 0.05  # Value TBD
MATCHING_FACTOR = 0.05  # Value TBD
CENTERING_FACTOR = 0.0005  # Value TBD
TURN_FACTOR = 0.2  # Value TBD
# To make update_boids more efficient, we'll break things up into cells
CELL_SIZE = VISIBLE_RANGE * 1.1

# Colours (RGB tuples)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def present_directory(fpath: str):
    """For use with argparse, makes sure argument is for a valid directory"""
    source = Path(fpath)
    if not source.is_dir():
        raise argparse.ArgumentTypeError("Invalid directory {}".format(fpath))
    return source


def parse_args():
    args = argparse.ArgumentParser()
    args.add_argument(
        "--boids", required=True, type=int, help="Number of boids to simulate"
    )
    args.add_argument("--video", action="store_true")
    args.add_argument("--dir", type=present_directory)
    args.add_argument("--frames", type=int)
    args.add_argument("--profile", action="store_true")
    return args.parse_args()


def main() -> None:
    # Get arguments and carry out some validation
    args = parse_args()
    if args.video and not (args.frames and args.dir):
        print("You must provide --frames and --dir with --video")
        sys.exit(1)

    if args.profile:
        import cProfile
        import pstats

        profiler = cProfile.Profile()
        profiler.enable()

    # Set up pygame
    pygame.init()
    flags = pygame.DOUBLEBUF | pygame.FULLSCREEN | pygame.HWSURFACE
    # screen = pygame.display.set_mode((3280, 2160))
    screen = pygame.display.set_mode((3280, 2160), flags=flags)
    hardware_surface = pygame.Surface((screen.get_width(), screen.get_height()), flags)
    screen.blit(hardware_surface, (0, 0))
    pygame.display.set_caption("Boidy")
    clock = pygame.time.Clock()
    height = screen.get_height()
    width = screen.get_width()

    # Create our initial BOIDS
    random.seed(0)

    boids: list[Boid] = []
    for idx in range(args.boids):
        x = random.uniform(MARGIN, width - MARGIN)
        boids.append(
            Boid(
                idx,
                x,
                random.uniform(MARGIN, height - MARGIN),
                random.uniform(-MAX_SPEED / 2.0, MAX_SPEED / 2.0),
                random.uniform(-MAX_SPEED / 2.0, MAX_SPEED / 2.0),
                colour=get_color_for_x(x, width),
                predator=False,
                alive=True,
            )
        )

    # main loop
    running = True
    if args.frames:
        pbar = tqdm(total=args.frames)
    frame_count = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        hardware_surface.fill(BLACK)  # Clear the screen / set background
        update_boids(
            boids,
            height,
            width,
            MARGIN,
            MIN_SPEED,
            MAX_SPEED,
            VISIBLE_RANGE,
            PROTECTED_RANGE,
            AVOID_FACTOR,
            MATCHING_FACTOR,
            CENTERING_FACTOR,
            TURN_FACTOR,
        )

        for boid in boids:
            # Draw the boids
            pygame.draw.circle(
                hardware_surface, boid.colour, (int(boid.x), int(boid.y)), 2
            )
        screen.blit(hardware_surface, (0, 0))
        pygame.display.flip()  # Updates the entire screen

        if args.frames:
            pbar.update(1)
            frame_count += 1
            if frame_count > args.frames:
                running = False

        if args.video:
            filename = os.path.join(args.dir, f"frame_{frame_count:05d}.png")
            pygame.image.save(screen, filename)
        else:
            clock.tick(FPS)

    if args.profile:
        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats("cumulative")
        stats.print_stats(20)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
