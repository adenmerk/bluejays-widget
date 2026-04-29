import requests, json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

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

def get_live_data(game_pk):
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
    return requests.get(url).json()

def format_day(game_date):
    # Parse as UTC
    game_dt_utc = datetime.fromisoformat(game_date.replace("Z", "+00:00"))

    # Convert to your local timezone (Regina)
    local_tz = ZoneInfo("America/Regina")
    game_dt_local = game_dt_utc.astimezone(local_tz)

    now = datetime.now(local_tz)

    diff = (game_dt_local.date() - now.date()).days

    if diff == 0:
        day_str = "Today"
    elif diff == 1:
        day_str = "Tomorrow"
    else:
        day_str = game_dt_local.strftime("%A")

    time_str = game_dt_local.strftime("%I:%M %p").lstrip("0")

    return f"{day_str} @ {time_str}"

def format_live_game(game):
    game_pk = game["gamePk"]
    live_data = get_live_data(game_pk)

    linescore = live_data.get("liveData", {}).get("linescore", {})

    inning = linescore.get("currentInning", "?")
    is_top = linescore.get("isTopInning", True)

    inning_half = "Top" if is_top else "Bot"

    teams = game["teams"]

    home = teams["home"]
    away = teams["away"]

    home_name = home["team"]["name"]
    away_name = away["team"]["name"]

    home_score = home.get("score", 0)
    away_score = away.get("score", 0)

    is_home = home_name == "Toronto Blue Jays"

    if is_home:
        jays_score = home_score
        opp_score = away_score
        opp_abbr = TEAM_ABBR.get(away["team"]["id"], "OPP").upper()
    else:
        jays_score = away_score
        opp_score = home_score
        opp_abbr = TEAM_ABBR.get(home["team"]["id"], "OPP").upper()

    return f"{inning_half} {inning} • TOR {jays_score}-{opp_score} {opp_abbr}"

def process_game(game):
    teams = game["teams"]
    status = game["status"]["abstractGameState"]

    home = teams["home"]
    away = teams["away"]

    home_team = home["team"]["name"]
    away_team = away["team"]["name"]

    home_id = home["team"]["id"]
    away_id = away["team"]["id"]

    is_home = home_team == "Toronto Blue Jays"

    opponent = away_team if is_home else home_team
    opponent_id = away_id if is_home else home_id

    home_away = "vs" if is_home else "@"

    # Logos
    opponent_logo = get_logo(opponent_id)
    jays_logo = get_logo(TEAM_ID)

    # =========================
    # 🔴 LIVE GAME
    # =========================
    if status == "Live":
        try:
            live_data = get_live_data(game["gamePk"])
            linescore = live_data.get("liveData", {}).get("linescore", {})

            inning = linescore.get("currentInning", "?")
            is_top = linescore.get("isTopInning", True)
            inning_half = "Top" if is_top else "Bot"

            home_score = home.get("score", 0)
            away_score = away.get("score", 0)

            if is_home:
                jays_score = home_score
                opp_score = away_score
                opp_abbr = TEAM_ABBR.get(away_id, "OPP").upper()
            else:
                jays_score = away_score
                opp_score = home_score
                opp_abbr = TEAM_ABBR.get(home_id, "OPP").upper()

            display_time = f"{inning_half} {inning} - TOR {jays_score}-{opp_score} {opp_abbr}"

        except:
            # fallback if API fails
            display_time = "Live • Updating"

        return {
            "opponent": opponent,
            "home_away": home_away,
            "display_time": display_time,
            "status": "live",
            "opponent_logo": opponent_logo,
            "jays_logo": jays_logo
        }

    # =========================
    # ✅ FINAL GAME
    # =========================
    if status == "Final":
        home_score = home.get("score", 0)
        away_score = away.get("score", 0)

        if is_home:
            jays_score = home_score
            opp_score = away_score
        else:
            jays_score = away_score
            opp_score = home_score

        if jays_score > opp_score:
            display_time = f"Jays win {jays_score}-{opp_score}"
        else:
            display_time = f"Jays lose {opp_score}-{jays_score}"

        return {
            "opponent": opponent,
            "home_away": home_away,
            "display_time": display_time,
            "status": "final",
            "opponent_logo": opponent_logo,
            "jays_logo": jays_logo
        }

    # =========================
    # 📅 UPCOMING GAME
    # =========================
    display_time = format_day(game["gameDate"])

    return {
        "opponent": opponent,
        "home_away": home_away,
        "display_time": display_time,
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

    # Sort by game time (newest first)
    games.sort(key=lambda g: g["gameDate"], reverse=True)

    live_game = None
    final_game = None
    next_game = None

    now = datetime.now(timezone.utc)

    for game in games:
        status = game["status"]["abstractGameState"]
        game_dt = datetime.fromisoformat(game["gameDate"].replace("Z", "+00:00"))

        # 🔴 PRIORITY 1: LIVE GAME
        if status == "Live":
            live_game = game
            break  # nothing beats live

        # ✅ PRIORITY 2: MOST RECENT FINAL
        if status == "Final" and not final_game:
            final_game = game

        # 📅 PRIORITY 3: NEXT UPCOMING
        if status in ["Preview", "Scheduled"] and game_dt > now:
            if not next_game:
                next_game = game

    if live_game:
        result = process_game(live_game)
    elif final_game:
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
