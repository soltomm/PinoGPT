"""
PinoGPT - Bot WhatsApp per Bilanciamento Squadre di Calcetto
Usa Meta Cloud API (GRATUITO)

Istruzioni di configurazione in SETUP_GUIDE.md

Variabili d'ambiente necessarie:
- META_ACCESS_TOKEN: Il tuo token WhatsApp Business API
- META_PHONE_NUMBER_ID: Il tuo ID numero di telefono WhatsApp
- WEBHOOK_VERIFY_TOKEN: Stringa casuale per verifica webhook
"""

import os
from dotenv import load_dotenv
load_dotenv()

import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response
from apscheduler.schedulers.background import BackgroundScheduler
from football_balancer import TeamBalancer

app = Flask(__name__)

# Meta Cloud API Configuration
META_ACCESS_TOKEN = os.environ.get('META_ACCESS_TOKEN')
META_PHONE_NUMBER_ID = os.environ.get('META_PHONE_NUMBER_ID')
WEBHOOK_VERIFY_TOKEN = os.environ.get('WEBHOOK_VERIFY_TOKEN', 'my_secret_token')
META_API_VERSION = 'v18.0'
META_API_URL = f'https://graph.facebook.com/{META_API_VERSION}/{META_PHONE_NUMBER_ID}/messages'

# Initialize Team Balancer
balancer = TeamBalancer()
balancer.load_from_file()

# Memorizza timestamp partite per promemoria del giorno dopo
game_reminders = {}

# Scheduler per invio promemoria
scheduler = BackgroundScheduler()
scheduler.start()


