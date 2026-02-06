"""
WhatsApp Bot for Football Team Balancer
Uses Meta Cloud API (FREE)

Setup instructions in SETUP_GUIDE.md

Environment variables needed:
- META_ACCESS_TOKEN: Your WhatsApp Business API token
- META_PHONE_NUMBER_ID: Your WhatsApp phone number ID
- WEBHOOK_VERIFY_TOKEN: Random string for webhook verification
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

# Store game timestamps for next-day reminders
game_reminders = {}

# Scheduler for sending reminders
scheduler = BackgroundScheduler()
scheduler.start()


def send_whatsapp_message(to_number: str, message: str):
    """Send WhatsApp message via Meta Cloud API"""
    
    # Remove 'whatsapp:' prefix if present
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
        print(f"Error sending message: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def mark_message_as_read(message_id: str):
    """Mark a message as read"""
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
        print(f"Error marking as read: {e}")


def schedule_score_request(game_id: str, phone_number: str):
    """Schedule a message to ask for score 24 hours later"""
    send_time = datetime.now() + timedelta(hours=24)
    
    def send_reminder():
        message = f"⚽ *GAME RESULT REQUEST*\n\n"
        message += f"How did yesterday's game go?\n\n"
        message += f"Reply with the score (e.g., '5-3' or '3-2')\n"
        message += f"_Game ID: {game_id}_"
        send_whatsapp_message(phone_number, message)
    
    scheduler.add_job(
        send_reminder,
        'date',
        run_date=send_time,
        id=f'reminder_{game_id}'
    )
    
    game_reminders[game_id] = (phone_number, send_time)


def handle_message(incoming_message: str, from_number: str) -> str:
    """Process incoming WhatsApp message and return response"""
    
    message = incoming_message.strip().lower()
    
    # Command: Add player
    if message.startswith('add '):
        parts = incoming_message.split()
        if len(parts) >= 3:
            name = ' '.join(parts[1:-1])
            try:
                vote = int(parts[-1])
                response = balancer.add_player(name, vote)
                balancer.save_to_file()
                return response
            except ValueError:
                return "❌ Invalid format. Use: add [name] [rating 1-10]"
        return "❌ Invalid format. Use: add [name] [rating 1-10]"
    
    # Command: Help
    elif message in ['help', 'commands', 'start', 'hi', 'hello']:
        return """⚽ *FOOTBALL TEAM BALANCER*

*Commands:*
• *add [name] [rating]* - Add player
  Example: add John 7
• *teams* - Create balanced teams
• *score* - Record game result
• *leaderboard* - Show rankings
• *pending* - Show unrecorded games
• *stats [name]* - Show player stats
• *help* - Show this message

*How to use:*
1️⃣ Add all players with ratings 1-10
2️⃣ Send "teams" then list 10 names
3️⃣ Next day, send "score" then result
"""
    
    # Command: Leaderboard
    elif message in ['leaderboard', 'rankings', 'top', 'rank']:
        return balancer.get_leaderboard()
    
    # Command: Pending games
    elif message in ['pending', 'games']:
        return balancer.get_pending_games()
    
    # Command: Player stats
    elif message.startswith('stats '):
        player_name = incoming_message[6:].strip()
        player = balancer._find_player(player_name)
        if player:
            win_rate = (player.wins / player.games_played * 100) if player.games_played > 0 else 0
            return f"""📊 *{player.name}*

ELO Rating: {player.elo}
Games Played: {player.games_played}
Wins: {player.wins}
Losses: {player.losses}
Win Rate: {win_rate:.1f}%
"""
        return f"❌ Player '{player_name}' not found"
    
    # Command: Teams (start team selection)
    elif message in ['teams', 'team', 'create teams']:
        return """⚽ *TEAM SELECTION MODE*

Send me the list of 10 participants.

*Format options:*
1. One name per line:
John
Mike
Sarah
...

2. Comma-separated:
John, Mike, Sarah, Tom, ...

