# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Documentation: https://docs.circuitpython.org/projects/pn532/en/latest/api.html

"""
This example shows connecting to the PN532 with I2C (requires clock
stretching support), SPI, or UART. SPI is best, it uses the most pins but
is the most reliable and universally supported.
After initialization, try waving various 13.56MHz RFID cards over it!
"""

import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.spi import PN532_SPI

def config_pn532():
    # SPI connection:
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    cs_pin = DigitalInOut(board.D8)
    pn532 = PN532_SPI(spi, cs_pin, debug=False)

    ic, ver, rev, support = pn532.firmware_version
    print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))

    # Configure PN532 to communicate with MiFare cards
    pn532.SAM_configuration()
    return pn532

def write_block(pn532, uid, block_number, data):
    key_a = bytes([0xFF, 0xFF, 0xFF, 0xFF,0xFF, 0xFF])
    authenticated = pn532.mifare_classic_authenticate_block(uid = uid, block_number = block_number , key_number =0x60, key = key_a)

    written = pn532.mifare_classic_write_block(block_number, data)

    if written:
        # Read to ensure data was written
        if pn532.mifare_classic_read_block(block_number) == data:
            return True
    return False

if __name__ == "__main__":
    pn532 = config_pn532()

    print("Waiting for RFID/NFC card...")
    while True:
        # Check if a card is available to read
        uid = pn532.read_passive_target(timeout=0.5)
        print(".", end="")
        # Try again if no card is available.
        if uid is None:
            continue
        print("Found card with UID:", [hex(i) for i in uid])
        break

    # Communication - Code
    block_number = 2
    # You can write 4 Bytes in a Block
    data = bytes([0x00, 0x01, 0x02, 0x03,0x00, 0x01, 0x02, 0x03,0x00, 0x01, 0x02, 0x03,0x00, 0x01, 0x02, 0x03])

    if write_block(pn532,uid, block_number, data):
        print("Sucessfully worte in block: ", block_number)

    read = pn532.mifare_classic_read_block(block_number)

    print(read)
