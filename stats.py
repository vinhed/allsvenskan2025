from tabulate import tabulate
from datetime import datetime
import html
from collections import Counter
import random  # For selecting one person randomly when there are ties

allsvenskan_tip_2025 = {}
html_output = open("index.html", "w", encoding='utf8')
readme = open("README.md", "w", encoding='utf8')

with open('bets', 'r', encoding='utf8') as f:
    bets = {}
    current_user = None
    for line in f:
        line = line.rstrip()
        if line[:2] == '##':
            current_user = line.replace("## ", "")
            bets[current_user] = []
            continue
        if current_user is None:
            continue
        if line == "":
            continue
        if len(line.split(". ")) == 2:
            line = line.split(". ")[1]
        line = line.replace("- ", "")
        bets[current_user].append(line)

for user in bets.keys():
    for i, bet in enumerate(bets[user]):
        if bet not in list(allsvenskan_tip_2025.keys()):
            allsvenskan_tip_2025[bet] = i
        else:
            allsvenskan_tip_2025[bet] += i

# Handle ties in scoring by sorting alphabetically as a tiebreaker
sorted_allsvenskan_tip_2025 = {}
grouped_by_score = {}

# Group teams by their score
for team, score in allsvenskan_tip_2025.items():
    if score not in grouped_by_score:
        grouped_by_score[score] = []
    grouped_by_score[score].append(team)

# Sort scores and within each score group, sort teams alphabetically
for score in sorted(grouped_by_score.keys()):
    for team in sorted(grouped_by_score[score]):
        sorted_allsvenskan_tip_2025[team] = score

# Keep original README generation for compatibility
readme.write("# 🏆 Grabbarnas Allsvenskan 2025 🏆\n\n")
readme.write("## 📊 Current Standings\n`Calculated based on everyones prediction (lower score is better)`\n")
table_data = [(pos+1, team, value) for pos, (team, value) in enumerate(sorted_allsvenskan_tip_2025.items())]

def highlight_top_teams(table_string):
    lines = table_string.split('\n')
    if len(lines) > 3:
        for i in range(len(lines)):
            if "| 1 |" in lines[i]:
                lines[i] = lines[i].replace("| 1 |", "| 1 🥇 |")
            elif "| 2 |" in lines[i]:
                lines[i] = lines[i].replace("| 2 |", "| 2 🥈 |")
            elif "| 3 |" in lines[i]:
                lines[i] = lines[i].replace("| 3 |", "| 3 🥉 |")
    return '\n'.join(lines)

table_result = tabulate(table_data, headers=["#", "Team", "Value"], tablefmt="github")
readme.write(highlight_top_teams(table_result) + "\n\n")
readme.write("## 🔮 Individual Predictions\n")
max_bets = max([len(bets[user]) for user in bets.keys()])
predictions_table = []
for i in range(max_bets):
    row = []
    for user in bets.keys():
        bet = bets[user][i] if i < len(bets[user]) else ""
        row.append(bet)
    predictions_table.append(row)

for i in range(len(predictions_table)):
    predictions_table[i] = [i + 1] + predictions_table[i]

headers = ["#"] + list(bets.keys())
readme.write(tabulate(predictions_table, headers=headers, tablefmt="github") + "\n")

if len(predictions_table) != 16:
    print(f"!!! Warning: Too many teams ({len(predictions_table)}) in table, someone spelled it wrong!!!")

# Helper function to format teams list
def format_team_list(teams_list):
    if len(teams_list) == 1:
        return teams_list[0]
    elif len(teams_list) == 2:
        return f"{teams_list[0]} & {teams_list[1]}"
    else:
        return ", ".join(teams_list[:-1]) + f" & {teams_list[-1]}"

