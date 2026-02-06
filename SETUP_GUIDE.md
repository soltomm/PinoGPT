# WhatsApp Football Team Balancer - Setup Guide

## 📋 Overview

This system creates balanced 5v5 football teams using ELO ratings and integrates with WhatsApp for easy team management.

**Features:**
- ✅ Add players with initial 1-10 ratings
- ✅ Send participant list → Get balanced teams instantly  
- ✅ Automatic reminder next day to record score
- ✅ ELO rating updates based on results
- ✅ Leaderboard and statistics

---

## 🚀 Quick Start Options

### Option 1: Meta Cloud API (FREE - Recommended)
**Pros:** Free, official Meta API, better reliability
**Cons:** More setup steps, verification required for production

### Option 2: Twilio (PAID - Easier)
**Pros:** Easier setup, instant testing
**Cons:** Costs money (~$0.005 per message)

---

## 📦 Installation

### 1. Install Dependencies

```bash
pip install flask twilio apscheduler requests
```

### 2. Files You Need

- `football_balancer.py` - Core ELO logic
- `whatsapp_bot.py` - Twilio integration
- `whatsapp_bot_meta.py` - Meta Cloud API integration (see below)

---

## 🔧 Setup: Meta Cloud API (FREE)

### Step 1: Create Meta App

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create new app → Select "Business" type
3. Add "WhatsApp" product to your app

### Step 2: Get Test Number

1. In WhatsApp dashboard, find "Test Number"
2. Add your phone number to test recipients
3. You'll receive a code - confirm it

### Step 3: Get Credentials

From WhatsApp settings, note:
- **Phone Number ID** (for sending messages)
- **WhatsApp Business Account ID**
- **Access Token** (temporary - lasts 24h)

### Step 4: Setup Webhook

1. Set Webhook URL: `https://your-domain.com/webhook`
2. Verify Token: Create a random string (e.g., `my_secret_token_123`)
3. Subscribe to: `messages`

### Step 5: Configure Environment

```bash
export META_ACCESS_TOKEN="your_access_token"
export META_PHONE_NUMBER_ID="your_phone_number_id"
export WEBHOOK_VERIFY_TOKEN="my_secret_token_123"
```

### Step 6: Run the Bot

```bash
python whatsapp_bot_meta.py
```

---

## 🔧 Setup: Twilio (PAID)

### Step 1: Create Twilio Account

