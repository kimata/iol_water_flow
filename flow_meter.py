#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import spidev
import pprint
import time
import struct

import iol_driver
    
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 100000
spi.mode = 0

ser = iol_driver.com_start(spi)

iol_driver.dir_param_read(spi, ser, 0x01)
iol_driver.dir_param_read(spi, ser, 0x02)
iol_driver.dir_param_read(spi, ser, 0x03)

iol_driver.dir_param_write(spi, ser, 0x00, 0x95)
iol_driver.dir_param_write(spi, ser, 0x00, 0x9A)

print(iol_driver.isdu_read(spi, ser, 0x11, iol_driver.DATA_TYPE_STRING))

iol_driver.com_stop(spi, ser)
