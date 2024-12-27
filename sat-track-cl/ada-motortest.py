import time
import board
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper

kit = MotorKit(i2c=board.I2C())

run = True

for i in range(200):
    kit.stepper1.onestep()