from flask import Flask, render_template_string, request, jsonify, send_from_directory
import os
from escpos.printer import Usb
from PIL import Image
from datetime import datetime
# Optional DHT sensor (Adafruit_DHT). If not available, proceed without crashing.
try:
    import Adafruit_DHT
    DHT_AVAILABLE = True
    DHT_SENSOR = Adafruit_DHT.DHT11
    DHT_PIN = 2  # GPIO-Nummer wie vom Benutzer angegeben
except Exception:
    DHT_AVAILABLE = False
    DHT_SENSOR = None
    DHT_PIN = None

def read_dht():
    """Versucht einmal die Temperatur und Luftfeuchte vom DHT-Sensor zu lesen.
    Gibt (humidity, temperature) zurück oder (None, None) bei Fehler/nicht vorhandenem Sensor.
    """
    if not DHT_AVAILABLE:
        return None, None
    try:
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        return humidity, temperature
    except Exception:
        return None, None

PRINTER_VENDOR = 0x04b8
PRINTER_PRODUCT = 0x0202

app = Flask(__name__)

cart = []

# Produkte
products = [
    {"name": "Limo", "price": 1.50, "emoji": "🥤"},
    {"name": "Eis", "price": 2.00, "emoji": "🍦"},
    {"name": "Pommes", "price": 1.20, "emoji": "🍟"},
    {"name": "Pizza", "price": 3.00, "emoji": "🍕"},
    {"name": "Burger", "price": 3.50, "emoji": "🍔"},
    {"name": "Hotdog", "price": 2.50, "emoji": "🌭"},
    {"name": "Taco", "price": 2.00, "emoji": "🌮"},
    {"name": "Brot", "price": 1.00, "emoji": "🍞"},
    {"name": "Brezel", "price": 1.00, "emoji": "🥨"},
    {"name": "Käse", "price": 1.20, "emoji": "🧀"},
    {"name": "Fisch", "price": 3.00, "emoji": "🐟"},
    {"name": "Hähnchen", "price": 4.00, "emoji": "🍗"},
    {"name": "Salat", "price": 2.50, "emoji": "🥗"},
    {"name": "Pfannkuchen", "price": 2.50, "emoji": "🥞"},
    {"name": "Kuchen", "price": 3.00, "emoji": "🍰"},
    {"name": "Donut", "price": 1.50, "emoji": "🍩"},
    {"name": "Cupcake", "price": 2.00, "emoji": "🧁"},
    {"name": "Schokolade", "price": 1.20, "emoji": "🍫"},
    {"name": "Apfel", "price": 0.80, "emoji": "🍎"},
    {"name": "Banane", "price": 0.70, "emoji": "🍌"},
    {"name": "Erdbeere", "price": 1.00, "emoji": "🍓"},
    {"name": "Kirsche", "price": 1.00, "emoji": "🍒"},
    {"name": "Melone", "price": 1.50, "emoji": "🍉"},
    {"name": "Karotte", "price": 0.50, "emoji": "🥕"},
    {"name": "Mais", "price": 0.80, "emoji": "🌽"},
    {"name": "Pilz", "price": 0.70, "emoji": "🍄"},
]

