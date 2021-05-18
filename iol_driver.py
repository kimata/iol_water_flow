#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import struct

import iol_const

def dump_byte_list(label, byte_list):
    print('{}: {}'.format(label, ', '.join(hex(x) for x in byte_list)))


def ltc2874_reg_read(spi, reg):
    return spi.xfer2([ (0x00 << 5) | (reg << 1), 0x00])


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


def build_msq(rw, ch, addr, mtype, data):
    mc = (rw << 7) | (ch << 5) | (addr)
    cht = (mtype << 6)

    msq = [mc, cht]

    if (data is not None):
        msq.extend(data)

    cht |= msq_checksum(msq)
    msq[1] = cht

    return msq


def com_start(spi):
    # Power on, CQ OC Timeout = 480us
    ltc2874_reg_write(spi, 0x0E, 0x11)

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


def com_stop(spi, ser):
    ser.close()
    # Drive disable
    ltc2874_reg_write(spi, 0x0D, 0x00)
    # Power off
    ltc2874_reg_write(spi, 0x0E, 0x00)


def com_write(spi, ser, byte_list):
    # Drive enable
    ltc2874_reg_write(spi, 0x0D, 0x01)

    dump_byte_list('SEND: ', byte_list)

    ser.write(struct.pack('{}B'.format(len(byte_list)), *byte_list))
    ser.flush()

    # Drive disable
    ltc2874_reg_write(spi, 0x0D, 0x00)


def com_read(spi, ser, length):
    recv = ser.read(length)
    byte_list = struct.unpack('{}B'.format(len(recv)), recv)

    dump_byte_list('RECV: ', byte_list)

    return byte_list
    

def dir_param_read(spi, ser, addr):
    msq = build_msq(iol_const.MSQ_RW_READ, iol_const.MSQ_CH_PAGE,
                    addr, iol_const.MSQ_TYPE_0, None)
    com_write(spi, ser, msq)

    data = com_read(spi, ser, 4)[2:]

    if (len(data) < 2):
        warn('response is too short')
        return None
    elif (data[1] != msq_checksum([data[0]])):
        warn('checksum unmatch')
        return None

    return data[1]
