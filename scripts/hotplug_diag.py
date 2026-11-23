"""Prints everything pygame knows about joysticks. Run it, then plug/unplug the controller."""

import os
import sys
import time

# Ask SDL to deliver joystick events even when no window has focus.
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

import pygame

use_window = "--window" in sys.argv   # compare: real window vs. the headless dummy driver

if not use_window:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

pygame.display.init()
pygame.joystick.init()
if use_window:
    pygame.display.set_mode((300, 100))   # a tiny real window, so SDL has something to attach to

print("Video driver:", pygame.display.get_driver())
print("Joysticks at startup:", pygame.joystick.get_count())
for i in range(pygame.joystick.get_count()):
    print("  ", i, pygame.joystick.Joystick(i).get_name())

print("Plug / unplug the controller. Ctrl+C to stop.")
joysticks = {}   # instance_id -> Joystick. Holding the reference keeps the device open.
try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYDEVICEADDED:
                # Opening the joystick registers it with pygame so later events work.
                joy = pygame.joystick.Joystick(event.device_index)
                joysticks[joy.get_instance_id()] = joy
                print("CONNECTED:", joy.get_name(), "instance", joy.get_instance_id())
            elif event.type == pygame.JOYDEVICEREMOVED:
                joysticks.pop(event.instance_id, None)
                print("DISCONNECTED: instance", event.instance_id)
        time.sleep(0.05)
except KeyboardInterrupt:
    pass