1. Sign up at [twilio.com](https://www.twilio.com/try-twilio)
2. Get $15 free credit for testing

### Step 2: Setup WhatsApp Sandbox

1. Go to Twilio Console → Messaging → Try it Out → Send a WhatsApp message
2. Send the join code from your WhatsApp to the Twilio number
3. Your number is now connected!

### Step 3: Get Credentials

From Twilio Console:
- Account SID
- Auth Token  
- WhatsApp Number (e.g., +1415238886)

### Step 4: Configure Environment

```bash
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886"
```

### Step 5: Run the Bot

```bash
python whatsapp_bot.py
```

---

## 🌐 Deployment Options

### Option A: Railway (Easiest)

1. Push code to GitHub
2. Go to [railway.app](https://railway.app)
3. Create new project from GitHub repo
4. Add environment variables
5. Railway gives you a public URL automatically

**Cost:** Free tier available, then ~$5/month

### Option B: Heroku

```bash
heroku create football-bot
heroku config:set META_ACCESS_TOKEN="..."
git push heroku main
```

**Cost:** ~$7/month for hobby dyno

### Option C: AWS EC2 / DigitalOcean

1. Launch small instance ($5-10/month)
2. SSH into server
3. Install Python and dependencies
4. Run with `nohup python whatsapp_bot_meta.py &`
5. Use nginx for HTTPS

### Option D: Local + ngrok (Testing)

```bash
# Terminal 1
python whatsapp_bot.py

# Terminal 2  
ngrok http 5000
```

Use the ngrok URL as your webhook URL.

---

## 📱 Usage Examples

### Adding Players

```
You: add John 7
Bot: ✅ Added John with initial rating 7/10 (ELO: 1666)

You: add Mike 8
Bot: ✅ Added Mike with initial rating 8/10 (ELO: 1777)
```

### Creating Teams

```
You: teams

Bot: ⚽ TEAM SELECTION MODE
     Send me the list of 10 participants...

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

Game ID: 20240205_143022
✅ Reminder scheduled for tomorrow!
```

### Recording Score (Next Day)

```
Bot: ⚽ GAME RESULT REQUEST
     How did yesterday's game go?
     Reply with the score (e.g., '5-3')
     Game ID: 20240205_143022

You: 5-3

Bot: 📊 GAME RESULT RECORDED

🔵 Team 1: 5
🔴 Team 2: 3
🏆 Winner: Team 1

Rating Changes:
  Mike: 1777 → 1792 (+15)
  Sarah: 1555 → 1570 (+15)
  David: 1666 → 1681 (+15)
  Lisa: 1555 → 1570 (+15)
  Anna: 1444 → 1459 (+15)
  Tom: 1888 → 1873 (-15)
  Emma: 1444 → 1429 (-15)
  John: 1666 → 1651 (-15)
  James: 1777 → 1762 (-15)
  Chris: 1666 → 1651 (-15)
```

### View Leaderboard

```
You: leaderboard

Bot: 🏆 TOP 10 PLAYERS

1. Tom
   ELO: 1873 | Games: 1 | Win Rate: 0.0%
2. Mike  
   ELO: 1792 | Games: 1 | Win Rate: 100.0%
...
```

---

## 🎯 Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show all commands | `help` |
| `add [name] [rating]` | Add player (1-10) | `add John 7` |
| `teams` | Start team selection | `teams` |
| `score` | Record game result | `score` then `5-3` |
| `leaderboard` | Show rankings | `leaderboard` |
| `pending` | Show unrecorded games | `pending` |

---

## 🔒 Security Tips

1. **Never commit credentials** - Use environment variables
2. **Validate webhook** - Check verify tokens
3. **Rate limiting** - Prevent spam (Flask-Limiter)
4. **HTTPS only** - Use SSL certificates
5. **Whitelist numbers** - Only allow known group members

---

## 🐛 Troubleshooting

### "❌ Unknown players: John"
**Solution:** Add the player first with `add John 7`

### "❌ Need exactly 10 players, got 8"
**Solution:** Send exactly 10 names in your list

### Bot not responding
1. Check webhook URL is correct
2. Check environment variables are set
3. Look at server logs: `heroku logs --tail`
4. Verify WhatsApp number is connected

### Reminder not sent
1. Check scheduler is running
2. Verify game was created successfully  
3. Check game_id exists in pending_games

---

## 📊 Database (Optional Upgrade)

For production, consider using PostgreSQL instead of JSON file:

```bash
pip install psycopg2-binary sqlalchemy
```

Benefits:
- Multiple concurrent users
- Better data integrity
- Easier backups
- Query capabilities

---

## 🚀 Production Checklist

- [ ] Get Meta Business verification (for unlimited messages)
- [ ] Set up proper database (PostgreSQL)
- [ ] Configure logging and monitoring
- [ ] Set up automated backups
- [ ] Add error tracking (Sentry)
- [ ] Implement rate limiting
- [ ] Add admin commands (reset ratings, etc.)
- [ ] Create web dashboard for statistics

---

## 💡 Future Enhancements

1. **Position-based balancing** (GK, DEF, MID, FWD)
2. **Player availability tracking** ("Who's playing next week?")
3. **Venue/time scheduling**
4. **Match statistics** (goals, assists)
5. **Team chemistry** (players who work well together)
6. **Substitution suggestions** during game
7. **Historical matchups** analysis

---

## 📞 Support

Issues? Questions? 

1. Check the troubleshooting section
2. Review Meta/Twilio documentation
3. Check server logs for errors

---

## 📄 License

MIT - Feel free to modify and use!
