import sqlite3
from collections import defaultdict

def get_rezept_for_flasche(db_path):
    # Verbindung zur Datenbank herstellen
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # SQL-Abfrage, um Rezept-ID, Granulatmengen und die Flaschen-ID abzurufen
    query = """
    SELECT f.Flaschen_ID, r.Rezept_ID, r.Granulat_ID, r.Menge
    FROM Rezept_besteht_aus_Granulat r
    JOIN Flasche f ON r.Rezept_ID = f.Rezept_ID
    WHERE f.Tagged_Date != 0
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    # Falls keine Daten gefunden werden
    if not rows:
        print("Keine Rezepte in der Datenbank gefunden.")
        return

    # Dictionary, um Daten nach Flaschen-ID zu gruppieren
    flaschen_daten = defaultdict(list)

    # Gruppiere die Granulate und Mengen für jede Flasche
    for row in rows:
        flaschen_id, rezept_id, granulat_id, menge = row
        flaschen_daten[flaschen_id].append((rezept_id, granulat_id, menge))

    # Ausgabe der relevanten Daten
    for flaschen_id, daten in flaschen_daten.items():
        print(f"Flasche ID: {flaschen_id}")
        for rezept_id, granulat_id, menge in daten:
            print(f"  Rezept ID: {rezept_id}, Granulat ID: {granulat_id}, Menge: {menge}g")

    # Verbindung schließen
    conn.close()

if __name__ == "__main__":
    db_path = 'data/flaschen_database.db'  # Der Pfad zur Datenbank
    get_rezept_for_flasche(db_path)
