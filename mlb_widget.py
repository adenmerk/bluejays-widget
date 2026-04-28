import requests
from datetime import datetime, timezone
import json

TEAM_ID = 141  # Toronto Blue Jays

TEAM_ABBR = {
    141: "tor",  # Blue Jays
    111: "bos",  # Red Sox
    147: "nyy",
    121: "nym",
    119: "lad",
    112: "chc",
    145: "chw",
    114: "cle",
    116: "det",
    118: "kc",
    108: "laa",
    117: "hou",
    133: "oak",
    136: "sea",
    140: "tex",
    109: "ari",
    115: "col",
    135: "sd",
    137: "sf",
    138: "stl",
    146: "mia",
    143: "phi",
    144: "atl",
    120: "was",
    134: "pit",
    113: "cin",
    158: "mil",
    142: "min",
    110: "bal",
    139: "tb"
}

def get_schedule():
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={TEAM_ID}&days=3"
    return requests.get(url).json()

def get_logo(team_id):
    abbr = TEAM_ABBR.get(team_id, "mlb")  # fallback
    return f"https://a.espncdn.com/i/teamlogos/mlb/500/{abbr}.png"

def format_day(game_date):
    game_dt = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    diff = (game_dt.date() - now.date()).days

    if diff == 0:
        day_str = "Today"
    elif diff == 1:
        day_str = "Tomorrow"
    else:
        day_str = game_dt.strftime("%A")

    time_str = game_dt.strftime("%I:%M %p").lstrip("0")

    return f"{day_str} @ {time_str}"

def process_game(game):
    teams = game["teams"]
    status = game["status"]["detailedState"]

    home = teams["home"]
    away = teams["away"]

    home_team = home["team"]["name"]
    away_team = away["team"]["name"]

    home_id = home["team"]["id"]
    away_id = away["team"]["id"]

    is_home = home_team == "Toronto Blue Jays"

    opponent = away_team if is_home else home_team
    opponent_id = away_id if is_home else home_id
    jays_id = 141

    home_away = "vs" if is_home else "@"

    # 🔥 Logo URLs
    opponent_logo = get_logo(opponent_id)
    jays_logo = get_logo(TEAM_ID)

    if status == "Final":
        jays_score = home["score"] if is_home else away["score"]
        opp_score = away["score"] if is_home else home["score"]

        if jays_score > opp_score:
            result_text = f"Jays Win {jays_score}-{opp_score}"
        else:
            result_text = f"Jays Lose {opp_score}-{jays_score}"

        return {
            "opponent": opponent,
            "home_away": home_away,
            "display_time": result_text,
            "status": "final",
            "opponent_logo": opponent_logo,
            "jays_logo": jays_logo
        }

    return {
        "opponent": opponent,
        "home_away": home_away,
        "display_time": format_day(game["gameDate"]),
        "status": "upcoming",
        "opponent_logo": opponent_logo,
        "jays_logo": jays_logo
    }

def main():
    data = get_schedule()

    games = []
    for date in data.get("dates", []):
        for game in date.get("games", []):
            games.append(game)

    if not games:
        print("No games found")
        return

    # Sort games by date (newest first)
    games.sort(key=lambda g: g["gameDate"], reverse=True)

    final_game = None
    next_game = None

    now = datetime.now(timezone.utc)

    for game in games:
        status = game["status"]["detailedState"]
        game_dt = datetime.fromisoformat(game["gameDate"].replace("Z", "+00:00"))

        # Most recent final game
        if status == "Final" and not final_game:
            final_game = game

        # Next upcoming game
        if status in ["Scheduled", "Pre-Game"] and game_dt > now:
            if not next_game:
                next_game = game

    if final_game:
        result = process_game(final_game)
    elif next_game:
        result = process_game(next_game)
    else:
        print("No valid game found")
        return

    print("\n=== FINAL OUTPUT ===")
    print(json.dumps(result, indent=2))

    with open("jays.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
