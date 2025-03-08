from tabulate import tabulate
from datetime import datetime
import html
from collections import Counter
import random
import sys
import json
from modules.allsvenskan_scraper import get_allsvenskan_standings, generate_live_standings_html, get_full_data
from html import escape

# Main script starts here
allsvenskan_tip_2025 = {}
html_output = open("index.html", "w", encoding='utf8')
readme = open("README.md", "w", encoding='utf8')

print("Loading bets and calculating consensus rankings...")
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

# Generate README content (unchanged from original)
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

def create_manual_team_mapping():
    """Create a manual mapping for teams that might be difficult to match automatically"""
    mapping = {
        # Your prediction team name: API team name
        "Malmö": "Malmö FF",
        "Malmö FF": "Malmö FF",
        "MFF": "Malmö FF",
        "AIK": "AIK",
        "Djurgården": "Djurgården",
        "DIF": "Djurgården",
        "Hammarby": "Hammarby",
        "Bajen": "Hammarby",
        "IFK Göteborg": "IFK Göteborg",
        "Göteborg": "IFK Göteborg",
        "Blåvitt": "IFK Göteborg",
        "Häcken": "BK Häcken",
        "BK Häcken": "BK Häcken",
        "Elfsborg": "IF Elfsborg",
        "IF Elfsborg": "IF Elfsborg",
        "IFK Norrköping": "IFK Norrköping",
        "Peking": "IFK Norrköping",
        "Värnamo": "IFK Värnamo",
        "IFK Värnamo": "IFK Värnamo",
        "Sirius": "IK Sirius",
        "IK Sirius": "IK Sirius",
        "Mjällby": "Mjällby AIF",
        "Mjällby AIF": "Mjällby AIF",
        "MAIF": "Mjällby AIF",
        "BP": "BP",
        "Brommapojkarna": "BP",
        "Degerfors": "Degerfors IF",
        "Degerfors IF": "Degerfors IF",
        "Halmstad": "Halmstads BK",
        "Halmstads BK": "Halmstads BK",
        "HBK": "Halmstads BK",
        "GAIS": "GAIS",
        "Gais": "GAIS",
        "Öster": "Östers IF",
        "Östers IF": "Östers IF",
        "Östers": "Östers IF"
    }
    return mapping

def enhanced_get_team_logos(api_data, prediction_teams):
    """
    Get team logos using both automatic matching and manual mapping
    
    Args:
        api_data: The API data containing team information
        prediction_teams: List of team names from predictions
        
    Returns:
        Dictionary mapping prediction team names to logo URLs
    """
    team_logos = {}
    api_teams = []
    
    try:
        # First collect all teams from API
        for key, team_info in api_data.items():
            # Skip non-team entries
            if key == 'undefined' or not key.isdigit():
                continue
                
            team_name = team_info.get('displayName', '')
            logo_url = team_info.get('logoImageUrl', '')
            
            if team_name and logo_url:
                api_teams.append({
                    'name': team_name,
                    'abbreviation': team_info.get('abbrv', ''),
                    'full_name': team_info.get('name', ''),
                    'logo_url': logo_url
                })
        
        # Create manual mapping
        manual_mapping = create_manual_team_mapping()
        
        # Go through API data and build a mapping from API team names to logo URLs
        api_name_to_logo = {}
        for api_team in api_teams:
            api_name_to_logo[api_team['name']] = api_team['logo_url']
        
        # For each team in predictions, try to match with API teams
        for team in prediction_teams:
            matched = False
            team_lower = team.lower().strip()
            
            # 1. Try direct match with manual mapping
            if team in manual_mapping:
                api_name = manual_mapping[team]
                for api_team in api_teams:
                    if api_name.lower() == api_team['name'].lower():
                        team_logos[team] = api_team['logo_url']
                        matched = True
                        print(f"✓ Manually matched '{team}' to '{api_team['name']}'")
                        break
            
            # 2. Try exact match (case insensitive)
            if not matched:
                for api_team in api_teams:
                    if team_lower == api_team['name'].lower().strip():
                        team_logos[team] = api_team['logo_url']
                        matched = True
                        print(f"✓ Exact match: '{team}' to '{api_team['name']}'")
                        break
            
            # 3. Try substring match
            if not matched:
                for api_team in api_teams:
                    # Our team name is in API team name
                    if team_lower in api_team['name'].lower() or team_lower in api_team['full_name'].lower():
                        team_logos[team] = api_team['logo_url']
                        matched = True
                        print(f"✓ Substring match: '{team}' in '{api_team['name']}'")
                        break
                    # API team name is in our team name
                    elif api_team['name'].lower() in team_lower or api_team['abbreviation'].lower() == team_lower:
                        team_logos[team] = api_team['logo_url']
                        matched = True
                        print(f"✓ Abbreviation match: '{team}' contains '{api_team['name']}'")
                        break
            
            if not matched:
                print(f"! Could not find logo for team '{team}'")
        
        return team_logos
    except Exception as e:
        print(f"Error extracting team logos: {e}")
        return {}

