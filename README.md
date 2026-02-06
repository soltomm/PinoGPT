# ⚽ WhatsApp Football Team Balancer

An intelligent 5v5 football team balancer using ELO ratings, integrated with WhatsApp for seamless team management.

## 🎯 Features

- ✅ **Initial Player Ratings**: Add players with 1-10 skill votes
- ✅ **Smart Team Balancing**: Algorithm creates balanced teams based on ELO ratings
- ✅ **WhatsApp Integration**: Everything happens in your group chat
- ✅ **Automatic Reminders**: Bot asks for game results 24 hours later
- ✅ **ELO Rating System**: Professional rating adjustments based on results
- ✅ **Leaderboard**: Track player stats and rankings
- ✅ **Persistent Storage**: All data saved automatically

## 🚀 Quick Start

### 1. Test the Core Logic (No WhatsApp Required)

```bash
python test_balancer.py
```

This runs all tests and shows you how the system works!

### 2. Choose Your Integration

#### Option A: Meta Cloud API (FREE) ⭐ Recommended

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Meta credentials

# Run the bot
python whatsapp_bot_meta.py
```

# Run the bot
python whatsapp_bot.py
```

### 3. Deploy to Cloud

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed deployment instructions.

**Quick Deploy Options:**
- **Railway**: Push to GitHub → Connect to Railway → Deploy
- **Heroku**: `heroku create && git push heroku main`
- **Local Testing**: Use ngrok to expose your local server

## 📱 Usage Example

### Add Players

```
You: add John 7
Bot: ✅ Added John with initial rating 7/10 (ELO: 1666)

You: add Mike 8
Bot: ✅ Added Mike with initial rating 8/10 (ELO: 1777)
```

### Create Teams

```
You: teams

Bot: ⚽ TEAM SELECTION MODE
     Send me 10 participant names...

You: 
John
Mike  
Sarah
Tom
Emma
David
Lisa
James
Anna
Chris

Bot: ⚽ TEAMS CREATED

🔵 Team 1 (Avg ELO: 1612)
  • Mike (1777)
  • Sarah (1555)
  • David (1666)
  • Lisa (1555)
  • Anna (1444)

🔴 Team 2 (Avg ELO: 1608)
  • Tom (1888)
  • Emma (1444)
  • John (1666)
  • James (1777)
  • Chris (1666)

⏰ I'll ask for the score tomorrow!
```

### Record Results (Next Day)

```
Bot: ⚽ How did yesterday's game go?
     Reply with the score (e.g., '5-3')

You: 5-3

Bot: 📊 GAME RESULT RECORDED

🔵 Team 1: 5
🔴 Team 2: 3
🏆 Winner: Team 1

Rating Changes:
  Mike: 1777 → 1792 (+15)
  Sarah: 1555 → 1570 (+15)
  ...
```

### View Rankings

```
You: leaderboard

Bot: 🏆 TOP 10 PLAYERS

1. Tom
   ELO: 1905 | Games: 5 | Win Rate: 80.0%
2. Mike
   ELO: 1792 | Games: 5 | Win Rate: 60.0%
...
```

## 🎮 Commands

| Command | Description |
|---------|-------------|
| `help` | Show all commands |
| `add [name] [rating]` | Add player with 1-10 rating |
| `teams` | Create balanced teams |
| `score` | Record game result |
| `leaderboard` | Show top players |
| `pending` | Show games waiting for scores |
| `stats [name]` | Show player statistics |

## 🏗️ Architecture

```
┌─────────────────┐
│   WhatsApp      │
│   (User Input)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Flask Webhook  │
│  (Message Handler)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TeamBalancer    │
│ (Core Logic)    │
│ - ELO Algorithm │
│ - Team Creation │
│ - Rating Updates│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JSON Storage   │
│  (Persistence)  │
└─────────────────┘
```

## 📊 How ELO Ratings Work

1. **Initial Conversion**: 1-10 votes → 1000-2000 ELO scale
   - Vote 1 = 1000 ELO
   - Vote 5 = 1500 ELO
   - Vote 10 = 2000 ELO

