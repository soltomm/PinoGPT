"""
5v5 Football Team Balancer with ELO Rating System
Designed for WhatsApp bot integration
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional


class Player:
    """Represents a football player with ELO rating"""
    
    def __init__(self, name: str, initial_rating: int = 1500):
        self.name = name
        self.elo = initial_rating
        self.games_played = 0
        self.wins = 0
        self.losses = 0
    
    @classmethod
    def from_vote(cls, name: str, vote: int):
        """Create player from 1-10 vote, converting to ELO scale"""
        # Convert 1-10 scale to 1000-2000 ELO range
        # vote=1 -> 1000, vote=5 -> 1500, vote=10 -> 2000
        elo = 1000 + (vote - 1) * (1000 / 9)
        return cls(name, int(elo))
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'elo': self.elo,
            'games_played': self.games_played,
            'wins': self.wins,
            'losses': self.losses
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        player = cls(data['name'], data['elo'])
        player.games_played = data['games_played']
        player.wins = data['wins']
        player.losses = data['losses']
        return player
    
    def __repr__(self):
        return f"{self.name} (ELO: {self.elo})"


class TeamBalancer:
    """Main class for team balancing and rating management"""
    
    def __init__(self, k_factor: int = 32):
        """
        Initialize balancer
        
        Args:
            k_factor: ELO K-factor (higher = more volatile ratings)
                     32 is standard for amateur players
        """
        self.players: Dict[str, Player] = {}
        self.k_factor = k_factor
        self.pending_games: Dict[str, dict] = {}  # game_id -> game data
    
    def add_player(self, name: str, initial_vote: int) -> str:
        """Add a new player with initial 1-10 vote"""
        if not 1 <= initial_vote <= 10:
            return f"❌ Vote must be between 1-10, got {initial_vote}"
        
        name = name.strip()
        if name.lower() in [p.lower() for p in self.players.keys()]:
            return f"❌ Player '{name}' already exists"
        
        self.players[name] = Player.from_vote(name, initial_vote)
        return f"✅ Added {name} with initial rating {initial_vote}/10 (ELO: {self.players[name].elo})"

    def remove_player(self, name: str) -> str:
        """Rimuovi un giocatore dal sistema"""
        player = self._find_player(name)
        if not player:
            return f"❌ Giocatore '{name}' non trovato"

        # Trova il nome esatto (case-sensitive) per la rimozione
        actual_name = player.name
        del self.players[actual_name]
        return f"✅ Giocatore '{actual_name}' rimosso"

    def parse_participant_list(self, message: str) -> List[str]:
        """
        Parse participant list from WhatsApp message
        Handles formats like:
        - "John, Mike, Sarah, Tom, ..."
        - "John\nMike\nSarah\n..."
        - "1. John\n2. Mike\n..."
        """
        # Remove numbers and common prefixes
        message = re.sub(r'^\d+[\.\)]\s*', '', message, flags=re.MULTILINE)
        message = re.sub(r'^[-•]\s*', '', message, flags=re.MULTILINE)
        
        # Split by newlines or commas
        if '\n' in message:
            names = [line.strip() for line in message.split('\n')]
        else:
            names = [name.strip() for name in message.split(',')]
        
        # Clean and filter
        names = [name for name in names if name and len(name) > 0]
        return names
    
    def create_teams(self, participant_names: List[str]) -> Tuple[Optional[dict], str]:
        """
        Create balanced teams from participant list
        
        Returns:
            (teams_dict, message) where teams_dict is None if error
        """
        if len(participant_names) != 10:
            return None, f"❌ Need exactly 10 players, got {len(participant_names)}"
        
        # Find players
        participants = []
        missing = []
        
        for name in participant_names:
            player = self._find_player(name)
            if player:
                participants.append(player)
            else:
                missing.append(name)
        
        if missing:
            return None, f"❌ Unknown players: {', '.join(missing)}\nPlease add them first with their ratings."
        
        # Balance teams using snake draft
        participants.sort(key=lambda p: p.elo, reverse=True)
        
        team1 = []
        team2 = []
        
        for i, player in enumerate(participants):
            if i % 4 == 0 or i % 4 == 3:
                team1.append(player)
            else:
                team2.append(player)
        
        team1_avg = sum(p.elo for p in team1) / len(team1)
        team2_avg = sum(p.elo for p in team2) / len(team2)
        
        # Create game ID
        game_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        teams = {
            'game_id': game_id,
            'team1': [p.name for p in team1],
            'team2': [p.name for p in team2],
            'team1_avg_elo': round(team1_avg),
            'team2_avg_elo': round(team2_avg),
            'timestamp': datetime.now().isoformat()
        }
        
        # Store pending game
        self.pending_games[game_id] = teams
        
        # Format message
        message = "⚽ *TEAMS CREATED*\n\n"
        message += f"🔵 *Team 1* (Avg ELO: {round(team1_avg)})\n"
        for p in team1:
            message += f"  • {p.name} ({p.elo})\n"
        message += f"\n🔴 *Team 2* (Avg ELO: {round(team2_avg)})\n"
        for p in team2:
            message += f"  • {p.name} ({p.elo})\n"
        message += f"\n_Game ID: {game_id}_"
        
        return teams, message
    
    def parse_score(self, message: str) -> Optional[Tuple[int, int]]:
        """
        Parse score from message
        Handles: "3-2", "3 2", "team1: 3, team2: 2", etc.
        """
        # Try hyphen format: "3-2"
        match = re.search(r'(\d+)\s*[-:]\s*(\d+)', message)
        if match:
            return int(match.group(1)), int(match.group(2))
        
        # Try space format: "3 2"
        match = re.search(r'(\d+)\s+(\d+)', message)
        if match:
            return int(match.group(1)), int(match.group(2))
        
        return None
    
    def update_ratings(self, game_id: str, team1_score: int, team2_score: int) -> str:
        """
        Update player ratings based on game result using ELO
        
        Args:
            game_id: ID of the game to update
            team1_score: Goals scored by team 1
            team2_score: Goals scored by team 2
        """
        if game_id not in self.pending_games:
            return f"❌ Game {game_id} not found"
        
        game = self.pending_games[game_id]
        
        # Determine outcome
        if team1_score > team2_score:
            team1_result = 1.0
            team2_result = 0.0
            winner = "Team 1"
        elif team2_score > team1_score:
            team1_result = 0.0
            team2_result = 1.0
            winner = "Team 2"
        else:
            team1_result = 0.5
            team2_result = 0.5
            winner = "Draw"
        
        # Get players
        team1_players = [self.players[name] for name in game['team1']]
        team2_players = [self.players[name] for name in game['team2']]
        
        # Calculate average ELOs
        team1_avg_elo = sum(p.elo for p in team1_players) / len(team1_players)
        team2_avg_elo = sum(p.elo for p in team2_players) / len(team2_players)
        
        # Expected scores using ELO formula
        expected1 = 1 / (1 + 10 ** ((team2_avg_elo - team1_avg_elo) / 400))
        expected2 = 1 / (1 + 10 ** ((team1_avg_elo - team2_avg_elo) / 400))
        
        # Goal difference multiplier (bigger wins = bigger rating changes)
        goal_diff = abs(team1_score - team2_score)
        multiplier = 1 + (goal_diff - 1) * 0.1  # +10% per goal difference
        
        # Update ratings
        rating_changes = []
        
        for player in team1_players:
            old_elo = player.elo
            change = self.k_factor * multiplier * (team1_result - expected1)
            player.elo = int(player.elo + change)
            player.games_played += 1
            if team1_result == 1.0:
                player.wins += 1
            elif team1_result == 0.0:
                player.losses += 1
            rating_changes.append(f"  {player.name}: {old_elo} → {player.elo} ({change:+.0f})")
        
        for player in team2_players:
            old_elo = player.elo
            change = self.k_factor * multiplier * (team2_result - expected2)
            player.elo = int(player.elo + change)
            player.games_played += 1
            if team2_result == 1.0:
                player.wins += 1
            elif team2_result == 0.0:
                player.losses += 1
            rating_changes.append(f"  {player.name}: {old_elo} → {player.elo} ({change:+.0f})")
        
        # Remove from pending
        del self.pending_games[game_id]
        
        # Format message
        message = f"📊 *GAME RESULT RECORDED*\n\n"
        message += f"🔵 Team 1: {team1_score}\n"
        message += f"🔴 Team 2: {team2_score}\n"
        message += f"🏆 Winner: {winner}\n\n"
        message += f"*Rating Changes:*\n"
        message += "\n".join(rating_changes)
        
        return message
    
    def get_leaderboard(self, limit: int = 10) -> str:
        """Get top players by ELO"""
        if not self.players:
            return "No players yet!"
        
        sorted_players = sorted(self.players.values(), key=lambda p: p.elo, reverse=True)
        
        message = f"🏆 *TOP {min(limit, len(sorted_players))} PLAYERS*\n\n"
        for i, player in enumerate(sorted_players[:limit], 1):
            win_rate = (player.wins / player.games_played * 100) if player.games_played > 0 else 0
            message += f"{i}. {player.name}\n"
            message += f"   ELO: {player.elo} | Games: {player.games_played} | Win Rate: {win_rate:.1f}%\n"
        
        return message
    
    def get_pending_games(self) -> str:
        """Get list of games waiting for scores"""
        if not self.pending_games:
            return "No pending games"
        
        message = "⏳ *PENDING GAMES*\n\n"
        for game_id, game in self.pending_games.items():
            timestamp = datetime.fromisoformat(game['timestamp'])
            message += f"Game {game_id}\n"
            message += f"Created: {timestamp.strftime('%Y-%m-%d %H:%M')}\n"
            message += f"Team 1: {', '.join(game['team1'][:3])}...\n"
            message += f"Team 2: {', '.join(game['team2'][:3])}...\n\n"
        
        return message
    
    def _find_player(self, name: str) -> Optional[Player]:
        """Find player by name (case-insensitive)"""
        for player_name, player in self.players.items():
            if player_name.lower() == name.lower():
                return player
        return None
    
    def save_to_file(self, filename: str = 'football_data.json'):
        """Save all data to JSON file"""
        data = {
            'players': {name: player.to_dict() for name, player in self.players.items()},
            'pending_games': self.pending_games,
            'k_factor': self.k_factor
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filename: str = 'football_data.json'):
        """Load data from JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.players = {name: Player.from_dict(pdata) 
                          for name, pdata in data['players'].items()}
            self.pending_games = data.get('pending_games', {})
            self.k_factor = data.get('k_factor', 32)
            return True
        except FileNotFoundError:
            return False


