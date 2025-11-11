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
.payment-section { margin-top:10px; padding:20px; border-radius:10px; }
.payment-display { display:flex; gap:20px; justify-content:center; font-size:1.5em; margin-bottom:20px; }
.payment-field { background:white; padding:15px; border-radius:8px; border:2px solid #ff4500; min-width:120px; text-align:center; }
.payment-field label { display:block; font-size:0.8em; color:#666; margin-bottom:5px; }
.payment-field value { display:block; font-size:1.5em; font-weight:bold; color:#ff4500; }
.numpad { display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; max-width:280px; margin:0 auto; }
.numpad button { 
    font-size:1.5em; 
    padding:25px; 
    background:#ffd700; 
    border:none; 
    border-radius:8px; 
    cursor:pointer;
    min-height:70px;
    min-width:70px;
    display:flex;
    align-items:center;
    justify-content:center;
}
.numpad button:active { background:#ffa500; }
.numpad button.clear { background:#ff6b6b; color:white; }
.numpad button#print { background:#90EE90; color:black; font-weight:bold; grid-column: 1 / -1; }
</style>
<script>
let cart = [];
const beepSound = new Audio('/static/beep.wav');  // Audio vorab laden
let customItems = [];  // Array für benutzerdefinierte Artikel

// LocalStorage laden
function loadCustomItems() {
    try {
        const saved = localStorage.getItem('kinderpos_custom_items');
        if (saved) {
            customItems = JSON.parse(saved);
            renderCustomItems();
        }
    } catch (e) {
        console.log('Fehler beim Laden von Custom-Items aus localStorage:', e);
    }
}

// CustomItems speichern
function saveCustomItems() {
    try {
        localStorage.setItem('kinderpos_custom_items', JSON.stringify(customItems));
    } catch (e) {
        console.log('Fehler beim Speichern von Custom-Items:', e);
    }
}

// CustomItems rendern (zB nach Seitenladung)
function renderCustomItems() {
    // Sicherstellen, dass der Container existiert
    const buttonsContainer = document.getElementById('buttons');
    if (!buttonsContainer) {
        console.log('buttons container nicht gefunden');
        return;
    }
    customItems.forEach(item => createCustomProductButton(item));
}

// Hilfsfunction zum Erstellen des Custom-Produktbuttons
function createCustomProductButton(item) {
    try {
        const buttonsContainer = document.getElementById('buttons');
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

        // Lösch-Button mit verbesserter Zentrierung (flexbox)
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
        del.style.display = 'flex';
        del.style.alignItems = 'center';
        del.style.justifyContent = 'center';
        del.style.padding = '0';
        del.style.fontSize = '16px';
        del.onclick = function(e){ 
            e.stopPropagation(); 
            wrap.remove();
            customItems = customItems.filter(ci => !(ci.name === item.name && ci.price === item.price));
            saveCustomItems();
        };

        wrap.appendChild(prodBtn);
        wrap.appendChild(del);
        buttonsContainer.appendChild(wrap);
    } catch (e) {
        console.log('Custom-Produktbutton konnte nicht hinzugefügt werden:', e);
    }
}

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

    // Zu Custom-Items hinzufügen und speichern
    customItems.push(item);
    saveCustomItems();

    // In den Warenkorb legen
    buy(item);

    // Custom-Produkt-Button erstellen
    createCustomProductButton(item);

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

    const total = cart.reduce((a, b) => a + b.price, 0);

    document.getElementById('cart').innerHTML = list;
    document.getElementById('total').innerText = 'Gesamt: €' + total.toFixed(2);
<!--    document.getElementById('payment_total').innerText = '€' + total.toFixed(2); -->

    // 🔁 Rückgeld immer nach jeder Änderung aktualisieren
    updatePaymentDisplay();
}

// Warenkorb drucken
function printCart() {
    if (cart.length === 0) {
        alert("Warenkorb ist leer!");
        return;
    }

    const total = cart.reduce((a, b) => a + b.price, 0);
    const given = parseFloat(paymentAmount) || 0;
    const change = given - total;

    // 🚫 Wenn zu wenig bezahlt wurde, abbrechen
    if (change < 0) {
        alert("Es wurde nicht genug bezahlt!");
        return;
    }

    // ✅ Wenn genug bezahlt wurde, weiter drucken
    lastPaymentGiven = given;
    lastPaymentChange = change;

    var audio = new Audio('/static/register_open.wav');
    audio.play();

    fetch('/print', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            items: cart,
            given: lastPaymentGiven,
            change: lastPaymentChange
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            cart = [];
            updateCart();
            resetPayment();
        } else {
            alert("Fehler beim Drucken: " + (data.message || "unbekannt"));
        }
    })
    .catch(err => alert("Fehler: " + err));
}

// Zahlungsbereich
let paymentAmount = '';

function addPaymentDigit(digit) {
    paymentAmount += digit;
    updatePaymentDisplay();
}

function clearPayment() {
    paymentAmount = '';
    updatePaymentDisplay();
}

function updatePaymentDisplay() {
    const total = cart.reduce((a, b) => a + b.price, 0);
    const given = parseFloat(paymentAmount) || 0;
    const change = given - total;

    document.getElementById('payment_given').innerText = '€' + given.toFixed(2);
    document.getElementById('payment_change').innerText = '€' + change.toFixed(2);

    // 🚫 Bon-Button deaktivieren, wenn zu wenig gezahlt wurde oder Warenkorb leer ist
    const printBtn = document.getElementById('print');
    if (printBtn) {
        const disabled = (change < 0 || cart.length === 0);
        printBtn.disabled = disabled;
        printBtn.style.opacity = disabled ? "0.5" : "1";
        printBtn.style.cursor = disabled ? "not-allowed" : "pointer";
    }
}

function resetPayment() {
    paymentAmount = '';
    updatePaymentDisplay();
}

// Globale Variablen für den Druck
let lastPaymentGiven = 0;
let lastPaymentChange = 0;

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

<div id="total" style="font-size:2em; margin:20px; color:#ff4500; font-weight:bold;"></div>

<!-- Zahlungsbereich mit Nummernpad -->
<div class="payment-section">
    <div class="payment-display">
<!--         <div class="payment-field">
             <label>Gesamt</label>
             <span id="payment_total">€0.00</span>
         </div> -->
        <div class="payment-field">
            <label>Gegeben</label>
            <span id="payment_given">€0.00</span>
        </div>
        <div class="payment-field">
            <label>Rückgeld</label>
            <span id="payment_change">€0.00</span>
        </div>
    </div>
    
    <div class="numpad">
        <button onclick="addPaymentDigit('1')">1</button>
        <button onclick="addPaymentDigit('2')">2</button>
        <button onclick="addPaymentDigit('3')">3</button>
        <button onclick="addPaymentDigit('4')">4</button>
        <button onclick="addPaymentDigit('5')">5</button>
        <button onclick="addPaymentDigit('6')">6</button>
        <button onclick="addPaymentDigit('7')">7</button>
        <button onclick="addPaymentDigit('8')">8</button>
        <button onclick="addPaymentDigit('9')">9</button>
        <button onclick="addPaymentDigit('.')">.</button>
        <button onclick="addPaymentDigit('0')">0</button>
        <button class="clear" onclick="clearPayment()">⛔</button>
        <button id="print" onclick="printCart()">✅</button>
    </div>
</div>

<!-- Script-Block: Custom-Items laden und Fullscreen -->
<script>
// Beim vollständigen Laden des DOM: Custom-Items aus localStorage laden
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded - Custom-Items laden...');
    loadCustomItems();
});

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
    data = request.get_json()
    # Items können direkt oder im 'items'-Feld kommen (für Rückwärtskompatibilität)
    items = data if isinstance(data, list) else data.get('items', [])
    given = data.get('given', 0) if isinstance(data, dict) else 0
    change = data.get('change', 0) if isinstance(data, dict) else 0
    
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
        p.text("...................................\n")
        p.set(bold=True)
        p.text(f"Gesamt: €{total:.2f}\n")
        p.set(bold=False)
        p.text(f"Gegeben: €{given:.2f}\n")
        p.text(f"Rückgeld: €{change:.2f}\n\n")
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
