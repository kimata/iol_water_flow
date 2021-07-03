#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ADI の LTC2874 を使って，IO-LINK 通信を行うラブラリです．

import spidev
import serial
import struct
import logging
import logging.handlers
import pprint
import time

import io_link as io_link

DEBUG = True

DATA_TYPE_RAW = 0
DATA_TYPE_STRING = 1
DATA_TYPE_UINT16 = 2

logger = logging.getLogger(__name__)

log_handler = logging.handlers.RotatingFileHandler(
    '/dev/shm/io_link.log',
    encoding='utf8', maxBytes=1*1024*1024, backupCount=10,
)
log_handler.formatter = logging.Formatter(
    fmt='%(asctime)s %(levelname)s %(name)s - %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S %Z'
)

if DEBUG:
    logger.addHandler(log_handler)
    logger.setLevel(logging.DEBUG)
else:
    logger.addHandler(logging.NullHandler())


def error(message):
    logger.error(message)
    raise RuntimeError(message)


def warn(message):
    logger.warn(message)


def info(message):
    logger.info(message)


def dump_byte_list(label, byte_list):
    logger.info('{}: {}'.format(label, ', '.join(hex(x) for x in byte_list)))


def ltc2874_reg_read(spi, reg):
    return spi.xfer2([ (0x00 << 5) | (reg << 1), 0x00])[1]


def ltc2874_reg_write(spi, reg, data):
    spi.xfer2([ (0x03 << 5) | (reg << 1), data])


def msq_checksum(data):
    chk = 0x52
    for d in data:
        chk ^= d
    chk = ((((chk >> 7) ^ (chk >> 5) ^ (chk >> 3) ^ (chk >> 1)) & 1) << 5) | \
         ((((chk >> 6) ^ (chk >> 4) ^ (chk >> 2) ^ (chk >> 0)) & 1) << 4)  | \
         ((((chk >> 7) ^ (chk >> 6)) & 1) << 3)  | \
         ((((chk >> 5) ^ (chk >> 4)) & 1) << 2)  | \
         ((((chk >> 3) ^ (chk >> 2)) & 1) << 1)  | \
         ((((chk >> 1) ^ (chk >> 0)) & 1) << 0)
    return chk


def msq_build(rw, ch, addr, mtype, data):
    mc = (rw << 7) | (ch << 5) | (addr)
    cht = (mtype << 6)

    msq = [mc, cht]

    if (data is not None):
        msq.extend(data)

    cht |= msq_checksum(msq)
    msq[1] = cht

    return msq


def com_open():
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1000
    spi.mode = 0

    return spi


def com_close(spi):
    spi.close()


def com_start(spi):
    enl1 = ltc2874_reg_read(spi, 0x0E)

    if enl1 != 0x11:
        # Power on, CQ OC Timeout = 480us
        info('***** Power-On IO-Link ****')
        ltc2874_reg_write(spi, 0x0E, 0x11)
        time.sleep(2)

    # Wakeup
    ltc2874_reg_write(spi, 0x0D, 0x10)

    # Drive enable
    ltc2874_reg_write(spi, 0x0D, 0x01)

    return serial.Serial(
        port="/dev/ttyAMA0",
        baudrate=38400,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.01,
    )


def com_stop(spi, ser, is_power_off=False):
    ser.close()
    # Drive disable
    ltc2874_reg_write(spi, 0x0D, 0x00)

    if is_power_off:
        # Power off
        info('***** Power-Off IO-Link ****')
        ltc2874_reg_write(spi, 0x0E, 0x00)


def com_write(spi, ser, byte_list):
    # Drive enable
    ltc2874_reg_write(spi, 0x0D, 0x01)

    dump_byte_list('SEND', byte_list)

    ser.write(struct.pack('{}B'.format(len(byte_list)), *byte_list))
    ser.flush()

    # Drive disable
    ltc2874_reg_write(spi, 0x0D, 0x00)