def debug_api_teams(api_data):
    """
    Display all teams available in the API data for debugging
    """
    print("\nDEBUG: All teams available in API data:")
    print("="*50)
    
    teams = []
    
    for key, team_info in api_data.items():
        if key == 'undefined' or not key.isdigit():
            continue
            
        display_name = team_info.get('displayName', 'N/A')
        abbrv = team_info.get('abbrv', 'N/A')
        full_name = team_info.get('name', 'N/A')
        logo_url = team_info.get('logoImageUrl', 'N/A')
        
        teams.append({
            'display_name': display_name,
            'abbrv': abbrv,
            'full_name': full_name,
            'has_logo': bool(logo_url)
        })
    
    # Sort teams by display name
    teams.sort(key=lambda x: x['display_name'])
    
    # Print formatted team info
    print(f"{'Display Name':<20} {'Abbrev.':<10} {'Full Name':<30} {'Has Logo'}")
    print("-"*70)
    
    for team in teams:
        print(f"{team['display_name']:<20} {team['abbrv']:<10} {team['full_name']:<30} {'✓' if team['has_logo'] else '✗'}")
    
    print("="*50)

def generate_enhanced_standings_table(sorted_allsvenskan_tip_2025, bets, team_logos):
    """
    Generate HTML for an enhanced consensus standings table with additional statistics
    """
    # Calculate additional statistics for each team
    team_stats = {}
    
    for team in sorted_allsvenskan_tip_2025.keys():
        positions = []
        
        # Collect all positions where this team was placed
        for user, predictions in bets.items():
            if team in predictions:
                pos = predictions.index(team) + 1  # Convert to 1-based position
                positions.append(pos)
        
        # Calculate statistics if we have positions
        if positions:
            avg_pos = sum(positions) / len(positions)
            highest_pos = min(positions)  # Lowest number = highest position
            lowest_pos = max(positions)   # Highest number = lowest position
            median_pos = sorted(positions)[len(positions) // 2] if len(positions) % 2 != 0 else (
                sorted(positions)[len(positions) // 2 - 1] + sorted(positions)[len(positions) // 2]
            ) / 2
            
            # Calculate how many users predicted this team for each position group
            top3 = sum(1 for p in positions if p <= 3)
            top3_pct = (top3 / len(positions)) * 100
            
            europa = sum(1 for p in positions if p == 1)
            europa_pct = (europa / len(positions)) * 100
            
            conference = sum(1 for p in positions if p in [2, 3])
            conference_pct = (conference / len(positions)) * 100
            
            relegation = sum(1 for p in positions if p >= len(sorted_allsvenskan_tip_2025) - 2)
            relegation_pct = (relegation / len(positions)) * 100
            
            team_stats[team] = {
                'consensus_pos': list(sorted_allsvenskan_tip_2025.keys()).index(team) + 1,
                'avg_pos': avg_pos,
                'highest_pos': highest_pos,
                'lowest_pos': lowest_pos,
                'median_pos': median_pos,
                'top3_pct': top3_pct,
                'europa_pct': europa_pct,
                'conference_pct': conference_pct,
                'relegation_pct': relegation_pct,
                'predictions_count': len(positions),
                'value': sorted_allsvenskan_tip_2025[team]
            }
    
    # Start generating the HTML
    html = '''
    <section class="section">
        <h2 class="section-title"><span class="icon">📊</span> Consensus Rankings & Team Statistics</h2>
        <p class="section-description">Comprehensive analysis of each team's predictions across all participants.</p>
        
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
                        <th>Consensus Rank</th>
                        <th>Team</th>
                        <th>Avg. Position</th>
                        <th>Highest Rank</th>
                        <th>Lowest Rank</th>
                        <th>Top 3</th>
                        <th>Relegation</th>
                    </tr>
                </thead>
                <tbody>
    '''
    
    team_count = len(sorted_allsvenskan_tip_2025)
    
    for pos, (team, value) in enumerate(sorted_allsvenskan_tip_2025.items()):
        if team not in team_stats:
            continue
            
        stats = team_stats[team]
        row_class = ""
        
        # Add classes for relegation and European qualification
        if pos == 0:
            row_class = "europaleague"
        elif pos == 1 or pos == 2:
            row_class = "conference-league"
        elif pos >= team_count - 2:
            row_class = "relegation-direct"
        elif pos == team_count - 3:
            row_class = "relegation-playoff"
        
        # Get team logo if available
        logo_url = team_logos.get(team, '')
        logo_html = f'<img src="{logo_url}" alt="{team} logo" class="team-logo" onerror="this.style.display=\'none\'">' if logo_url else ''
        
        # Format the stats
        avg_pos = f"{stats['avg_pos']:.1f}"
        top3_pct = f"{stats['top3_pct']:.0f}%"
        relegation_pct = f"{stats['relegation_pct']:.0f}%"
        
        # Generate a mini bar chart for top3 percentage
        top3_bar = f'''
            <div class="mini-bar-container">
                <div class="mini-bar top3-bar" style="width: {stats['top3_pct']}%"></div>
                <span class="mini-bar-text">{top3_pct}</span>
            </div>
        '''
        
        # Generate a mini bar chart for relegation percentage
        relegation_bar = f'''
            <div class="mini-bar-container">
                <div class="mini-bar relegation-bar" style="width: {stats['relegation_pct']}%"></div>
                <span class="mini-bar-text">{relegation_pct}</span>
            </div>
        '''
        
        html += f'''
            <tr class="{row_class}">
                <td>{pos+1}</td>
                <td>
                    <div class="team-name-with-logo">
                        {logo_html}
                        <span>{escape(team)}</span>
                    </div>
                </td>
                <td>{avg_pos}</td>
                <td>{stats['highest_pos']}</td>
                <td>{stats['lowest_pos']}</td>
                <td>{top3_bar}</td>
                <td>{relegation_bar}</td>
            </tr>
        '''
    
    html += '''
                </tbody>
            </table>
        </div>
    </section>
    '''
    
    return html

def get_api_data():
    """
    Try to get the API data from various sources
    """
    try:
        try:
            return get_full_data()
        except Exception as e:
            print(f"Note: Could not get data from scraper: {e}")
        
        return {}
    except Exception as e:
        print(f"Error getting API data: {e}")
        return {}

# This code should be inserted after you set up the current_standings variable
# And right before you generate the HTML

# Get API data and extract team logos
print("Getting team logos from API data...")
api_data = get_api_data()
team_logos = enhanced_get_team_logos(api_data, sorted_allsvenskan_tip_2025.keys())

if team_logos:
    print(f"✓ Successfully extracted logos for {len(team_logos)} teams")
else:
    print("! Could not extract team logos")

# Then, when you're generating the standings table in your HTML generation code,
# replace the existing standings table with this:

# Inside your html_content generation, replace the standings table section with:
standings_table_html = '''
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

# Add standings table rows with logos, relegation highlighting and European qualification
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
    
    # Get logo if available
    logo_url = '' #team_logos.get(team, '')
    logo_html = f'<img src="{logo_url}" alt="{team} logo" class="team-logo" onerror="this.style.display=\'none\'">' if logo_url else ''
    
    # Calculate normalized score (inverted from the value)
    normalized_score = (16 * len(bets)) - value
    
    standings_table_html += f'''
                        <tr class="{row_class}">
                            <td>{position_display}</td>
                            <td>
                                <div class="team-name-with-logo">
                                    {logo_html}
                                    <span>{escape(team)}</span>
                                </div>
                            </td>
                            <td>{normalized_score}</td>
                        </tr>'''

standings_table_html += '''
                    </tbody>
                </table>
            </div>
'''

# Then replace your existing predictions table with this:
predictions_table_html = '''
            <div class="table-wrapper">
                <table id="predictions-table">
                    <thead>
                        <tr>
                            <th>Pos</th>
'''

# Add user headers
for user in bets.keys():
    predictions_table_html += f'                            <th>{escape(user)}</th>\n'

predictions_table_html += '''                        </tr>
                    </thead>
                    <tbody>
'''

# Add prediction rows with logos, relegation highlighting and European qualification
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
    
    predictions_table_html += f'                        <tr class="{row_class}">\n'
    predictions_table_html += f'                            <td>{i+1}</td>\n'
    
    for user in bets.keys():
        bet = bets[user][i] if i < len(bets[user]) else ""
        
        # Get logo if available and bet is not empty
        cell_content = ""
        if bet:
            logo_html = ""
            if bet in team_logos:
                logo_url = team_logos[bet]
                logo_html = f'<img src="{logo_url}" alt="{bet} logo" class="team-logo" onerror="this.style.display=\'none\'">'
            
            cell_content = f'''
                <div class="team-name-with-logo">
                    {logo_html}
                    <span>{escape(bet)}</span>
                </div>
            '''
        
        predictions_table_html += f'                            <td>{cell_content}</td>\n'
    
    predictions_table_html += f'                        </tr>\n'

predictions_table_html += '''                    </tbody>
                </table>
            </div>
'''

# Helper function to format teams list
def format_team_list(teams_list):
    if len(teams_list) == 1:
        return teams_list[0]
    elif len(teams_list) == 2:
        return f"{teams_list[0]} & {teams_list[1]}"
    else:
        return ", ".join(teams_list[:-1]) + f" & {teams_list[-1]}"

# Calculate additional fun stats
def calculate_fun_stats(bets, sorted_standings):
    # [The original fun_stats calculation function - unchanged]
    # ... [code remains unchanged] ...
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
    
    team_positions = {}
    for team in sorted_standings.keys():
        team_positions[team] = []
    
    for user in bets.keys():
        for pos, team in enumerate(bets[user]):
            if team in team_positions:
                team_positions[team].append(pos + 1)
    
    # Calculate the average position for each team
    team_avg_pos = {}
    for team, positions in team_positions.items():
        if positions:
            team_avg_pos[team] = sum(positions) / len(positions)
    
    # Calculate the difference between consensus ranking and average predicted ranking
    dark_horse_potential = {}
    for i, team in enumerate(sorted_standings.keys()):
        consensus_pos = i + 1  # Position in consensus ranking (1-based)
        if team in team_avg_pos:
            # Positive means team is ranked better in consensus than average predictions
            # Negative means team is predicted better than consensus (dark horse)
            dark_horse_potential[team] = consensus_pos - team_avg_pos[team]
    
    # Find the biggest dark horse (most negative value)
    if dark_horse_potential:
        biggest_dark_horse_value = min(dark_horse_potential.values())  # Most negative value
        biggest_dark_horses = [team for team, val in dark_horse_potential.items() if val == biggest_dark_horse_value]
        if biggest_dark_horses:
            if len(biggest_dark_horses) > 1:
                stats['biggest_dark_horse'] = random.choice(biggest_dark_horses)
            else:
                stats['biggest_dark_horse'] = biggest_dark_horses[0]
            stats['dark_horse_value'] = round(abs(biggest_dark_horse_value), 1)  # Show as positive positions
    
    # 2. The "Underrated" Team (most commonly placed worse than consensus)
    if dark_horse_potential:
        most_underrated_value = max(dark_horse_potential.values())  # Most positive value
        most_underrated_teams = [team for team, val in dark_horse_potential.items() if val == most_underrated_value]
        if most_underrated_teams:
            if len(most_underrated_teams) > 1:
                stats['most_underrated'] = random.choice(most_underrated_teams)
            else:
                stats['most_underrated'] = most_underrated_teams[0]
            stats['underrated_value'] = round(most_underrated_value, 1)
    
    # 3. "The Prophet" - user whose predictions align most closely with consensus
    user_alignment = {}
    consensus_order = list(sorted_standings.keys())
    
    for user, user_predictions in bets.items():
        total_position_diff = 0
        count = 0
        for i, team in enumerate(user_predictions):
            if team in consensus_order:
                consensus_pos = consensus_order.index(team)
                total_position_diff += abs(i - consensus_pos)
                count += 1
        
        if count > 0:
            user_alignment[user] = total_position_diff / count
    
    if user_alignment:
        # Lowest difference = closest to consensus
        min_difference = min(user_alignment.values())
        closest_users = [user for user, diff in user_alignment.items() if diff == min_difference]
        if closest_users:
            if len(closest_users) > 1:
                stats['prophet'] = random.choice(closest_users)
            else:
                stats['prophet'] = closest_users[0]
            stats['prophet_score'] = round(min_difference, 1)
    
    return stats

def generate_enhanced_standings_table(sorted_allsvenskan_tip_2025, bets, team_logos):
    """
    Generate HTML for an enhanced consensus standings table with additional statistics
    """
    # Calculate additional statistics for each team
    team_stats = {}
    
    for team in sorted_allsvenskan_tip_2025.keys():
        positions = []
        
        # Collect all positions where this team was placed
        for user, predictions in bets.items():
            if team in predictions:
                pos = predictions.index(team) + 1  # Convert to 1-based position
                positions.append(pos)
        
        # Calculate statistics if we have positions
        if positions:
            avg_pos = sum(positions) / len(positions)
            highest_pos = min(positions)  # Lowest number = highest position
            lowest_pos = max(positions)   # Highest number = lowest position
            median_pos = sorted(positions)[len(positions) // 2] if len(positions) % 2 != 0 else (
                sorted(positions)[len(positions) // 2 - 1] + sorted(positions)[len(positions) // 2]
            ) / 2
            
            # Calculate how many users predicted this team for each position group
            top3 = sum(1 for p in positions if p <= 3)
            top3_pct = (top3 / len(positions)) * 100
            
            europa = sum(1 for p in positions if p == 1)
            europa_pct = (europa / len(positions)) * 100
            
            conference = sum(1 for p in positions if p in [2, 3])
            conference_pct = (conference / len(positions)) * 100
            
            relegation = sum(1 for p in positions if p >= len(sorted_allsvenskan_tip_2025) - 2)
            relegation_pct = (relegation / len(positions)) * 100
            
            team_stats[team] = {
                'consensus_pos': list(sorted_allsvenskan_tip_2025.keys()).index(team) + 1,
                'avg_pos': avg_pos,
                'highest_pos': highest_pos,
                'lowest_pos': lowest_pos,
                'median_pos': median_pos,
                'top3_pct': top3_pct,
                'europa_pct': europa_pct,
                'conference_pct': conference_pct,
                'relegation_pct': relegation_pct,
                'predictions_count': len(positions),
                'value': sorted_allsvenskan_tip_2025[team]
            }
    
    # Start generating the HTML
    html = '''
    <section class="section">
        <h2 class="section-title"><span class="icon">📊</span> Consensus Rankings & Team Statistics</h2>
        <p class="section-description">Comprehensive analysis of each team's predictions across all participants.</p>
        
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
                        <th>Consensus Rank</th>
                        <th>Team</th>
                        <th>Avg. Position</th>
                        <th>Highest Rank</th>
                        <th>Lowest Rank</th>
                        <th>Top 3 %</th>
                        <th>Relegation %</th>
                    </tr>
                </thead>
                <tbody>
    '''
    
    team_count = len(sorted_allsvenskan_tip_2025)
    
    for pos, (team, value) in enumerate(sorted_allsvenskan_tip_2025.items()):
        if team not in team_stats:
            continue
            
        stats = team_stats[team]
        row_class = ""
        
        # Add classes for relegation and European qualification
        if pos == 0:
            row_class = "europaleague"
        elif pos == 1 or pos == 2:
            row_class = "conference-league"
        elif pos >= team_count - 2:
            row_class = "relegation-direct"
        elif pos == team_count - 3:
            row_class = "relegation-playoff"
        
        # Get team logo if available
        logo_url = team_logos.get(team, '')
        logo_html = f'<img src="{logo_url}" alt="{team} logo" class="team-logo" onerror="this.style.display=\'none\'">' if logo_url else ''
        
        # Format the stats
        avg_pos = f"{stats['avg_pos']:.1f}"
        top3_pct = f"{stats['top3_pct']:.0f}%"
        relegation_pct = f"{stats['relegation_pct']:.0f}%"
        
        # Generate a mini bar chart for top3 percentage
        top3_bar = f'''
            <div class="mini-bar-container">
                <div class="mini-bar top3-bar" style="width: {stats['top3_pct']}%"></div>
                <span class="mini-bar-text">{top3_pct}</span>
            </div>
        '''
        
        # Generate a mini bar chart for relegation percentage
        relegation_bar = f'''
            <div class="mini-bar-container">
                <div class="mini-bar relegation-bar" style="width: {stats['relegation_pct']}%"></div>
                <span class="mini-bar-text">{relegation_pct}</span>
            </div>
        '''
        
        html += f'''
            <tr class="{row_class}">
                <td>{pos+1}</td>
                <td>
                    <div class="team-name-with-logo">
                        {logo_html}
                        <span>{escape(team)}</span>
                    </div>
                </td>
                <td>{avg_pos}</td>
                <td>{stats['highest_pos']}</td>
                <td>{stats['lowest_pos']}</td>
                <td>{top3_bar}</td>
                <td>{relegation_bar}</td>
            </tr>
        '''
    
    html += '''
                </tbody>
            </table>
        </div>
    </section>
    '''
    
    return html

# Calculate fun stats
print("Calculating fun statistics...")
fun_stats = calculate_fun_stats(bets, sorted_allsvenskan_tip_2025)

print("Generating enhanced standings table...")
enhanced_standings_html = generate_enhanced_standings_table(sorted_allsvenskan_tip_2025, bets, team_logos)

# Try to fetch current standings
print("Fetching current Allsvenskan standings...")
try:
    # Fetch current standings
    current_standings = get_allsvenskan_standings()
    
    if not current_standings:
        print("! Could not fetch current standings from API - using fallback data")
    
    if current_standings:
        print(f"✓ Successfully fetched current standings with {len(current_standings)} teams")
    else:
        print("! Could not fetch any standings data - check your implementation")
except Exception as e:
    print(f"! Error importing or using API module: {e}")
    current_standings = []

# Generate HTML for live standings section
live_standings_html = ""
if current_standings:
    try:
        live_standings_html = generate_live_standings_html(current_standings, bets)
        print("✓ Generated live standings and leaderboard HTML")
    except Exception as e:
        print(f"! Error generating live standings HTML: {e}")

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
        /* Style for highlighted team cells */
        .team-highlight {
            background-color: rgba(255, 215, 0, 0.3) !important; /* Golden highlight */
            box-shadow: inset 0 0 0 2px rgba(255, 215, 0, 0.8) !important;
            color: white !important;
            position: relative;
            z-index: 20;
        }

        /* Ensure highlighted cells maintain their styling even in relegation/european rows */
        tr.europaleague td.team-highlight,
        tr.conference-league td.team-highlight,
        tr.relegation-direct td.team-highlight,
        tr.relegation-playoff td.team-highlight {
            background-color: rgba(255, 215, 0, 0.4) !important;
        }

        /* Also highlight the same team in the standings table */
        #standings-table td.team-highlight {
            background-color: rgba(255, 215, 0, 0.3) !important;
            box-shadow: inset 0 0 0 2px rgba(255, 215, 0, 0.8) !important;
            color: white !important;
        }

        /* Add a subtle transition for smoother highlighting */
        #predictions-table td,
        #standings-table td {
            transition: background-color 0.15s ease, box-shadow 0.15s ease, color 0.15s ease;
        }

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

        /* Additional CSS to add to your existing styles */

        /* Team logos in tables */
        .team-logo {
            height: 24px;
            width: auto;
            margin-right: 10px;
            vertical-align: middle;
        }

        .team-name-with-logo {
            display: flex;
            align-items: center;
        }

        /* Standings table specific styles */
        #live-standings-table th,
        #live-standings-table td {
            text-align: center;
        }

        #live-standings-table th:nth-child(2),
        #live-standings-table td:nth-child(2) {
            text-align: left;
        }

        /* Highlight points column */
        #live-standings-table th:last-child,
        #live-standings-table td:last-child {
            font-weight: 700;
        }

        /* Handle image loading issues */
        .team-logo.error {
            display: none;
        }

        /* Team name highlight on hover */
        .team-name-with-logo:hover {
            opacity: 0.8;
        }

        /* Responsive adjustments for standings table */
        @media (max-width: 768px) {
            #live-standings-table th:nth-child(3),
            #live-standings-table th:nth-child(7),
            #live-standings-table th:nth-child(8),
            #live-standings-table td:nth-child(3),
            #live-standings-table td:nth-child(7),
            #live-standings-table td:nth-child(8) {
                display: none; /* Hide less important columns on mobile */
            }
            
            .team-logo {
                height: 18px; /* Smaller logos on mobile */
            }
        }

        /* Fallback placeholder for missing images */
        .team-logo-placeholder {
            display: inline-block;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background-color: var(--accent);
            margin-right: 10px;
            text-align: center;
            line-height: 24px;
            color: white;
            font-weight: bold;
            font-size: 12px;
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
            position: relative;
            overflow: hidden;
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
        
        /* Fun stat card color variations */
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

        /* Additional colors for new stats */
        .fun-stat-card:nth-child(9) .fun-stat-value {
            color: #00b4d8;
        }

        .fun-stat-card:nth-child(10) .fun-stat-value {
            color: #fb8500;
        }

        .fun-stat-card:nth-child(11) .fun-stat-value {
            color: #06d6a0;
        }

        .fun-stat-card:nth-child(12) .fun-stat-value {
            color: #ef476f;
        }

        .fun-stat-card:nth-child(13) .fun-stat-value {
            color: #ffd166;
        }
        
        /* Fun stat card hover effects */
        .fun-stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background-color: transparent;
            transition: background-color 0.3s ease;
        }

        .fun-stat-card:nth-child(1):hover::before { background-color: var(--accent); }
        .fun-stat-card:nth-child(2):hover::before { background-color: var(--accent2); }
        .fun-stat-card:nth-child(3):hover::before { background-color: var(--accent3); }
        .fun-stat-card:nth-child(4):hover::before { background-color: #f72585; }
        .fun-stat-card:nth-child(5):hover::before { background-color: #4361ee; }
        .fun-stat-card:nth-child(6):hover::before { background-color: #4cc9f0; }
        .fun-stat-card:nth-child(7):hover::before { background-color: #f77f00; }
        .fun-stat-card:nth-child(8):hover::before { background-color: #7209b7; }
        .fun-stat-card:nth-child(9):hover::before { background-color: #00b4d8; }
        .fun-stat-card:nth-child(10):hover::before { background-color: #fb8500; }
        .fun-stat-card:nth-child(11):hover::before { background-color: #06d6a0; }
        .fun-stat-card:nth-child(12):hover::before { background-color: #ef476f; }
        .fun-stat-card:nth-child(13):hover::before { background-color: #ffd166; }
        
        /* Leaderboard styling */
        #current-leaderboard-table .medal-1 {
            background-color: rgba(255, 215, 0, 0.3); /* Gold */
        }
        
        #current-leaderboard-table .medal-2 {
            background-color: rgba(192, 192, 192, 0.3); /* Silver */
        }
        
        #current-leaderboard-table .medal-3 {
            background-color: rgba(205, 127, 50, 0.3); /* Bronze */
        }
        
        .best-prediction {
            color: #4cc9f0;
            font-weight: bold;
        }
        
        .worst-prediction {
            color: #f72585;
            font-weight: bold;
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

        /* Enhanced team logo styling */
        .team-logo {
            height: 24px;
            width: 24px;
            object-fit: contain;
            margin-right: 8px;
            vertical-align: middle;
            border-radius: 50%;
            background-color: rgba(255, 255, 255, 0.1);
            padding: 2px;
        }

        .team-name-with-logo {
            display: flex;
            align-items: center;
            padding: 2px 0;
        }

        /* Create a placeholder for missing logos */
        .team-logo-placeholder {
            display: inline-flex;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background-color: var(--accent);
            margin-right: 8px;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 10px;
        }

        /* Improve mobile styling for logos */
        @media (max-width: 768px) {
            .team-logo {
                height: 20px;
                width: 20px;
                margin-right: 5px;
            }
            
            .team-logo-placeholder {
                width: 20px;
                height: 20px;
                font-size: 9px;
                margin-right: 5px;
            }
            
            .team-name-with-logo span {
                font-size: 11px;
            }
        }

        /* Add a hover effect to team names */
        .team-name-with-logo:hover {
            opacity: 0.8;
            cursor: pointer;
        }

        /* Custom styling for the score bar */
        .score-bar-container {
            width: 100%;
            height: 14px;
            background-color: var(--row-even);
            border-radius: 7px;
            overflow: hidden;
            position: relative;
        }

        .score-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--accent) 0%, var(--accent2) 100%);
            border-radius: 7px;
        }

        .score-value {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 10px;
            font-weight: bold;
            color: var(--text-primary);
            text-shadow: 0 0 2px rgba(0, 0, 0, 0.5);
        }

        /* Enhanced team highlighting */
        .team-highlight .team-name-with-logo {
            position: relative;
        }

        .team-highlight .team-name-with-logo::after {
            content: '';
            position: absolute;
            top: -2px;
            left: -5px;
            right: -5px;
            bottom: -2px;
            border-radius: 4px;
            border: 2px solid rgba(255, 215, 0, 0.8);
            pointer-events: none;
        }

        /* Enhanced standings table styling */
        #standings-table {
            font-size: 13px;
        }

        #standings-table th {
            text-align: center;
            padding: 10px 8px;
            white-space: nowrap;
        }

        #standings-table th:nth-child(1),
        #standings-table td:nth-child(1) {
            width: 80px;
            text-align: center;
        }

        #standings-table th:nth-child(2),
        #standings-table td:nth-child(2) {
            width: 200px;
            text-align: left;
        }

        #standings-table td {
            text-align: center;
            padding: 4px;
        }

        /* Mini bar charts for percentages */
        .mini-bar-container {
            width: 100%;
            height: 16px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            position: relative;
            overflow: hidden;
        }

        .mini-bar {
            height: 100%;
            border-radius: 8px;
            position: absolute;
            left: 0;
            top: 0;
        }

        .mini-bar-text {
            position: absolute;
            left: 0;
            right: 0;
            top: 0;
            bottom: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 11px;
            font-weight: bold;
            text-shadow: 0 0 2px rgba(0, 0, 0, 0.7);
        }

        .top3-bar {
            background: linear-gradient(90deg, rgba(16, 185, 129, 0.7) 0%, rgba(59, 130, 246, 0.7) 100%);
        }

        .relegation-bar {
            background: linear-gradient(90deg, rgba(239, 68, 68, 0.7) 0%, rgba(245, 158, 11, 0.7) 100%);
        }

        /* Highlight cells for highest and lowest ranks */
        .best-rank {
            color: #10B981;
            font-weight: bold;
        }

        .worst-rank {
            color: #EF4444;
            font-weight: bold;
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            #standings-table th:nth-child(4),
            #standings-table th:nth-child(5),
            #standings-table td:nth-child(4),
            #standings-table td:nth-child(5) {
                display: none;
            }
            
            .mini-bar-container {
                height: 14px;
            }
            
            .mini-bar-text {
                font-size: 10px;
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
                    <div class="fun-stat-value">{escape(str(fun_stats['most_predicted_champion']))}</div>
                    <div class="fun-stat-description">Most frequently predicted to win with {fun_stats['champion_votes']} votes</div>
                </div>
    '''

if 'most_predicted_relegation' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">Direct Relegation Favorite</div>
                    <div class="fun-stat-value">{escape(str(fun_stats['most_predicted_relegation']))}</div>
                    <div class="fun-stat-description">Most frequently predicted for direct relegation (bottom 2) with {fun_stats['relegation_votes']} votes</div>
                </div>
    '''

if 'most_predicted_playoff' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">Playoff Candidate</div>
                    <div class="fun-stat-value">{escape(str(fun_stats['most_predicted_playoff']))}</div>
                    <div class="fun-stat-description">Most frequently predicted for relegation playoff (14th place) with {fun_stats['playoff_votes']} votes</div>
                </div>
    '''

if 'most_divisive_team' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">Most Divisive Team</div>
                    <div class="fun-stat-value">{escape(str(fun_stats['most_divisive_team']))}</div>
                    <div class="fun-stat-description">Highest variance in predicted positions (variance: {fun_stats['divisive_variance']})</div>
                </div>
    '''

if 'most_agreed_team' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">Most Agreed Upon Team</div>
                    <div class="fun-stat-value">{escape(str(fun_stats['most_agreed_team']))}</div>
                    <div class="fun-stat-description">Lowest variance in predicted positions (variance: {fun_stats['agreed_variance']})</div>
                </div>
    '''

if 'most_optimistic' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">The Optimist</div>
                    <div class="fun-stat-value">{escape(str(fun_stats['most_optimistic']))}</div>
                    <div class="fun-stat-description">Ranks top teams higher than others</div>
                </div>
    '''

if 'most_pessimistic' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">The Pessimist</div>
                    <div class="fun-stat-value">{escape(str(fun_stats['most_pessimistic']))}</div>
                    <div class="fun-stat-description">Ranks top teams lower than others</div>
                </div>
    '''

if 'most_unique' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">The Maverick</div>
                    <div class="fun-stat-value">{escape(str(fun_stats['most_unique']))}</div>
                    <div class="fun-stat-description">Most predictions different from the consensus</div>
                </div>
    '''

if 'prophet' in fun_stats:
    html_content += f'''
                <div class="fun-stat-card">
                    <div class="fun-stat-title">The Prophet</div>
                    <div class="fun-stat-value">{escape(str(fun_stats['prophet']))}</div>
                    <div class="fun-stat-description">Predictions most aligned with the group consensus</div>
                </div>
    '''

html_content += '''
            </div>
        </section>
'''

# Insert live standings section if available
if live_standings_html:
    html_content += live_standings_html

# Continue with the average standings section        
html_content += enhanced_standings_html

html_content += '''
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
    html_content += f'                            <th>{escape(user)}</th>\n'

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
        html_content += f'                            <td>{escape(bet)}</td>\n'
    
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

    <script>
        // Function to highlight the same team across all predictions and standings
        function setupTeamHighlighting() {
            // Get the predictions table and standings table
            const predictionsTable = document.getElementById('predictions-table');
            const standingsTable = document.getElementById('standings-table');
            if (!predictionsTable || !standingsTable) return;
            
            // Live standings table (optional)
            const liveStandingsTable = document.getElementById('live-standings-table');
            
            // Get all cells in the predictions table (excluding header and position column)
            const predictionCells = predictionsTable.querySelectorAll('tbody td:not(:first-child)');
            
            // Get all team cells from live standings - need to handle the new structure with logos
            const liveStandingTeamCells = liveStandingsTable ? 
                liveStandingsTable.querySelectorAll('tbody td:nth-child(2)') : [];
            
            // For each cell in predictions table, add mouseenter and mouseleave event listeners
            predictionCells.forEach(cell => {
                cell.addEventListener('mouseenter', function() {
                    const teamName = this.textContent.trim();
                    
                    // Skip if empty cell
                    if (!teamName) return;
                    
                    // Highlight this team across all tables
                    highlightTeam(teamName);
                });
                
                cell.addEventListener('mouseleave', function() {
                    // Remove highlight from all cells in all tables
                    removeAllHighlights();
                });
            });
            
            // Allow highlighting from consensus standings table to predictions table
            standingTeamCells.forEach(cell => {
                cell.addEventListener('mouseenter', function() {
                    const teamName = this.textContent.trim();
                    
                    // Highlight this team across all tables
                    highlightTeam(teamName);
                });
                
                cell.addEventListener('mouseleave', function() {
                    // Remove highlight from all cells in all tables
                    removeAllHighlights();
                });
            });
            // Allow highlighting from live standings table to other tables
            if (liveStandingTeamCells.length > 0) {
                liveStandingTeamCells.forEach(cell => {
                    cell.addEventListener('mouseenter', function() {
                        // Handle both old and new format - the cell might contain just text or a div with an image and span
                        let teamName;
                        const teamNameSpan = cell.querySelector('.team-name-with-logo span');
                        
                        if (teamNameSpan) {
                            // New format with logo
                            teamName = teamNameSpan.textContent.trim();
                        } else {
                            // Old format - direct text
                            teamName = cell.textContent.trim();
                        }
                        
                        if (!teamName) return;
                        
                        // Highlight this team across all tables
                        highlightTeam(teamName);
                    });
                    
                    cell.addEventListener('mouseleave', function() {
                        // Remove highlight from all cells in all tables
                        removeAllHighlights();
                    });
                });
            }
            
            // Function to highlight a team across all tables
            function highlightTeam(teamName) {
                // Find all cells with the same team name in predictions and highlight them
                predictionCells.forEach(predCell => {
                    if (predCell.textContent.trim() === teamName) {
                        predCell.classList.add('team-highlight');
                    }
                });
                
                // Find the team in consensus standings table and highlight it
                standingTeamCells.forEach(teamCell => {
                    if (teamCell.textContent.trim() === teamName) {
                        // Highlight the team cell
                        teamCell.classList.add('team-highlight');
                        // Also highlight position and score cells (siblings)
                        teamCell.previousElementSibling?.classList.add('team-highlight');
                        teamCell.nextElementSibling?.classList.add('team-highlight');
                    }
                });
                
                // Find the team in live standings table and highlight it
                if (liveStandingTeamCells.length > 0) {
                    liveStandingTeamCells.forEach(teamCell => {
                        // Check for both formats - either direct text or div with span
                        const teamSpan = teamCell.querySelector('.team-name-with-logo span');
                        const cellTeamName = teamSpan ? teamSpan.textContent.trim() : teamCell.textContent.trim();
                        
                        if (cellTeamName === teamName) {
                            // Highlight the entire row for better visibility
                            const row = teamCell.closest('tr');
                            if (row) {
                                row.querySelectorAll('td').forEach(td => {
                                    td.classList.add('team-highlight');
                                });
                            } else {
                                // Fallback to just highlighting the team cell
                                teamCell.classList.add('team-highlight');
                                teamCell.previousElementSibling?.classList.add('team-highlight');
                            }
                        }
                    });
                }
            }
            
            // Function to remove all highlights
            function removeAllHighlights() {
                document.querySelectorAll('.team-highlight').forEach(highlightedCell => {
                    highlightedCell.classList.remove('team-highlight');
                });
            }
            
            // Handle image loading errors for team logos
            document.querySelectorAll('.team-logo').forEach(img => {
                img.onerror = function() {
                    // Create a placeholder with team initials
                    const teamName = img.alt.replace(' logo', '');
                    const initials = teamName.split(' ').map(word => word[0]).join('');
                    
                    const placeholder = document.createElement('div');
                    placeholder.className = 'team-logo-placeholder';
                    placeholder.textContent = initials;
                    
                    // Replace the image with the placeholder
                    img.parentNode.replaceChild(placeholder, img);
                };
            });
        }

        // Function to handle team logo failures and create placeholders
        function handleTeamLogos() {
            // Get all team logo images
            const teamLogos = document.querySelectorAll('.team-logo');
            
            // For each logo, add an error handler
            teamLogos.forEach(img => {
                img.onerror = function() {
                    // Get the team name from the alt attribute
                    const teamName = img.alt.replace(' logo', '');
                    
                    // Create initials from the team name
                    let initials = '';
                    if (teamName) {
                        const words = teamName.split(' ');
                        initials = words.map(word => word.charAt(0)).join('');
                        
                        // Limit to 2 characters
                        if (initials.length > 2) {
                            initials = initials.substring(0, 2);
                        }
                    }
                    
                    // Create a placeholder element
                    const placeholder = document.createElement('div');
                    placeholder.className = 'team-logo-placeholder';
                    placeholder.textContent = initials;
                    
                    // Replace the image with the placeholder
                    if (img.parentNode) {
                        img.parentNode.replaceChild(placeholder, img);
                    }
                };
            });
        }

        // Call the function when the document is fully loaded
        document.addEventListener('DOMContentLoaded', function() {
            handleTeamLogos();
            setupTeamHighlighting(); // Your existing function
        });
    </script>

</body>
</html>'''

html_output.write(html_content)
html_output.close()
readme.close()

print("✓ Successfully generated files with improved stats and Allsvenskan standings!")
print("  - index.html: Dark mode design with proper relegation highlighting and European qualification")
print("  - README.md: Original GitHub format preserved")
if current_standings:
    print(f"  - Current Allsvenskan standings for {len(current_standings)} teams added")
    print("  - Added live prediction scores based on current standings")
else:
    print("  - Could not fetch current Allsvenskan standings")
print("  - Added team highlighting that works across all tables")
print("  - Fun stats now include The Dark Horse and The Underrated Team")