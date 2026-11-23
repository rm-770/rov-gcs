"""Shows live axis and button values for the first controller. Ctrl+C to stop."""

import os
import time

import pygame

# "dummy" means SDL opens no real window. This must be set before display.init().
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.display.init()    # pump()/get() need the display subsystem running
pygame.joystick.init()

count = pygame.joystick.get_count()
print("Joysticks found:", count)
if count == 0:
    raise SystemExit("No controller found. Wake it (press the PS button) and try again.")

joy = pygame.joystick.Joystick(0)
print(joy.get_name(), joy.get_numaxes(), "axes", joy.get_numbuttons(), "buttons",
      joy.get_numhats(), "hats")
print("Move one stick or press one button at a time. Ctrl+C to stop.")

try:
    while True:
        pygame.event.pump()    # refresh joystick state from the OS
        axes = [round(joy.get_axis(i), 2) for i in range(joy.get_numaxes())]
        # Collect the numbers of every button currently held down.
        pressed = [i for i in range(joy.get_numbuttons()) if joy.get_button(i)]
        line = f"axes={axes} buttons_down={pressed}"
        # The padding overwrites leftovers from a previous, longer line.
        print(f"{line:<110}", end="\r")
        time.sleep(0.05)
except KeyboardInterrupt:
    print()