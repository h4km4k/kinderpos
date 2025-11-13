# kinderpos

Touch‑Kassen‑App für Raspberry Pi — einfach, bunt und kindgerecht.

Kurzbeschreibung
---------------
Eine einfache Touch‑Kassen‑Anwendung für kleine Verkaufsstände (z. B. Schulbasar oder Kinderfest). Bietet Produktbuttons, eigene Artikel mit Preis/Emoji, akustisches Feedback (Beep + Kassen‑Sound), Bon‑Druck über ESC/POS‑USB‑Drucker und optionale Anzeige von Temperatur und Luftfeuchte über einen DHT‑Sensor.

Features
--------
- Produktbuttons zum schnellen Hinzufügen
- Eigenen Artikel (Name, Preis, Emoji) hinzufügen
- Akustisches Feedback: Beep bei Artikelwahl, Kassen‑Sound beim Druck
- Bon‑Druck via ESC/POS (USB)
- Optional: DHT11‑Sensor für Temp / Luftfeuchte auf dem Bon
- Leichtgewichtig, offline‑fähig (läuft auf Raspberry Pi)

Schnellstart
-----------
1. Auf dem Raspberry Pi klonen:

```sh
git clone <repo-url>
cd kinderpos
```

2. Abhängigkeiten installieren (Beispiel):

```sh
python3 -m venv venv
. venv/bin/activate
pip install flask pillow python-escpos
# Optional: Adafruit_DHT für DHT‑Sensor
pip install Adafruit_DHT
```

3. `kinderpos_sound.py` anpassen (falls nötig):
- `PRINTER_VENDOR` und `PRINTER_PRODUCT` anpassen, falls Ihr Drucker andere IDs hat.
- Falls Sie DHT22 statt DHT11 nutzen oder anderen GPIO‑Pin verwenden, passen Sie `DHT_SENSOR` / `DHT_PIN` im Script an.

4. App starten:

```sh
python3 kinderpos_sound.py
```

5. Im Browser öffnen: `http://raspberry.local:8080` (oder die IP Ihres Pi).

Konfiguration
-------------
- Drucker: USB‑Vendor/Product IDs in `kinderpos_sound.py` setzen.
- DHT‑Sensor: Standard ist DHT11 an GPIO 2. Wenn `Adafruit_DHT` fehlt, läuft die App trotzdem und schreibt "N/A" auf den Bon.

Screenshots
-----------
- Demo UI: `screenshots/screen1.png`
- Demo UI: `screenshots/screen2.png`
- Bon‑Beispiel: `screenshots/screen3.png`

Tests & Debugging
-----------------
- Browser‑Konsole (F12) zeigt Fehler beim Laden von Assets oder beim Abspielen von Audio.
- Server‑Konsole zeigt Druckfehler oder Fehler beim DHT‑Lesen.

Lizenz
------
MIT

Kontakt
-------
Projekt für den persönlichen Einsatz. Bei Fragen: README aktualisieren oder Issues öffnen.