# Calculate additional fun stats with correct relegation format
def calculate_fun_stats(bets, sorted_standings):
    stats = {}
    
    # Flatten all predictions into a single list
    all_predictions = []
    for user, predictions in bets.items():
        all_predictions.extend(predictions)
    
    # Most frequently predicted team for 1st place
    first_place_predictions = [bets[user][0] for user in bets.keys() if len(bets[user]) > 0]
    first_place_counter = Counter(first_place_predictions)
    if first_place_counter:
        # Handle ties for most predicted champion - ALLOW MULTIPLE TEAMS
        champion_count = first_place_counter.most_common(1)[0][1]
        champions = [team for team, count in first_place_counter.items() if count == champion_count]
        # Format with commas and & sign
        stats['most_predicted_champion'] = format_team_list(champions)
        stats['champion_votes'] = f"{champion_count} each" if len(champions) > 1 else champion_count
    
    # Direct relegation (bottom 2 teams)
    direct_relegation_predictions = {}
    for user in bets.keys():
        if len(bets[user]) >= 2:  # Ensure there are enough predictions
            for team in bets[user][-2:]:  # Get bottom 2 teams
                if team not in direct_relegation_predictions:
                    direct_relegation_predictions[team] = 0
                direct_relegation_predictions[team] += 1
    
    if direct_relegation_predictions:
        # Find team most predicted for direct relegation - ALLOW MULTIPLE TEAMS
        relegation_count = max(direct_relegation_predictions.values())
        relegation_teams = [team for team, count in direct_relegation_predictions.items() if count == relegation_count]
        # Format with commas and & sign
        stats['most_predicted_relegation'] = format_team_list(relegation_teams)
        stats['relegation_votes'] = f"{relegation_count} each" if len(relegation_teams) > 1 else relegation_count
    
    # Playoff spot (3rd last position)
    playoff_predictions = {}
    for user in bets.keys():
        if len(bets[user]) >= 3:  # Ensure there are enough predictions
            team = bets[user][-3]  # Third from bottom
            if team not in playoff_predictions:
                playoff_predictions[team] = 0
            playoff_predictions[team] += 1
    
    if playoff_predictions:
        # Find team most predicted for playoff - ONLY ONE TEAM
        playoff_team, playoff_count = max(playoff_predictions.items(), key=lambda x: x[1])
        # Handle ties by selecting one randomly
        playoff_teams = [team for team, count in playoff_predictions.items() if count == playoff_count]
        if len(playoff_teams) > 1:
            stats['most_predicted_playoff'] = random.choice(playoff_teams)
        else:
            stats['most_predicted_playoff'] = playoff_teams[0]
        stats['playoff_votes'] = playoff_count
    
    # Most divisive team (highest standard deviation in predictions)
    team_positions = {}
    for team in sorted_standings.keys():
        team_positions[team] = []
    
    for user in bets.keys():
        for pos, team in enumerate(bets[user]):
            if team in team_positions:
                team_positions[team].append(pos + 1)
    
    # Calculate position variance for each team
    team_variance = {}
    for team, positions in team_positions.items():
        if positions:  # Check if there are any positions
            # Calculate variance if we have at least 2 positions
            if len(positions) >= 2:
                mean = sum(positions) / len(positions)
                variance = sum((pos - mean) ** 2 for pos in positions) / len(positions)
                team_variance[team] = variance
    
    if team_variance:
        most_divisive_variance = max(team_variance.values())
        most_divisive_teams = [team for team, var in team_variance.items() if var == most_divisive_variance]
        if len(most_divisive_teams) > 1:
            stats['most_divisive_team'] = random.choice(most_divisive_teams)
        else:
            stats['most_divisive_team'] = most_divisive_teams[0]
        stats['divisive_variance'] = round(most_divisive_variance, 1)
    
    # Find highest agreement team (team with lowest variance)
    if team_variance:
        most_agreed_variance = min(team_variance.values())
        most_agreed_teams = [team for team, var in team_variance.items() if var == most_agreed_variance]
        if len(most_agreed_teams) > 1:
            stats['most_agreed_team'] = random.choice(most_agreed_teams)
        else:
            stats['most_agreed_team'] = most_agreed_teams[0]
        stats['agreed_variance'] = round(most_agreed_variance, 1)
    
    # Calculate the most optimistic and pessimistic predictors
    user_optimism = {}
    for user in bets.keys():
        # Calculate average predicted position for top 5 teams in consensus ranking
        top_teams = list(sorted_standings.keys())[:5]
        user_predictions = bets[user]
        
        total_pos = 0
        counted_teams = 0
        for team in top_teams:
            if team in user_predictions:
                total_pos += user_predictions.index(team) + 1
                counted_teams += 1
        
        if counted_teams > 0:
            user_optimism[user] = total_pos / counted_teams
    
    if user_optimism:
        # Handle ties for optimistic - ONLY ONE PERSON
        min_optimism = min(user_optimism.values())
        most_optimistic_users = [user for user, opt in user_optimism.items() if opt == min_optimism]
        if len(most_optimistic_users) > 1:
            stats['most_optimistic'] = random.choice(most_optimistic_users)
        else:
            stats['most_optimistic'] = most_optimistic_users[0]
        
        # Handle ties for pessimistic - ONLY ONE PERSON
        max_optimism = max(user_optimism.values())
        most_pessimistic_users = [user for user, opt in user_optimism.items() if opt == max_optimism]
        if len(most_pessimistic_users) > 1:
            stats['most_pessimistic'] = random.choice(most_pessimistic_users)
        else:
            stats['most_pessimistic'] = most_pessimistic_users[0]
    
    # Calculate most unique predictor (most picks different from consensus)
    user_uniqueness = {}
    consensus_order = list(sorted_standings.keys())
    
    for user, user_predictions in bets.items():
        differences = 0
        for i, team in enumerate(user_predictions):
            if i < len(consensus_order):
                consensus_pos = consensus_order.index(team)
                differences += abs(i - consensus_pos)
        
        user_uniqueness[user] = differences
    
    if user_uniqueness:
        # Handle ties for most unique - ONLY ONE PERSON
        max_uniqueness = max(user_uniqueness.values())
        most_unique_users = [user for user, unique in user_uniqueness.items() if unique == max_uniqueness]
        if len(most_unique_users) > 1:
            stats['most_unique'] = random.choice(most_unique_users)
        else:
            stats['most_unique'] = most_unique_users[0]
    
    return stats

