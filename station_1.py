import time
import sqlite3
import logging
from rfid_handler import RFIDHandler

# Logger konfigurieren
logging.basicConfig(filename='station1.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = 'data/flaschen_database.db'

def write_flaschen_id():
    rfid_handler = RFIDHandler()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Erste ungetaggte Flasche abrufen
        cursor.execute("SELECT Flaschen_ID FROM Flasche WHERE Tagged_Date = 0 LIMIT 1;")
        result = cursor.fetchone()

        if result:
            flaschen_id = result[0]
            logger.info(f"Ungetaggte Flasche gefunden: {flaschen_id}")

            # Flaschen-ID auf die Karte schreiben
            if rfid_handler.write_flaschen_id(flaschen_id):
                # Aktualisiere Datenbank
                current_timestamp = int(time.time())
                cursor.execute(
                    "UPDATE Flasche SET Tagged_Date = ? WHERE Flaschen_ID = ?;",
                    (current_timestamp, flaschen_id),
                )
                conn.commit()
                logger.info(f"Flaschen-ID {flaschen_id} erfolgreich geschrieben und getagged.")
            else:
                logger.error("Fehler beim Schreiben der Flaschen-ID auf die Karte.")
        else:
            logger.warning("Keine ungetaggte Flasche in der Datenbank gefunden.")

    except Exception as e:
        logger.error(f"Fehler in station1.py: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    write_flaschen_id()
