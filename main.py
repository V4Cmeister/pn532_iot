import time
import sqlite3
import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.spi import PN532_SPI

# Konfiguration der Datenbank
db_path = 'data/flaschen_database.db'


# Funktion zur Konfiguration des PN532
def config_pn532():
    # SPI Verbindung initialisieren
    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    cs_pin = DigitalInOut(board.D8)  # CS-Pin definieren
    pn532 = PN532_SPI(spi, cs_pin, debug=False)

    ic, ver, rev, support = pn532.firmware_version
    print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))

    # Konfiguration für MiFare-Karten
    pn532.SAM_configuration()
    return pn532

# Funktion zum Schreiben der Flaschen-ID auf die Karte
def write_flaschen_id(pn532, flaschen_id, block_number=1):
    key_a = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])  # Standard-Key A
    uid = pn532.read_passive_target(timeout=0.5)

    if uid:
        print("Karte gefunden mit UID:", [hex(i) for i in uid])
        authenticated = pn532.mifare_classic_authenticate_block(
            uid=uid, block_number=block_number, key_number=0x60, key=key_a
        )

        if authenticated:
            # Schreiben der Flaschen-ID (in Byte-Format konvertieren)
            data = [0] * 16  # 16-Byte Block (Standardgröße)
            data[0] = flaschen_id  # Flaschen-ID in das erste Byte des Blocks schreiben
            success = pn532.mifare_classic_write_block(block_number, bytes(data))
            if success:
                print(f"Flaschen-ID {flaschen_id} erfolgreich in Block {block_number} geschrieben.")
                return True
            else:
                print("Fehler beim Schreiben auf die Karte.")
                return False
        else:
            print("Authentifizierung fehlgeschlagen.")
            return False
    else:
        print("Keine Karte erkannt.")
        return False


# Funktion zur Aktualisierung der Datenbank
def update_tagged_date(flaschen_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    current_timestamp = int(time.time())

    cursor.execute(
        "UPDATE Flasche SET Tagged_Date = ? WHERE Flaschen_ID = ?;",
        (current_timestamp, flaschen_id),
    )
    connection.commit()
    connection.close()
    print(f"Datenbank aktualisiert: Flasche {flaschen_id} getagged mit {current_timestamp}.")

if __name__ == "__main__":
    # RFID initialisieren
    pn532 = config_pn532()

    # Datenbankverbindung
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Erste ungetaggte Flasche holen
    cursor.execute("SELECT Flaschen_ID FROM Flasche WHERE Tagged_Date = 0 LIMIT 1;")
    untagged_bottle = cursor.fetchone()

    if untagged_bottle:
        flaschen_id = untagged_bottle[0]
        print(f"Untagged Flaschen_ID gefunden: {flaschen_id}")

        # Flaschen-ID auf die Karte schreiben
        if write_flaschen_id(pn532, flaschen_id):
            # Datenbank nur aktualisieren, wenn das Schreiben erfolgreich war
            update_tagged_date(flaschen_id)
        else:
            print("Tagging wurde abgebrochen, da kein gültiges RFID-Tag beschrieben werden konnte.")
    else:
        print("Keine ungetaggte Flasche gefunden.")

    # Datenbank schließen
    connection.close()