fun_stats = calculate_fun_stats(bets, sorted_allsvenskan_tip_2025)

# Generate Dark Mode HTML with updated fun statistics
html_content = '''<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Allsvenskan 2025</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Dark mode color scheme */
        :root {
            --bg-primary: #121212;
            --bg-secondary: #1e1e1e;
            --bg-tertiary: #252525;
            --text-primary: #ffffff;
            --text-secondary: #aaaaaa;
            --accent: #3a86ff;
            --accent2: #4cc9f0;
            --accent3: #7209b7;
            --row-even: #1e1e1e;
            --row-odd: #252525;
            --row-hover: #303030;
            --header-bg: #111111;
            --border-color: #333333;
            --relegation-direct: rgba(74, 38, 35, 1);
            --relegation-playoff: rgba(201, 127, 81, 1);
            --europaleague: rgba(56, 107, 46, 1);
            --conferenceLeague: rgba(61, 87, 56, 1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
        }
        
        body {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
        }
        
        /* Main container */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header styling */
        header {
            background-color: var(--header-bg);
            color: var(--text-primary);
            padding: 40px 0;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .header-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .header-subtitle {
            font-size: 1.2rem;
            font-weight: 300;
            opacity: 0.9;
            color: var(--text-secondary);
        }
        
        /* Section styling */
        .section {
            background-color: var(--bg-secondary);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 5px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
        }
        
        .section-title .icon {
            margin-right: 10px;
            font-size: 1.6rem;
        }
        
        .section-description {
            color: var(--text-secondary);
            margin-bottom: 20px;
            font-size: 1rem;
        }
        
        /* Table container with horizontal scroll */
        .table-wrapper {
            overflow-x: auto;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        /* Table styling */
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        
        /* Table header */
        thead th {
            background-color: var(--header-bg);
            color: var(--text-primary);
            font-weight: 600;
            padding: 12px 15px;
            text-align: left;
            position: sticky;
            top: 0;
            z-index: 10;
            white-space: nowrap;
        }
        
        /* First header - fixed */
        thead th:first-child {
            position: sticky;
            left: 0;
            z-index: 200;
        }
        
        /* Table body - alternating rows for entire rows */
        tbody tr:nth-child(even) {
            background-color: var(--row-even);
        }
        
        tbody tr:nth-child(odd) {
            background-color: var(--row-odd);
        }
        
        tbody tr:hover {
            background-color: var(--row-hover);
        }
        
        /* Table cells */
        td {
            padding: 6px 6px;
            border-bottom: 2px solid var(--border-color);
        }
        
        /* First column - fixed */
        td:first-child {
            font-weight: 600;
            position: sticky;
            left: 0;
            z-index: 5;
            border-right: 2px solid var(--border-color);
        }
        
        /* Ensure first column matches row background */
        tr:nth-child(even) td:first-child {
            background-color: var(--row-even);
        }
        
        tr:nth-child(odd) td:first-child {
            background-color: var(--row-odd);
        }
        
        /* Ensure first column background on hover */
        tr:hover td:first-child {
            background-color: var(--row-hover);
        }
        
        /* Relegation and European qualification highlighting in standings table */
        tr.europaleague td {
            background-color: var(--europaleague);
        }
        
        tr.conference-league td {
            background-color: var(--conferenceLeague);
        }
        
        tr.relegation-direct td {
            background-color: var(--relegation-direct);
        }
        
        tr.relegation-playoff td {
            background-color: var(--relegation-playoff);
        }
        
        /* Make sure the first column keeps the relegation styling on even/odd rows */
        tr.europaleague:nth-child(even) td:first-child,
        tr.europaleague:nth-child(odd) td:first-child {
            background-color: var(--europaleague);
        }
        
        tr.conference-league:nth-child(even) td:first-child,
        tr.conference-league:nth-child(odd) td:first-child {
            background-color: var(--conferenceLeague);
        }
        
        tr.relegation-direct:nth-child(even) td:first-child,
        tr.relegation-direct:nth-child(odd) td:first-child {
            background-color: var(--relegation-direct);
        }
        
        tr.relegation-playoff:nth-child(even) td:first-child,
        tr.relegation-playoff:nth-child(odd) td:first-child {
            background-color: var(--relegation-playoff);
        }
        
        /* Ensure rows keep their styling on hover */
        tr.europaleague:hover td {
            background-color: rgba(39, 61, 29, 1);
        }
        
        tr.europaleague:hover td:first-child {
            background-color: rgba(39, 61, 29, 1);
        }
        
        tr.conference-league:hover td {
            background-color: rgba(63, 79, 60, 1);
        }
        
        tr.conference-league:hover td:first-child {
            background-color: rgba(63, 79, 60, 1);
        }
        
        tr.relegation-direct:hover td {
            background-color: rgba(220, 53, 69, 0.3);
        }
        
        tr.relegation-direct:hover td:first-child {
            background-color: rgba(220, 53, 69, 0.3);
        }
        
        tr.relegation-playoff:hover td {
            background-color: rgba(255, 193, 7, 0.2);
        }
        
        tr.relegation-playoff:hover td:first-child {
            background-color: rgba(255, 193, 7, 0.2);
        }
        
        /* Stats section */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background-color: var(--bg-secondary);
            padding: 25px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            transition: transform 0.2s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 5px;
            min-height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Fun stats section */
        .fun-stats-section {
            background-color: var(--bg-secondary);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        .fun-stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .fun-stat-card {
            background-color: var(--bg-tertiary);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease;
        }
        
        .fun-stat-card:hover {
            transform: translateY(-3px);
        }
        
        .fun-stat-title {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 10px;
            color: var(--text-primary);
        }
        
        .fun-stat-value {
            font-size: 1.6rem;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .fun-stat-description {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        
        /* Color variations for fun stats */
        .fun-stat-card:nth-child(1) .fun-stat-value {
            color: var(--accent);
        }
        
        .fun-stat-card:nth-child(2) .fun-stat-value {
            color: var(--accent2);
        }
        
        .fun-stat-card:nth-child(3) .fun-stat-value {
            color: var(--accent3);
        }
        
        .fun-stat-card:nth-child(4) .fun-stat-value {
            color: #f72585;
        }
        
        .fun-stat-card:nth-child(5) .fun-stat-value {
            color: #4361ee;
        }
        
        .fun-stat-card:nth-child(6) .fun-stat-value {
            color: #4cc9f0;
        }
        
        .fun-stat-card:nth-child(7) .fun-stat-value {
            color: #f77f00;
        }
        
        .fun-stat-card:nth-child(8) .fun-stat-value {
            color: #7209b7;
        }
        
        /* Legend for relegation zones and European qualifications */
        .legend {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            font-size: 0.85rem;
        }
        
        .legend-color {
            width: 15px;
            height: 15px;
            margin-right: 8px;
            border-radius: 3px;
        }
        
        .legend-europaleague {
            background-color: var(--europaleague);
        }
        
        .legend-conference {
            background-color: var(--conferenceLeague);
        }
        
        .legend-direct {
            background-color: var(--relegation-direct);
        }
        
        .legend-playoff {
            background-color: var(--relegation-playoff);
        }
        
        /* Footer */
        footer {
            text-align: center;
            padding: 20px;
            margin-top: 30px;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .header-title {
                font-size: 2rem;
            }
            
            .section {
                padding: 20px;
            }
            
            .stats-grid, .fun-stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1 class="header-title">🏆 Grabbarnas Allsvenskan 2025 🏆</h1>
            <div class="header-subtitle">Prediction Football</div>
        </div>
    </header>
    
    <div class="container">
        <!-- Stats Cards -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">''' + str(len(bets.keys())) + '''</div>
                <div class="stat-label">Participants</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(len(allsvenskan_tip_2025.keys())) + '''</div>
                <div class="stat-label">Teams</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(list(sorted_allsvenskan_tip_2025.keys())[0]) + '''</div>
                <div class="stat-label">Current Favorite</div>
            </div>
        </div>
        
        <!-- Fun Stats Section -->
        <section class="fun-stats-section">
            <h2 class="section-title"><span class="icon">🎮</span> Statistics</h2>
            <p class="section-description">Interesting insights from everyone's predictions</p>
            
            <div class="fun-stats-grid">
'''