def send_whatsapp_message(to_number: str, message: str):
    """Invia messaggio WhatsApp tramite Meta Cloud API"""
    
    # Rimuovi prefisso 'whatsapp:' se presente
    to_number = to_number.replace('whatsapp:', '')
    
    headers = {
        'Authorization': f'Bearer {META_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual',
        'to': to_number,
        'type': 'text',
        'text': {
            'preview_url': False,
            'body': message
        }
    }
    
    try:
        response = requests.post(META_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore invio messaggio: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def mark_message_as_read(message_id: str):
    """Segna un messaggio come letto"""
    headers = {
        'Authorization': f'Bearer {META_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'messaging_product': 'whatsapp',
        'status': 'read',
        'message_id': message_id
    }
    
    try:
        response = requests.post(META_API_URL, headers=headers, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Errore nel segnare come letto: {e}")


def schedule_score_request(game_id: str, phone_number: str):
    """Programma un messaggio per chiedere il risultato dopo 24 ore"""
    send_time = datetime.now() + timedelta(hours=24)

    def send_reminder():
        message = f"⚽ *RICHIESTA RISULTATO PARTITA*\n\n"
        message += f"Com'è andata la partita di ieri?\n\n"
        message += f"Rispondi con il risultato (es. '5-3' o '3-2')\n"
        message += f"_ID Partita: {game_id}_"
        send_whatsapp_message(phone_number, message)
    
    scheduler.add_job(
        send_reminder,
        'date',
        run_date=send_time,
        id=f'reminder_{game_id}'
    )
    
    game_reminders[game_id] = (phone_number, send_time)


def handle_message(incoming_message: str, from_number: str) -> str:
    """Elabora messaggio WhatsApp in arrivo e restituisce risposta"""

    message = incoming_message.strip().lower()

    # Comando: Aggiungi giocatore
    if message.startswith('aggiungi '):
        parts = incoming_message.split()
        if len(parts) >= 3:
            name = ' '.join(parts[1:-1])
            try:
                vote = int(parts[-1])
                response = balancer.add_player(name, vote)
                balancer.save_to_file()
                return response
            except ValueError:
                return "❌ Formato non valido. Usa: aggiungi [nome] [voto 1-10]"
        return "❌ Formato non valido. Usa: aggiungi [nome] [voto 1-10]"

    # Comando: Rimuovi giocatore
    elif message.startswith('rimuovi '):
        player_name = incoming_message[8:].strip()
        if not player_name:
            return "❌ Formato non valido. Usa: rimuovi [nome]"
        response = balancer.remove_player(player_name)
        balancer.save_to_file()
        return response

    # Comando: Aiuto
    elif message in ['help', 'aiuto', 'comandi', 'start', 'ciao', 'hello']:
        return """⚽ *PinoGPT*

*Comandi:*
• *aggiungi [nome] [voto]* - Aggiungi giocatore
  Esempio: aggiungi Marco 7 (voto da 1 a 10)
• *rimuovi [nome]* - Rimuovi giocatore
• *squadre* - Crea squadre bilanciate
• *risultato* - Registra il risultato della partita
• *classifica* - Mostra la classifica
• *inattesa* - Mostra le partite non registrate
• *stats [nome]* - Mostra statistiche giocatore
• *aiuto* - Mostra questo messaggio

*Come usare:*
1️⃣ Aggiungi tutti i giocatori con voti 1-10
2️⃣ Scrivi "squadre" poi elenca 10 nomi
3️⃣ Il giorno dopo, scrivi "risultato" poi il punteggio
"""
    
    # Comando: Classifica
    elif message in ['classifica', 'leaderboard', 'rankings', 'top', 'rank']:
        return balancer.get_leaderboard()

    # Comando: Partite in attesa
    elif message in ['inattesa', 'pending', 'partite']:
        return balancer.get_pending_games()

    # Comando: Statistiche giocatore
    elif message.startswith('stats '):
        player_name = incoming_message[6:].strip()
        player = balancer._find_player(player_name)
        if player:
            win_rate = (player.wins / player.games_played * 100) if player.games_played > 0 else 0
            return f"""📊 *{player.name}*

Punteggio ELO: {player.elo}
Partite Giocate: {player.games_played}
Vittorie: {player.wins}
Sconfitte: {player.losses}
Percentuale Vittorie: {win_rate:.1f}%
"""
        return f"❌ Giocatore '{player_name}' non trovato"

    # Comando: Squadre (inizia selezione squadre)
    elif message in ['squadre', 'teams', 'team', 'crea squadre']:
        return """⚽ *MODALITÀ SELEZIONE SQUADRE*

Inviami la lista di 10 partecipanti.

*Opzioni formato:*
1. Un nome per riga:
Marco
Luca
Anna
...

2. Separati da virgola:
Marco, Luca, Anna, Paolo, ...

Invia la lista adesso! 👇
"""
    
    # Comando: Risultato (inserimento punteggio)
    elif message in ['risultato', 'score', 'result', 'punteggio']:
        pending = balancer.get_pending_games()
        if pending == "No pending games":
            return "❌ Nessuna partita in attesa. Prima crea le squadre!"
        return f"{pending}\n\n💡 Rispondi con il risultato:\n• Solo punteggio: 5-3\n• Con ID: 20240205_143022 5-3"

    # Prova a interpretare come lista partecipanti
    elif '\n' in incoming_message or ',' in incoming_message:
        names = balancer.parse_participant_list(incoming_message)
        if len(names) == 10:
            teams, response = balancer.create_teams(names)
            if teams:
                balancer.save_to_file()
                schedule_score_request(teams['game_id'], from_number)
                response += "\n\n⏰ Ti chiederò il risultato domani!"
            return response
        elif len(names) > 0:
            return f"❌ Servono esattamente 10 giocatori, ne hai inseriti {len(names)}.\n\n👥 Invia esattamente 10 nomi per creare le squadre."

    # Prova a interpretare come inserimento risultato
    elif any(char in message for char in ['-', ' ']) and any(char.isdigit() for char in message):
        words = incoming_message.split()

        game_id = None
        score_str = None

        # Trova game_id e punteggio
        for word in words:
            if '_' in word and len(word) > 10:
                game_id = word
            elif balancer.parse_score(word):
                score_str = word

        # Se c'è solo una partita in attesa, usa quella
        if not game_id and len(balancer.pending_games) == 1:
            game_id = list(balancer.pending_games.keys())[0]

        if game_id and score_str:
            score = balancer.parse_score(score_str)
            if score:
                response = balancer.update_ratings(game_id, score[0], score[1])
                balancer.save_to_file()
                return response

        # Prova solo il punteggio se c'è una sola partita in attesa
        score = balancer.parse_score(incoming_message)
        if score and len(balancer.pending_games) == 1:
            game_id = list(balancer.pending_games.keys())[0]
            response = balancer.update_ratings(game_id, score[0], score[1])
            balancer.save_to_file()
            return response

        return "❌ Non riesco a interpretare il risultato.\n\n💡 Formato: 5-3 oppure 20240205_143022 5-3"

    # Risposta predefinita
    return "❓ Non ho capito.\n\nScrivi *aiuto* per i comandi."


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Gestisce webhook Meta WhatsApp"""

    if request.method == 'GET':
        # Verifica webhook
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        print(f"🔍 Richiesta GET webhook:")
        print(f"   mode: {mode}")
        print(f"   token ricevuto: {token}")
        print(f"   token atteso: {WEBHOOK_VERIFY_TOKEN}")
        print(f"   challenge: {challenge}")
        print(f"   token corrisponde: {token == WEBHOOK_VERIFY_TOKEN}")

        if mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
            print("✅ Webhook verificato")
            if challenge:
                response = make_response(challenge, 200)
                response.headers['Content-Type'] = 'text/plain'
                return response
            else:
                print("⚠️ Nessun challenge ricevuto")
                return 'OK', 200
        else:
            print("❌ Verifica webhook fallita")
            return 'Forbidden', 403

    elif request.method == 'POST':
        # Gestisci messaggi in arrivo
        data = request.get_json()

        if not data:
            return jsonify({'status': 'error', 'message': 'Nessun dato'}), 400

        try:
            # Estrai dati messaggio
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])

            if not messages:
                return jsonify({'status': 'nessun messaggio'}), 200

            message = messages[0]
            message_id = message.get('id')
            from_number = message.get('from')
            message_type = message.get('type')

            # Gestisci solo messaggi di testo
            if message_type == 'text':
                text_body = message.get('text', {}).get('body', '')

                # Segna come letto
                mark_message_as_read(message_id)

                # Elabora messaggio
                response_text = handle_message(text_body, from_number)

                # Invia risposta
                send_whatsapp_message(from_number, response_text)

            return jsonify({'status': 'success'}), 200

        except Exception as e:
            print(f"Errore elaborazione webhook: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Endpoint controllo stato"""
    return jsonify({
        'status': 'attivo',
        'giocatori': len(balancer.players),
        'partite_in_attesa': len(balancer.pending_games),
        'promemoria_programmati': len(game_reminders)
    })


@app.route('/stats', methods=['GET'])
def stats():
    """Ottieni statistiche bot"""
    return jsonify({
        'giocatori_totali': len(balancer.players),
        'partite_in_attesa': len(balancer.pending_games),
        'promemoria_programmati': len(game_reminders),
        'top_giocatori': [
            {
                'nome': p.name,
                'elo': p.elo,
                'partite': p.games_played
            }
            for p in sorted(balancer.players.values(), key=lambda x: x.elo, reverse=True)[:5]
        ]
    })


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 PinoGPT in avvio (Meta Cloud API)")
    print("=" * 50)
    print(f"✅ Giocatori caricati: {len(balancer.players)}")
    print(f"⏳ Partite in attesa: {len(balancer.pending_games)}")
    print(f"📱 Phone Number ID: {META_PHONE_NUMBER_ID}")
    print("=" * 50)

    # Verifica configurazione
    if not META_ACCESS_TOKEN:
        print("⚠️  ATTENZIONE: META_ACCESS_TOKEN non impostato!")
    if not META_PHONE_NUMBER_ID:
        print("⚠️  ATTENZIONE: META_PHONE_NUMBER_ID non impostato!")

    # Avvia app Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