# Example usage and testing
if __name__ == "__main__":
    balancer = TeamBalancer()
    
    # Example 1: Adding players with initial votes
    print("=" * 50)
    print("ADDING PLAYERS")
    print("=" * 50)
    players_votes = [
        ("John", 7),
        ("Mike", 8),
        ("Sarah", 6),
        ("Tom", 9),
        ("Emma", 5),
        ("David", 7),
        ("Lisa", 6),
        ("James", 8),
        ("Anna", 5),
        ("Chris", 7)
    ]
    
    for name, vote in players_votes:
        print(balancer.add_player(name, vote))
    
    # Example 2: Creating teams
    print("\n" + "=" * 50)
    print("CREATING TEAMS")
    print("=" * 50)
    participant_message = """
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
"""
    
    names = balancer.parse_participant_list(participant_message)
    teams, message = balancer.create_teams(names)
    print(message)
    
    # Example 3: Recording result
    print("\n" + "=" * 50)
    print("RECORDING RESULT")
    print("=" * 50)
    if teams:
        game_id = teams['game_id']
        score_message = "5-3"  # Team 1 wins 5-3
        team1_score, team2_score = balancer.parse_score(score_message)
        print(balancer.update_ratings(game_id, team1_score, team2_score))
    
    # Example 4: Leaderboard
    print("\n" + "=" * 50)
    print("LEADERBOARD")
    print("=" * 50)
    print(balancer.get_leaderboard())
    
    # Save data
    balancer.save_to_file()
    print("\n✅ Data saved to football_data.json")