# Add fun stats cards
if 'most_predicted_champion' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">People's Champion</div>
                    <div class="fun-stat-value">{html.escape(str(fun_stats['most_predicted_champion']))}</div>
                    <div class="fun-stat-description">Most frequently predicted to win with {fun_stats['champion_votes']} votes</div>
                </div>
    '''

if 'most_predicted_relegation' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">Direct Relegation Favorite</div>
                    <div class="fun-stat-value">{html.escape(str(fun_stats['most_predicted_relegation']))}</div>
                    <div class="fun-stat-description">Most frequently predicted for direct relegation (bottom 2) with {fun_stats['relegation_votes']} votes</div>
                </div>
    '''

if 'most_predicted_playoff' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">Playoff Candidate</div>
                    <div class="fun-stat-value">{html.escape(str(fun_stats['most_predicted_playoff']))}</div>
                    <div class="fun-stat-description">Most frequently predicted for relegation playoff (14th place) with {fun_stats['playoff_votes']} votes</div>
                </div>
    '''

if 'most_divisive_team' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">Most Divisive Team</div>
                    <div class="fun-stat-value">{html.escape(str(fun_stats['most_divisive_team']))}</div>
                    <div class="fun-stat-description">Highest variance in predicted positions (variance: {fun_stats['divisive_variance']})</div>
                </div>
    '''

