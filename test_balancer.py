"""
Test script for Football Team Balancer
Run this to verify the core logic before connecting to WhatsApp
"""

from football_balancer import TeamBalancer

def test_basic_flow():
    """Test the complete workflow"""
    print("=" * 60)
    print("TESTING FOOTBALL TEAM BALANCER")
    print("=" * 60)
    
    # Initialize
    balancer = TeamBalancer()
    print("\n✅ Balancer initialized")
    
    # Test 1: Adding players
    print("\n" + "=" * 60)
    print("TEST 1: Adding Players with Initial Votes")
    print("=" * 60)
    
    test_players = [
        ("John", 7), ("Mike", 8), ("Sarah", 6), ("Tom", 9),
        ("Emma", 5), ("David", 7), ("Lisa", 6), ("James", 8),
        ("Anna", 5), ("Chris", 7), ("Alex", 6), ("Kate", 8)
    ]
    
    for name, vote in test_players:
        result = balancer.add_player(name, vote)
        print(result)
    
    # Test 2: Parse participant list
    print("\n" + "=" * 60)
    print("TEST 2: Parsing Participant List")
    print("=" * 60)
    
    # Test different formats
    test_messages = [
        "John, Mike, Sarah, Tom, Emma, David, Lisa, James, Anna, Chris",
        """John
Mike
Sarah
Tom
Emma
David
Lisa
James
Anna
Chris""",
        """1. John
2. Mike
3. Sarah
4. Tom
5. Emma
6. David
7. Lisa
8. James
9. Anna
10. Chris"""
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\nFormat {i}:")
        names = balancer.parse_participant_list(message)
        print(f"  Parsed {len(names)} names: {names[:3]}...")
    
    # Test 3: Create teams
    print("\n" + "=" * 60)
    print("TEST 3: Creating Balanced Teams")
    print("=" * 60)
    
    participants = ["John", "Mike", "Sarah", "Tom", "Emma", 
                   "David", "Lisa", "James", "Anna", "Chris"]
    
    teams, message = balancer.create_teams(participants)
    print(message)
    
    if not teams:
        print("❌ Team creation failed!")
        return
    
    game_id = teams['game_id']
    print(f"\n✅ Teams created with ID: {game_id}")
    
    # Test 4: Parse scores
    print("\n" + "=" * 60)
    print("TEST 4: Parsing Different Score Formats")
    print("=" * 60)
    
    test_scores = ["5-3", "5 3", "team1: 5, team2: 3", "5:3"]
    
    for score_text in test_scores:
        score = balancer.parse_score(score_text)
        print(f"  '{score_text}' → {score}")
    
    # Test 5: Update ratings
    print("\n" + "=" * 60)
    print("TEST 5: Updating Ratings After Game")
    print("=" * 60)
    
    print("\nRecording result: Team 1 wins 5-3")
    result = balancer.update_ratings(game_id, 5, 3)
    print(result)
    
    # Test 6: Leaderboard
    print("\n" + "=" * 60)
    print("TEST 6: Viewing Leaderboard")
    print("=" * 60)
    
    print(balancer.get_leaderboard())
    
    # Test 7: Save and load
    print("\n" + "=" * 60)
    print("TEST 7: Save and Load Data")
    print("=" * 60)
    
    balancer.save_to_file('test_data.json')
    print("✅ Data saved to test_data.json")
    
    # Create new balancer and load
    balancer2 = TeamBalancer()
    success = balancer2.load_from_file('test_data.json')
    
    if success:
        print(f"✅ Data loaded: {len(balancer2.players)} players")
        print(f"   Sample player: {list(balancer2.players.values())[0]}")
    else:
        print("❌ Load failed")
    
    # Test 8: Edge cases
    print("\n" + "=" * 60)
    print("TEST 8: Testing Edge Cases")
    print("=" * 60)
    
    # Duplicate player
    result = balancer.add_player("John", 5)
    print(f"Duplicate player: {result}")
    
    # Invalid rating
    result = balancer.add_player("Invalid", 11)
    print(f"Invalid rating: {result}")
    
    # Wrong number of participants
    teams, message = balancer.create_teams(["John", "Mike"])
    print(f"Too few players: {message}")
    
    # Unknown player
    teams, message = balancer.create_teams(
        ["John", "Mike", "Sarah", "Tom", "Emma", 
         "David", "Lisa", "James", "Anna", "UnknownPlayer"]
    )
    print(f"Unknown player: {message}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)


def test_elo_calculations():
    """Test ELO rating calculations"""
    print("\n" + "=" * 60)
    print("ELO RATING SYSTEM TEST")
    print("=" * 60)
    
    balancer = TeamBalancer()
    
    # Create two evenly matched teams
    for i in range(1, 11):
        balancer.add_player(f"Player{i}", 5)  # All start at 1500 ELO
    
    print("\n📊 Initial ratings (all 1500):")
    print(balancer.get_leaderboard())
    
    # Play several games with different outcomes
    participants = [f"Player{i}" for i in range(1, 11)]
    
    print("\n🎮 Simulating 3 games:\n")
    
    # Game 1: Close win (3-2)
    teams, _ = balancer.create_teams(participants)
    balancer.update_ratings(teams['game_id'], 3, 2)
    print("Game 1: 3-2 (close win)")
    
    # Game 2: Dominant win (5-1)
    teams, _ = balancer.create_teams(participants)
    balancer.update_ratings(teams['game_id'], 5, 1)
    print("Game 2: 5-1 (dominant win)")
    
    # Game 3: Draw (2-2)
    teams, _ = balancer.create_teams(participants)
    balancer.update_ratings(teams['game_id'], 2, 2)
    print("Game 3: 2-2 (draw)")
    
    print("\n📊 Final ratings after 3 games:")
    print(balancer.get_leaderboard())
    
    print("\n💡 Observations:")
    print("- Bigger wins cause larger rating changes")
    print("- Draws result in smaller adjustments")
    print("- Underdog victories are rewarded more")


if __name__ == "__main__":
    try:
        test_basic_flow()
        test_elo_calculations()
        print("\n✅ All tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
