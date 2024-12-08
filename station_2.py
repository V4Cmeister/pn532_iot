import logging
from rfid_handler import RFIDHandler
import sqlite3

# Logging konfigurieren
logging.basicConfig(
    filename="station2.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DB_PATH = "data/flaschen_database.db"

def get_rezept_for_flasche(flaschen_id):
    """Holt die Rezeptdaten für eine gegebene Flaschen-ID aus der Datenbank."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Rezeptdaten aus der Datenbank abrufen
    query = """
    SELECT r.Rezept_ID, r.Granulat_ID, r.Menge
    FROM Rezept_besteht_aus_Granulat r
    JOIN Flasche f ON r.Rezept_ID = f.Rezept_ID
    WHERE f.Flaschen_ID = ?
    """
    cursor.execute(query, (flaschen_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        logging.warning(f"Keine Rezeptdaten für Flaschen-ID {flaschen_id} gefunden.")
        return None

    logging.info(f"Rezeptdaten für Flaschen-ID {flaschen_id} abgerufen: {rows}")
    return rows

if __name__ == "__main__":
    rfid_handler = RFIDHandler()

    # Lese die Flaschen-ID von der Karte
    flaschen_id = rfid_handler.read_flaschen_id()
    if flaschen_id is not None:
        logging.info(f"Flaschen-ID gelesen: {flaschen_id}")
        rezeptdaten = get_rezept_for_flasche(flaschen_id)
        if rezeptdaten:
            print(f"Rezeptdaten für Flaschen-ID {flaschen_id}:")
            for rezept_id, granulat_id, menge in rezeptdaten:
                print(f"  Rezept ID: {rezept_id}, Granulat ID: {granulat_id}, Menge: {menge}g")
        else:
            print(f"Keine Rezeptdaten für Flaschen-ID {flaschen_id} gefunden.")
    else:
        logging.error("Keine Flaschen-ID von der Karte gelesen.")
