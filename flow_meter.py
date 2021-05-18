#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pprint
import time
import struct

import iol_driver


try:
    spi = iol_driver.com_init()
    ser = iol_driver.com_start(spi)

# iol_driver.dir_param_read(spi, ser, 0x01)
# iol_driver.dir_param_read(spi, ser, 0x02)
# iol_driver.dir_param_read(spi, ser, 0x03)

    print(iol_driver.isdu_read(spi, ser, 0x94, iol_driver.DATA_TYPE_INTEGER) * 0.01)
    iol_driver.com_stop(spi, ser)
except RuntimeError as e:
    print('ERROR:', e)
    iol_driver.com_stop(spi, ser, True)
