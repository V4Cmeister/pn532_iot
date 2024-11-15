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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
DEFAULT_KEY_A = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

def config_pn532():
    """
    Configures the PN532 with SPI connection and initializes it.
    
    Returns:
        PN532_SPI: Configured PN532 instance.
    """

    try:
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        cs_pin = DigitalInOut(board.D8)
        pn532 = PN532_SPI(spi, cs_pin, debug=False)

        ic, ver, rev, support = pn532.firmware_version
        logging.info("Found PN532 with firmware version: %d.%d", ver, rev)

        # Configure PN532 to communicate with MiFare cards
        pn532.SAM_configuration()
        return pn532
    except Exception as e:
        logging.error("Failed to configure PN532: %s", e)
        raise

def write_block(pn532, uid, block_number, data):
    """
    Writes data to a specific block on the MiFare card.
    
    Args:
        pn532 (PN532_SPI): Configured PN532 instance.
        uid (bytes): UID of the MiFare card.
        block_number (int): Block number to write data to.
        data (bytes): Data to write to the block.
    
    Returns:
        bool: True if the data was written successfully, False otherwise.
    """
    try:
        authenticated = pn532.mifare_classic_authenticate_block(uid, block_number, 0x60, DEFAULT_KEY_A)
        if not authenticated:
            logging.error("Authentication failed for block %d", block_number)
            return False

        written = pn532.mifare_classic_write_block(block_number, data)
        if written and pn532.mifare_classic_read_block(block_number) == data:
            return True
        return False
    except Exception as e:
        logging.error("Failed to write to block %d: %s", block_number, e)
        return False
    


if __name__ == "__main__":
    try:
        pn532 = config_pn532()

        logging.info("Waiting for RFID/NFC card...")
        while True:
            uid = pn532.read_passive_target(timeout=0.5)
            print(".", end="")
            if uid is None:
                continue
            logging.info("Found card with UID: %s", [hex(i) for i in uid])
            break

        block_number = 2
        data = bytes([0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03, 0x00, 0x01, 0x02, 0x03])

        if write_block(pn532, uid, block_number, data):
            logging.info("Successfully wrote to block: %d", block_number)
        else:
            logging.error("Failed to write to block: %d", block_number)

        read_data = pn532.mifare_classic_read_block(block_number)
        if read_data:
            logging.info("Read data from block: %s", read_data)
        else:
            logging.error("Failed to read data from block: %d", block_number)
    except Exception as e:
        logging.error("An error occurred: %s", e)