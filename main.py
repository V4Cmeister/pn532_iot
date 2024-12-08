import time
import sqlite3
import logging
import board
import busio
from digitalio import DigitalInOut
from adafruit_pn532.spi import PN532_SPI

# Logger konfigurieren
LOG_FILE = 'station.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),  # Log-Datei
        logging.StreamHandler()        # Konsole
    ]
)
logger = logging.getLogger(__name__)

# Datenbank-Pfad
DB_PATH = 'data/flaschen_database.db'

# RFID-Handler Klasse
class RFIDHandler:
    def __init__(self):
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        cs_pin = DigitalInOut(board.D8)
        self.pn532 = PN532_SPI(spi, cs_pin, debug=False)
        self.pn532.SAM_configuration()
        ic, ver, rev, support = self.pn532.firmware_version
        logger.info(f"PN532 Firmware: {ver}.{rev}")

    def write_id(self, flaschen_id, block_number=1):
        uid = self.pn532.read_passive_target(timeout=0.5)
        if uid:
            logger.info(f"Karte gefunden mit UID: {uid}")
            key_a = bytes([0xFF] * 6)
            if self.pn532.mifare_classic_authenticate_block(uid, block_number, 0x60, key_a):
                data = [0] * 16
                data[0] = flaschen_id
                if self.pn532.mifare_classic_write_block(block_number, bytes(data)):
                    logger.info(f"Flaschen-ID {flaschen_id} erfolgreich geschrieben.")
                    return True
                else:
                    logger.error("Fehler beim Schreiben auf die Karte.")
            else:
                logger.error("Authentifizierung fehlgeschlagen.")
        else:
            logger.warning("Keine Karte erkannt.")
        return False

# State-Machine Klassen
class State:
    def __init__(self, machine):
        self.machine = machine

    def run(self):
        raise NotImplementedError("State must implement 'run' method.")

class State1(State):
    def run(self):
        logger.info("State1: Warte auf ungetaggte Flasche in der Datenbank...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT Flaschen_ID FROM Flasche WHERE Tagged_Date = 0 LIMIT 1;")
        result = cursor.fetchone()

        if result:
            flaschen_id = result[0]
            logger.info(f"Ungetaggte Flasche gefunden: {flaschen_id}")
            self.machine.data["flaschen_id"] = flaschen_id
            self.machine.current_state = "State2"
        else:
            logger.warning("Keine ungetaggte Flasche gefunden.")
            self.machine.current_state = "State5"
        conn.close()

class State2(State):
    def run(self):
        logger.info("State2: Schreibe Flaschen-ID auf die RFID-Karte...")
        flaschen_id = self.machine.data.get("flaschen_id")
        if flaschen_id and self.machine.rfid_handler.write_id(flaschen_id):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            current_timestamp = int(time.time())
            cursor.execute(
                "UPDATE Flasche SET Tagged_Date = ? WHERE Flaschen_ID = ?;",
                (current_timestamp, flaschen_id),
            )
            conn.commit()
            conn.close()
            logger.info(f"Flaschen-ID {flaschen_id} erfolgreich geschrieben und Datenbank aktualisiert.")
            self.machine.current_state = "State3"
        else:
            logger.error("Fehler beim Schreiben der Flaschen-ID.")
            self.machine.current_state = "State5"

class State3(State):
    def run(self):
        logger.info("State3: Rezeptinformationen für Flasche abrufen...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.Rezept_ID, r.Granulat_ID, r.Menge
            FROM Rezept_besteht_aus_Granulat r
            JOIN Flasche f ON r.Rezept_ID = f.Rezept_ID
            WHERE f.Flaschen_ID = ?;
        """, (self.machine.data["flaschen_id"],))
        results = cursor.fetchall()
        if results:
            for rezept_id, granulat_id, menge in results:
                logger.info(f"Rezept ID: {rezept_id}, Granulat ID: {granulat_id}, Menge: {menge}g")
            self.machine.current_state = "State4"
        else:
            logger.warning("Keine Rezeptinformationen gefunden.")
            self.machine.current_state = "State5"
        conn.close()

class State4(State):
    def run(self):
        logger.info("State4: Bestätigung senden...")
        logger.info(f"Flasche {self.machine.data['flaschen_id']} erfolgreich verarbeitet.")
        self.machine.current_state = "State5"

class State5(State):
    def run(self):
        logger.info("State5: Fehlerbehandlung oder Abschluss...")
        logger.info("Prozess beendet.")
        self.machine.is_running = False

# State-Machine Klasse
class StateMachine:
    def __init__(self):
        self.rfid_handler = RFIDHandler()
        self.states = {
            "State1": State1(self),
            "State2": State2(self),
            "State3": State3(self),
            "State4": State4(self),
            "State5": State5(self),
        }
        self.current_state = "State1"
        self.is_running = True
        self.data = {}

    def run(self):
        while self.is_running:
            state = self.states[self.current_state]
            state.run()

# Hauptprogramm
if __name__ == "__main__":  
    machine = StateMachine()
    machine.run()