def com_read(spi, ser, length):
    recv = ser.read(length)
    byte_list = struct.unpack('{}B'.format(len(recv)), recv)

    dump_byte_list('RECV', byte_list)

    return byte_list
    

def dir_param_read(spi, ser, addr):
    info('***** CALL: dir_param_read(addr: 0x{:x}) ****'.format(addr))

    msq = msq_build(io_link.MSQ_RW_READ, io_link.MSQ_CH_PAGE,
                    addr, io_link.MSQ_TYPE_0, None)
    com_write(spi, ser, msq)

    data = com_read(spi, ser, 4)[2:]

    if (len(data) < 2):
        error('response is too short')
    elif (data[1] != msq_checksum([data[0]])):
        error('checksum unmatch')

    return data[0]


def dir_param_write(spi, ser, addr, value):
    info('***** CALL: dir_param_write(addr: 0x{:x}, value: 0x{:x}) ****'.format(addr, value))

    msq = msq_build(io_link.MSQ_RW_WRITE, io_link.MSQ_CH_PAGE,
                    addr, io_link.MSQ_TYPE_0, [value])
    com_write(spi, ser, msq)

    data = com_read(spi, ser, 4)[3:]

    if (len(data) < 1):
        error('response is too short')
    elif (data[0] != msq_checksum([])):
        error('checksum unmatch')


def isdu_req_build(index):
    rw = io_link.MSQ_RW_WRITE
    isrv = io_link.ISDU_ISRV_READ_8BIT_IDX
    length = 3

    return [
        msq_build(rw, io_link.MSQ_CH_ISDU, 0x10, io_link.MSQ_TYPE_0,
                  [(isrv << 4) | length]),
        msq_build(rw, io_link.MSQ_CH_ISDU, 0x01, io_link.MSQ_TYPE_0,
                  [index]),
        msq_build(rw, io_link.MSQ_CH_ISDU, 0x02, io_link.MSQ_TYPE_0,
                  [((isrv << 4) | length) ^ index]),
    ]


def isdu_res_read(spi, ser, flow):
    msq = msq_build(io_link.MSQ_RW_READ, io_link.MSQ_CH_ISDU,
                    flow, io_link.MSQ_TYPE_0, None)
    com_write(spi, ser, msq)

    data = com_read(spi, ser, 4)[2:]

    if (len(data) < 2):
        warn('response is too short')
        return None
    elif (data[1] != msq_checksum([data[0]])):
        warn('checksum unmatch')
        return None

    return data[0]


def isdu_read(spi, ser, index, data_type):
    info('***** CALL: isdu_read(index: 0x{:x}) ****'.format(index))

    isdu_req = isdu_req_build(index)

    for msq in isdu_req:
        com_write(spi, ser, msq)
        data = com_read(spi, ser, 4)

    chk = 0x00
    flow = 1
    data_list = []
    while True:
        header = isdu_res_read(spi, ser, 0x10)
        chk = header

        if (header >> 4) == 0x0D:
            if (header & 0x0F) == 0x01:
                remain = isdu_res_read(spi, ser, flow) - 2
                flow += 1
                chk ^= length
            else:
                remain = (header & 0x0F) - 1
            break
        elif header == 0x01:
            info('WAIT response')
            continue
        elif (header >> 4) == 0x0C:
            error('ERROR reponse')
        else:
            logger.warn("INVALID response: %s" % pprint.pformat(header))
            error('INVALID reponse')

    for x in range(remain-1):
        data = isdu_res_read(spi, ser, flow & 0xF)
        data_list.append(data)
        flow += 1
        chk ^= data

    chk ^= isdu_res_read(spi, ser, flow)

    if chk != 0x00:
        error('ISDU checksum unmatch')

    if data_type == DATA_TYPE_STRING:
        return struct.pack('{}B'.format(len(data_list)), *data_list).decode('utf-8')
    elif data_type == DATA_TYPE_UINT16:
        return struct.unpack('>H', bytes(data_list))[0]
    else:
        return data_list
