import time

import pygame

pygame.joystick.init()
print("Joysticks found:", pygame.joystick.get_count())
joy = pygame.joystick.Joystick(0)
print(joy.get_name(), joy.get_numaxes(), "axes", joy.get_numbuttons(), "buttons", joy.get_numhats(), "hats")

while True:
    pygame.event.pump()
    axes = [round(joy.get_axis(i), 2) for i in range(joy.get_numaxes())]
    print(axes, end="\r")
    time.sleep(0.1)