2. **Team Balancing**: Snake draft algorithm ensures similar average team ELO

3. **Rating Updates**: After each game
   - Winner gains points
   - Loser loses points
   - Amount depends on:
     - Expected outcome (underdog wins = bigger changes)
     - Score difference (5-1 = bigger change than 3-2)
     - K-factor (32 for amateur players)

4. **Formula**: 
   ```
   Change = K × Multiplier × (Actual - Expected)
   Multiplier = 1 + (goal_diff - 1) × 0.1
   Expected = 1 / (1 + 10^((OpponentELO - PlayerELO) / 400))
   ```

## 🗂️ File Structure

```
.
├── football_balancer.py      # Core ELO logic
├── whatsapp_bot_meta.py      # Meta Cloud API integration (FREE)
├── whatsapp_bot.py            # Twilio integration (PAID)
├── test_balancer.py           # Test suite
├── requirements.txt           # Dependencies
├── Procfile                   # Heroku deployment
├── .env.example               # Environment template
├── SETUP_GUIDE.md             # Detailed setup instructions
└── README.md                  # This file
```

## 🔧 Configuration

### Environment Variables

**Meta Cloud API:**
- `META_ACCESS_TOKEN` - Your WhatsApp API token
- `META_PHONE_NUMBER_ID` - Your phone number ID
- `WEBHOOK_VERIFY_TOKEN` - Random secret for webhook verification

**Twilio:**
- `TWILIO_ACCOUNT_SID` - Your Twilio account SID
- `TWILIO_AUTH_TOKEN` - Your Twilio auth token
- `TWILIO_WHATSAPP_NUMBER` - Your Twilio WhatsApp number

**General:**
- `PORT` - Server port (default: 5000)

## 🚢 Deployment

### Railway (Recommended)

1. Push code to GitHub
2. Connect Railway to your repo
3. Add environment variables in Railway dashboard
4. Deploy automatically on push

### Heroku

```bash
heroku create football-balancer
heroku config:set META_ACCESS_TOKEN="..."
heroku config:set META_PHONE_NUMBER_ID="..."
git push heroku main
```

### Self-Hosted

```bash
# Run with gunicorn for production
gunicorn -w 4 -b 0.0.0.0:5000 whatsapp_bot_meta:app
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_balancer.py
```

This tests:
- ✅ Player management
- ✅ Message parsing
- ✅ Team creation algorithm
- ✅ Score parsing
- ✅ ELO calculations
- ✅ Data persistence
- ✅ Edge cases

## 📝 API Endpoints

- `POST /webhook` - Receive WhatsApp messages
- `GET /webhook` - Verify webhook (Meta)
- `GET /health` - Health check
- `GET /stats` - Bot statistics

## 🐛 Troubleshooting

### Bot not responding
1. Check webhook URL is correct
2. Verify environment variables
3. Check server logs
4. Test with `/health` endpoint

### "Unknown players" error
Add players first with `add [name] [rating]`

### Need exactly 10 players
Send exactly 10 names in participant list

### Reminder not sent
1. Check scheduler is running
2. Verify game was created
3. Check server uptime (24+ hours)

## 🎯 Future Enhancements

- [ ] Position-based balancing (GK, DEF, MID, FWD)
- [ ] Player availability tracking
- [ ] Match statistics (goals, assists)
- [ ] Team chemistry analysis
- [ ] Web dashboard for stats
- [ ] Multi-group support
- [ ] PostgreSQL database
- [ ] Admin commands

## 📚 Resources

- [Setup Guide](SETUP_GUIDE.md) - Detailed setup instructions
- [Meta WhatsApp Docs](https://developers.facebook.com/docs/whatsapp)
- [Twilio WhatsApp Docs](https://www.twilio.com/docs/whatsapp)
- [ELO Rating System](https://en.wikipedia.org/wiki/Elo_rating_system)

## 🤝 Contributing

Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📄 License

MIT License - Use freely!

---

**Made with ⚽ for football lovers**

Questions? Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions!