if 'most_agreed_team' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">Most Agreed Upon Team</div>
                    <div class="fun-stat-value">{html.escape(str(fun_stats['most_agreed_team']))}</div>
                    <div class="fun-stat-description">Lowest variance in predicted positions (variance: {fun_stats['agreed_variance']})</div>
                </div>
    '''

if 'most_optimistic' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">The Optimist</div>
                    <div class="fun-stat-value">{html.escape(str(fun_stats['most_optimistic']))}</div>
                    <div class="fun-stat-description">Ranks top teams higher than others</div>
                </div>
    '''

if 'most_pessimistic' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">The Pessimist</div>
                    <div class="fun-stat-value">{html.escape(str(fun_stats['most_pessimistic']))}</div>
                    <div class="fun-stat-description">Ranks top teams lower than others</div>
                </div>
    '''

if 'most_unique' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">The Maverick</div>
                    <div class="fun-stat-value">{html.escape(str(fun_stats['most_unique']))}</div>
                    <div class="fun-stat-description">Most predictions different from the consensus</div>
                </div>
    '''

html_content += '''
            </div>
        </section>
        
        <!-- Current Standings Section -->
        <section class="section">
            <h2 class="section-title"><span class="icon">📊</span> Current Standings</h2>
            <p class="section-description">Calculated based on everyone's predictions. Lower score indicates higher collective ranking.</p>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color legend-europaleague"></div>
                    <span>Europa League (1st Place)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-conference"></div>
                    <span>Conference League (2nd-3rd Place)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-direct"></div>
                    <span>Direct Relegation (Bottom 2)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color legend-playoff"></div>
                    <span>Relegation Playoff (14th Place)</span>
                </div>
            </div>
            
            <div class="table-wrapper">
                <table id="standings-table">
                    <thead>
                        <tr>
                            <th>Position</th>
                            <th>Team</th>
                            <th>Score</th>
                        </tr>
                    </thead>
                    <tbody>
'''

