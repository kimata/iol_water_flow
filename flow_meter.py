#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# KEYENCE のクランプオン式流量センサ FD-Q10C と IO-LINK で通信を行なって
# 流量を取得するスクリプトです．

import time
import struct

import iol_driver

def sense():
    try:
        spi = iol_driver.com_init()
        ser = iol_driver.com_start(spi)

        flow = iol_driver.isdu_read(spi, ser, 0x94, iol_driver.DATA_TYPE_INTEGER) * 0.01
        iol_driver.com_stop(spi, ser)

        return { 'flow': round(flow, 2) }
    except RuntimeError as e:
        iol_driver.com_stop(spi, ser, True)
        raise


if __name__ == '__main__':
    import pprint

    pprint.pprint(sense())
