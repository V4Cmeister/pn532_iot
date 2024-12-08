import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.spi import PN532_SPI

class RFIDHandler:
    def __init__(self):
        # SPI-Verbindung initialisieren
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        cs_pin = DigitalInOut(board.D8)  # CS-Pin definieren
        self.pn532 = PN532_SPI(spi, cs_pin, debug=False)

        # Firmware-Version ausgeben
        ic, ver, rev, support = self.pn532.firmware_version
        print(f"Found PN532 with firmware version: {ver}.{rev}")

        # Konfiguration für MiFare-Karten
        self.pn532.SAM_configuration()

    def read_uid(self):
        """Liest die UID der RFID-Karte."""
        uid = self.pn532.read_passive_target(timeout=1)
        if uid:
            return int.from_bytes(uid, byteorder='big')
        return None

    def read_flaschen_id(self, block_number=1):
        """Liest die Flaschen-ID aus einem Block der Karte."""
        key_a = bytes([0xFF] * 6)  # Standard-Key A

        uid = self.pn532.read_passive_target(timeout=1)
        if not uid:
            print("Keine Karte erkannt.")
            return None

        # Authentifizierung
        authenticated = self.pn532.mifare_classic_authenticate_block(
            uid=uid, block_number=block_number, key_number=0x60, key=key_a
        )
        if not authenticated:
            print("Authentifizierung fehlgeschlagen.")
            return None

        # Block auslesen
        data = self.pn532.mifare_classic_read_block(block_number)
        if data:
            flaschen_id = data[0]  # Flaschen-ID aus dem ersten Byte extrahieren
            return flaschen_id
        else:
            print("Fehler beim Lesen des Blocks.")
            return None

    def write_flaschen_id(self, flaschen_id, block_number=1):
        """Schreibt die Flaschen-ID auf die Karte."""
        key_a = bytes([0xFF] * 6)  # Standard-Key A

        uid = self.pn532.read_passive_target(timeout=0.5)
        if not uid:
            print("Keine Karte erkannt.")
            return False

        # Authentifizierung
        authenticated = self.pn532.mifare_classic_authenticate_block(
            uid=uid, block_number=block_number, key_number=0x60, key=key_a
        )
        if not authenticated:
            print("Authentifizierung fehlgeschlagen.")
            return False

        # Schreiben der Flaschen-ID
        data = [0] * 16  # 16-Byte Block
        data[0] = flaschen_id
        success = self.pn532.mifare_classic_write_block(block_number, bytes(data))

        if success:
            print(f"Flaschen-ID {flaschen_id} erfolgreich geschrieben.")
            return True
        else:
            print("Fehler beim Schreiben der Flaschen-ID.")
            return False
