"""
WhatsApp Bot for Football Team Balancer
Uses Twilio WhatsApp API and Flask

Setup instructions:
1. pip install flask twilio apscheduler
2. Set environment variables: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
3. Run: python whatsapp_bot.py
4. Expose via ngrok or deploy to cloud
"""

import os
from datetime import datetime, timedelta
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from apscheduler.schedulers.background import BackgroundScheduler
from football_balancer import TeamBalancer

app = Flask(__name__)

# Initialize Twilio
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize Team Balancer
balancer = TeamBalancer()
balancer.load_from_file()

# Store game timestamps for next-day reminders
game_reminders = {}  # game_id -> (phone_number, timestamp)

# Scheduler for sending reminders
scheduler = BackgroundScheduler()
scheduler.start()


def send_whatsapp_message(to_number: str, message: str):
    """Send WhatsApp message via Twilio"""
    try:
        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message,
            to=f'whatsapp:{to_number}'
        )
        return message.sid
    except Exception as e:
        print(f"Error sending message: {e}")
        return None


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
        # Format: "add John 7"
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
    elif message in ['help', 'commands', 'start']:
        return """⚽ *FOOTBALL TEAM BALANCER*

*Commands:*
• *add [name] [rating]* - Add player (e.g., "add John 7")
• *teams* - Enter team selection mode
• *score* - Enter score submission mode
• *leaderboard* - Show top players
• *pending* - Show games waiting for scores
• *help* - Show this message

*Workflows:*
1️⃣ Add all players with ratings (1-10)
2️⃣ Send "teams" then list 10 participants
3️⃣ Next day, send "score" then the result
"""
    
    # Command: Leaderboard
    elif message in ['leaderboard', 'rankings', 'top']:
        return balancer.get_leaderboard()
    
    # Command: Pending games
    elif message in ['pending', 'games']:
        return balancer.get_pending_games()
    
    # Command: Teams (start team selection)
    elif message == 'teams':
        return """⚽ *TEAM SELECTION MODE*

Send me the list of 10 participants, one per line or comma-separated.

Example:
John
Mike
Sarah
Tom
...

Or: John, Mike, Sarah, Tom, ...
"""
    
    # Command: Score (start score submission)
    elif message == 'score':
        pending = balancer.get_pending_games()
        if pending == "No pending games":
            return "❌ No pending games. Create teams first!"
        return f"{pending}\n\nReply with: [game_id] [score]\nExample: 20240205_143022 5-3"
    
    # Try to parse as participant list (if contains newlines or multiple names)
    elif '\n' in incoming_message or ',' in incoming_message:
        names = balancer.parse_participant_list(incoming_message)
        if len(names) == 10:
            teams, response = balancer.create_teams(names)
            if teams:
                balancer.save_to_file()
                # Schedule reminder for next day
                schedule_score_request(teams['game_id'], from_number.replace('whatsapp:', ''))
                response += "\n\n✅ Reminder scheduled for tomorrow to record the score!"
            return response
        else:
            return f"❌ Expected 10 players, got {len(names)}. Please send exactly 10 names."
    
    # Try to parse as score submission
    elif any(char in message for char in ['-', ' ']) and any(char.isdigit() for char in message):
        # Check if message contains game_id
        words = incoming_message.split()
        
        # Try to find game_id and score
        game_id = None
        score_str = None
        
        for word in words:
            if '_' in word and len(word) > 10:  # Looks like a game_id
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
        
        return "❌ Could not parse score. Use format: [game_id] 5-3\nOr just '5-3' if only one pending game."
    
    # Default response
    return "❓ I didn't understand that. Send 'help' for commands."


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages from Twilio"""
    incoming_msg = request.values.get('Body', '')
    from_number = request.values.get('From', '')
    
    # Process message
    response_text = handle_message(incoming_msg, from_number)
    
    # Create Twilio response
    resp = MessagingResponse()
    resp.message(response_text)
    
    return str(resp)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return {'status': 'healthy', 'players': len(balancer.players)}


if __name__ == '__main__':
    print("🚀 WhatsApp Football Bot Starting...")
    print(f"Players loaded: {len(balancer.players)}")
    print(f"Pending games: {len(balancer.pending_games)}")
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