HTML = """<!doctype html>
<html class="bg-yellow-50">
<head>
<meta charset="utf-8">
<title>Kinderkasse 🍭</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#ff4500">
<link rel="icon" href="/favicon/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/favicon/apple-touch-icon.png">
<style>
body { font-family: sans-serif; text-align:center; background:#fff8dc; }
h1 { color:#ff4500; }
#buttons { display:flex; flex-wrap: wrap; justify-content:center; }
button {
    font-size:2em; margin:10px; padding:20px 40px;
    border-radius:20px; background:#ffd700; border:none; cursor:pointer;
    transition: transform 0.1s;
}
button:active { transform: scale(0.95); background:#ffa500; }
#total { font-size:2em; margin:20px; color:#ff4500; }
#cart { font-size:1.5em; margin:10px; }
#print { font-size:2em; background:#ff69b4; color:white; padding:15px 30px; border:none; border-radius:20px; cursor:pointer; }
#print:active { background:#ff1493; }
</style>
<script>
let cart = [];
const beepSound = new Audio('/static/beep.wav');  // Audio vorab laden

// Artikel zum Warenkorb hinzufügen
function buy(item) {
    cart.push(item);
    updateCart();
    beepSound.currentTime = 0;  // Zurück zum Start
    beepSound.play();
}

// Eigenen Artikel hinzufügen (Name + Preis + optional Emoji)
function addCustomItem(){
    const nameEl = document.getElementById('custom_name');
    const priceEl = document.getElementById('custom_price');
    const emojiEl = document.getElementById('custom_emoji');

    const name = (nameEl.value || '').trim();
    const priceRaw = priceEl.value;
    const emoji = (emojiEl.value || '').trim();

    if(!name){
        alert('Bitte einen Namen eingeben.');
        return;
    }

    const price = parseFloat(priceRaw);
    if(isNaN(price) || price < 0){
        alert('Bitte einen gültigen Preis eingeben.');
        return;
    }

    const item = { name: name, price: Math.round(price*100)/100, emoji: emoji || '🔖' };

    // In den Warenkorb legen (wie bisher)
    buy(item);

    // Zusätzlich einen Produkt-Button in die Produktliste einfügen, mit Lösch-Button
    try {
        const buttonsContainer = document.getElementById('buttons');
        // Wrapper für Button + Lösch-Icon
        const wrap = document.createElement('div');
        wrap.style.display = 'inline-block';
        wrap.style.margin = '10px';
        wrap.style.position = 'relative';

        const prodBtn = document.createElement('button');
        prodBtn.style.fontSize = '2em';
        prodBtn.style.padding = '20px 40px';
        prodBtn.style.borderRadius = '20px';
        prodBtn.style.background = '#ffd700';
        prodBtn.style.border = 'none';
        prodBtn.style.cursor = 'pointer';
        prodBtn.innerText = `${item.emoji} ${item.name} (€${item.price.toFixed(2)})`;
        prodBtn.onclick = function(){ buy(item); };

        // Kleiner Lösch-Button oben rechts am Wrapper
        const del = document.createElement('button');
        del.innerText = '✖';
        del.title = 'Dieses benutzerdefinierte Produkt entfernen';
        del.style.position = 'absolute';
        del.style.top = '-8px';
        del.style.right = '-8px';
        del.style.border = 'none';
        del.style.background = '#ff6b6b';
        del.style.color = 'white';
        del.style.borderRadius = '50%';
        del.style.width = '28px';
        del.style.height = '28px';
        del.style.cursor = 'pointer';
        del.onclick = function(e){ e.stopPropagation(); wrap.remove(); };

        wrap.appendChild(prodBtn);
        wrap.appendChild(del);
        buttonsContainer.appendChild(wrap);
    } catch (e) {
        // Falls irgendwas mit DOM nicht klappt, ist das kein Showstopper
        console.log('Produkt-Button konnte nicht hinzugefügt werden:', e);
    }

    // Formularfelder zurücksetzen
    nameEl.value = '';
    priceEl.value = '';
    emojiEl.value = '';
    nameEl.focus();
}

// Artikel aus dem Warenkorb entfernen
function removeItem(index) {
    cart.splice(index, 1);
    updateCart();
}

// Warenkorb aktualisieren
function updateCart() {
    let list = cart.map((i, idx) => 
        i.emoji + ' ' + i.name + ' €' + i.price.toFixed(2) + 
        ` <button onclick="removeItem(${idx})">❌</button>`
    ).join('<br>');

    let total = cart.reduce((a, b) => a + b.price, 0);

    document.getElementById('cart').innerHTML = list;
    document.getElementById('total').innerText = 'Gesamt: €' + total.toFixed(2);
}

// Warenkorb drucken
function printCart() {
    if(cart.length === 0) return; // Nichts zu drucken
    var audio = new Audio('/static/register_open.wav'); // Sound abspielen
    audio.play();
    fetch('/print', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(cart)
    })
    .then(res => res.json())
    .then(data => {
        if(data.status == 'ok'){
            cart = [];         // Warenkorb leeren
            updateCart();      // UI aktualisieren
        }
    });
}
</script>

<script>
// Vollbild aktivieren wenn möglich (einmalig bei erster Interaktion)
function enableFullscreen() {
    let elem = document.documentElement;
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
    }
}
document.addEventListener('click', enableFullscreen, {once: true});
</script>

</head>
<body>
<h1>Kinderkasse 🍭</h1>
<div id="buttons">
{% for p in products %}
    <button onclick='buy({name:"{{p.name}}",price:{{p.price}},emoji:"{{p.emoji}}"})'>
        {{p.emoji}} {{p.name}} (€{{p.price}})
    </button>
{% endfor %}
</div>
<!-- Formular zum Hinzufügen eigener Artikel -->
<div id="custom" style="margin-top:20px;">
    <h3>Eigenen Artikel hinzufügen</h3>
    <input id="custom_name" placeholder="Name" style="font-size:1em; padding:6px;" />
    <input id="custom_price" placeholder="Preis (€)" type="number" step="0.01" style="font-size:1em; padding:6px; width:100px;" />
    <input id="custom_emoji" placeholder="Emoji (optional)" style="font-size:1em; padding:6px; width:120px;" />
    <button onclick="addCustomItem()" style="font-size:1em; padding:8px 12px; margin-left:6px;">Hinzufügen</button>
</div>

<div id="cart"></div>
<div id="total">Gesamt: €0.00</div>
<button id="print" onclick="printCart()">🖨️ Bon drucken</button>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML, products=products)

# Route zum Ausliefern der vorhandenen Favicon-Dateien im Ordner /favicon
@app.route('/favicon/<path:filename>')
def favicon_files(filename):
        return send_from_directory(os.path.join(app.root_path, 'favicon'), filename)


@app.route("/print", methods=["POST"])
def print_cart():
    items = request.get_json()
    total = sum(i["price"] for i in items)
    try:
        p = Usb(PRINTER_VENDOR, PRINTER_PRODUCT)

	# 1) Bild drucken (z.B. Logo)
        logo_path = "/root/img.png"  # Pfad zum Bild
        logo = Image.open(logo_path)
        p.image(logo)
    # 2) Geschäftsinhaberin (zentriert)
        p.set(align='center', bold=False)
        p.text("\n")
        p.text("👩‍💼  Inhaberin: Anna Musterfrau\n")
        p.text("Musterstraße 12\n")
        p.text("12345 Musterstadt\n")
        p.text("Mail: anna@musterfrau.de\n")
        p.text("Tel: 0123 / 456789\n")
        p.text("\n")
    # Text zentrieren
        p.set(align='center', bold=True)
	# # Unterstrich aktivieren
    #     p.set(underline=2)  # 1 = einfarbig unterstrichen, 2 = doppelt
	# Titel drucken
        p.text("\n---====== Kinderkassenbon ======---\n\n")
	# # Unterstrich wieder ausschalten
    #     p.set(underline=0)
    # Text linksbündig
        p.set(align='left', bold=False)
        for i in items:
            p.text(f"{i['name']}  €{i['price']:.2f}\n")
        p.text(f"\nGesamt: €{total:.2f}\n\n")
    # Text zentrieren
        p.set(align='center')
        p.text("===================================\n")
        # Temperatur und Luftfeuchte ermitteln (falls Sensor verfügbar)
        humidity, temperature = read_dht()
        if temperature is not None and humidity is not None:
            try:
                p.text(f"Temp.: {temperature:.1f} C  Feucht.: {humidity:.1f}%\n")
            except Exception:
                # Fallback, falls Printer-Objekt Probleme mit Formatierung hat
                p.text("Temp.: -- C  Feucht.: --%\n")
        else:
            p.text("Temp.: N/A  Feucht.: N/A\n")
        p.text("===================================\n")
        # Aktuelles Datum und Uhrzeit beim Drucken
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        p.text(f"{current_time}\n")
        p.text("===================================\n")

        # Unterstrich aktivieren
        # p.set(underline=2)  # 1 = einfarbig unterstrichen, 2 = doppelt
        # # Titel drucken
        p.set(bold=True)
        p.text("\n---====== Kinderkassenbon ======---\n\n")
        # # Unterstrich wieder ausschalten
        # p.set(underline=0)

        p.cut()
    except Exception as e:
        print("Druckfehler:", e)
        return jsonify({"status": "error", "message": str(e)})
    finally:
        # Drucker freigeben
        try:
            p.close()
        except:
            pass
    
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
