# notifier.py - Modulo Notifiche Telegram con Diagnostica Avanzata

import urllib.request
import urllib.parse
import urllib.error
import json
import config

def send_telegram_alert(message):
    """Invia una notifica formattata in HTML a Telegram"""
    print("\n[MODULO NOTIFICHE TELEGRAM]")
    
    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID
    
    # Se le chiavi Telegram non sono impostate o sono quelle di default
    if not token or token == "IL_TUO_TELEGRAM_BOT_TOKEN":
        print("ℹ️  Notifiche Telegram non configurate (Modalità Simulazione Locale).")
        print("📱 ANTEPRIMA NOTIFICA SMARTPHONE:")
        print("-" * 38)
        print(message.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", ""))
        print("-" * 38)
        return

    # Invio reale dell'alert via API Telegram usando HTML
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("📲 Notifica inviata con successo al tuo account Telegram!")
    except urllib.error.HTTPError as e:
        error_details = e.read().decode('utf-8')
        print(f"⚠️ Errore Telegram ({e.code}): {error_details}")
    except Exception as e:
        print(f"⚠️ Errore di connessione: {e}")

if __name__ == "__main__":
    send_telegram_alert("🤖 <b>TEST BOT MULTI-ASSET</b>\nStrategia attiva.")