# Add standings table rows with relegation highlighting and European qualification
team_count = len(sorted_allsvenskan_tip_2025)
for pos, (team, value) in enumerate(sorted_allsvenskan_tip_2025.items()):
    position_display = f"{pos+1}"
    row_class = ""
    
    # Add medals to top 3
    if pos == 0:
        row_class = "europaleague"  # 1st place - Europa League
    elif pos == 1 or pos == 2:
        row_class = "conference-league"  # 2nd and 3rd place - Conference League
    # Add relegation classes
    elif pos >= team_count - 2:  # Bottom 2 teams (direct relegation)
        row_class = "relegation-direct"
    elif pos == team_count - 3:  # 3rd from bottom (playoff)
        row_class = "relegation-playoff"
    
    html_content += f'''
                        <tr class="{row_class}">
                            <td>{position_display}</td>
                            <td>{html.escape(team)}</td>
                            <td>{value}</td>
                        </tr>'''

html_content += '''
                    </tbody>
                </table>
            </div>
        </section>
        
        <!-- Individual Predictions Section -->
        <section class="section">
            <h2 class="section-title"><span class="icon">🔮</span> Individual Predictions</h2>
            <p class="section-description">Each column represents a participant's predicted final table positions.</p>
            
            <div class="table-wrapper">
                <table id="predictions-table">
                    <thead>
                        <tr>
                            <th>Pos</th>
'''

# Add user headers
for user in bets.keys():
    html_content += f'                            <th>{html.escape(user)}</th>\n'

html_content += '''                        </tr>
                    </thead>
                    <tbody>
'''

# Add prediction rows with relegation highlighting and European qualification
for i in range(max_bets):
    row_class = ""
    
    # Highlight European qualification and relegation positions in the position column
    if i == 0:  # Top position (Europa League)
        row_class = "europaleague"
    elif i == 1 or i == 2:  # 2nd and 3rd position (Conference League)
        row_class = "conference-league"
    elif i >= max_bets - 2:  # Bottom 2 positions (direct relegation)
        row_class = "relegation-direct"
    elif i == max_bets - 3:  # 3rd from bottom position (playoff)
        row_class = "relegation-playoff"
    
    html_content += f'                        <tr class="{row_class}">\n'
    html_content += f'                            <td>{i+1}</td>\n'
    
    for user in bets.keys():
        bet = bets[user][i] if i < len(bets[user]) else ""
        html_content += f'                            <td>{html.escape(bet)}</td>\n'
    
    html_content += f'                        </tr>\n'

html_content += '''                    </tbody>
                </table>
            </div>
        </section>
    </div>
    
    <footer>
        <div>Updated on ''' + datetime.now().strftime("%B %d, %Y at %H:%M") + '''</div>
        <div>Allsvenskan 2025 Prediction League</div>
    </footer>
</body>
</html>'''

html_output.write(html_content)
html_output.close()
readme.close()

print("✓ Successfully generated files with improved relegation statistics and European qualification!")
print("  - index.html: Dark mode design with proper relegation highlighting and European qualification")
print("  - README.md: Original GitHub format preserved")
print("  - Ties in standings are now sorted alphabetically")
print("  - Fun stats now only show one person for individual stats")
print("  - Only People's Champion and Direct Relegation Favorite can have multiple teams")