Send the list now! 👇
"""
    
    # Command: Score (start score submission)
    elif message in ['score', 'result', 'record']:
        pending = balancer.get_pending_games()
        if pending == "No pending games":
            return "❌ No pending games. Create teams first!"
        return f"{pending}\n\n💡 Reply with the score:\n• Just score: 5-3\n• With ID: 20240205_143022 5-3"
    
    # Try to parse as participant list
    elif '\n' in incoming_message or ',' in incoming_message:
        names = balancer.parse_participant_list(incoming_message)
        if len(names) == 10:
            teams, response = balancer.create_teams(names)
            if teams:
                balancer.save_to_file()
                schedule_score_request(teams['game_id'], from_number)
                response += "\n\n⏰ I'll ask for the score tomorrow!"
            return response
        elif len(names) > 0:
            return f"❌ Need exactly 10 players, got {len(names)}.\n\n👥 Send exactly 10 names to create teams."
    
    # Try to parse as score submission
    elif any(char in message for char in ['-', ' ']) and any(char.isdigit() for char in message):
        words = incoming_message.split()
        
        game_id = None
        score_str = None
        
        # Find game_id and score
        for word in words:
            if '_' in word and len(word) > 10:
                game_id = word
            elif balancer.parse_score(word):
                score_str = word
        
        # If only one pending game, use that
        if not game_id and len(balancer.pending_games) == 1:
            game_id = list(balancer.pending_games.keys())[0]
        
        if game_id and score_str:
            score = balancer.parse_score(score_str)
            if score:
                response = balancer.update_ratings(game_id, score[0], score[1])
                balancer.save_to_file()
                return response
        
        # Try just score if one pending game
        score = balancer.parse_score(incoming_message)
        if score and len(balancer.pending_games) == 1:
            game_id = list(balancer.pending_games.keys())[0]
            response = balancer.update_ratings(game_id, score[0], score[1])
            balancer.save_to_file()
            return response
        
        return "❌ Could not parse score.\n\n💡 Format: 5-3 or 20240205_143022 5-3"
    
    # Default response
    return "❓ I didn't understand that.\n\nSend *help* for commands."


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Handle Meta WhatsApp webhook"""
    
    if request.method == 'GET':
        # Webhook verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        print(f"🔍 Webhook GET request:")
        print(f"   mode: {mode}")
        print(f"   token received: {token}")
        print(f"   token expected: {WEBHOOK_VERIFY_TOKEN}")
        print(f"   challenge: {challenge}")
        print(f"   tokens match: {token == WEBHOOK_VERIFY_TOKEN}")

        if mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
            print("✅ Webhook verified")
            if challenge:
                response = make_response(challenge, 200)
                response.headers['Content-Type'] = 'text/plain'
                return response
            else:
                print("⚠️ No challenge received")
                return 'OK', 200
        else:
            print("❌ Webhook verification failed")
            return 'Forbidden', 403
    
    elif request.method == 'POST':
        # Handle incoming messages
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data'}), 400
        
        try:
            # Extract message data
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])
            
            if not messages:
                return jsonify({'status': 'no messages'}), 200
            
            message = messages[0]
            message_id = message.get('id')
            from_number = message.get('from')
            message_type = message.get('type')
            
            # Only handle text messages
            if message_type == 'text':
                text_body = message.get('text', {}).get('body', '')
                
                # Mark as read
                mark_message_as_read(message_id)
                
                # Process message
                response_text = handle_message(text_body, from_number)
                
                # Send response
                send_whatsapp_message(from_number, response_text)
            
            return jsonify({'status': 'success'}), 200
            
        except Exception as e:
            print(f"Error processing webhook: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'players': len(balancer.players),
        'pending_games': len(balancer.pending_games),
        'scheduled_reminders': len(game_reminders)
    })


@app.route('/stats', methods=['GET'])
def stats():
    """Get bot statistics"""
    return jsonify({
        'total_players': len(balancer.players),
        'pending_games': len(balancer.pending_games),
        'scheduled_reminders': len(game_reminders),
        'top_players': [
            {
                'name': p.name,
                'elo': p.elo,
                'games': p.games_played
            }
            for p in sorted(balancer.players.values(), key=lambda x: x.elo, reverse=True)[:5]
        ]
    })


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 WhatsApp Football Bot Starting (Meta Cloud API)")
    print("=" * 50)
    print(f"✅ Players loaded: {len(balancer.players)}")
    print(f"⏳ Pending games: {len(balancer.pending_games)}")
    print(f"📱 Phone Number ID: {META_PHONE_NUMBER_ID}")
    print("=" * 50)
    
    # Verify configuration
    if not META_ACCESS_TOKEN:
        print("⚠️  WARNING: META_ACCESS_TOKEN not set!")
    if not META_PHONE_NUMBER_ID:
        print("⚠️  WARNING: META_PHONE_NUMBER_ID not set!")
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
