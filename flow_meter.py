#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import spidev
import pprint
import time
import serial
import RPi.GPIO as GPIO
import struct
import sys

import iol_driver
    
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 100000
spi.mode = 0


time.sleep(1)

ser = iol_driver.com_start(spi)

iol_driver.dir_param_read(spi, ser, 0x01)
iol_driver.dir_param_read(spi, ser, 0x02)
iol_driver.dir_param_read(spi, ser, 0x03)

