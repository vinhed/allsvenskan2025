import requests
import json
from datetime import datetime

def get_allsvenskan_standings():
    """
    Fetch the current Allsvenskan standings from the official API
    Returns a list of teams in their current order (1st to last)
    """
    url = "https://allsvenskan.se/data-endpoint/statistics/standings/2025/total"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Parse JSON response
        data = response.json()
        
        # Create a list to store team information in order
        standings_data = []
        
        # Process each team entry (ignoring the 'undefined' key)
        for key, team_info in data.items():
            # Skip the 'undefined' key and any non-numeric keys
            if not key.isdigit():
                continue
                
            # Extract team information
            position = int(team_info.get('position', 0))
            team_name = team_info.get('name', '')
            display_name = team_info.get('displayName', team_name)
            logo_url = team_info.get('logoImageUrl', '')
            
            # Get stats
            stats = {}
            for stat in team_info.get('stats', []):
                stat_name = stat.get('name', '')
                stat_value = stat.get('value', 0)
                stats[stat_name] = stat_value
            
            # Add team to list
            standings_data.append({
                'position': position,
                'name': team_name,
                'displayName': display_name,
                'logoUrl': logo_url,
                'stats': stats
            })
        
        # Sort by position
        standings_data.sort(key=lambda x: x['position'])
        
        # Extract just the team names for compatibility with existing code
        standings = [team['displayName'] for team in standings_data]
        
        # Store the full data for use in the HTML generation
        get_allsvenskan_standings.full_data = standings_data
        
        return standings
    
    except Exception as e:
        print(f"Error fetching Allsvenskan standings from API: {e}")
        # Fall back to parsing the team data directly
        try:
            # Extract team names from the team data if we at least got that
            if 'data' in locals() and 'documents' in data:
                return [team['fields'].get('name', {}).get('stringValue') 
                        for team in data['documents'] 
                        if 'name' in team['fields']]
        except Exception as nested_e:
            print(f"Error in fallback processing: {nested_e}")
        
        return []

def calculate_prediction_scores(bets, actual_results):
    """
    Calculate scores for each person based on the difference between 
    their predictions and actual results. Higher score is better.
    """
    scores = {}
    team_count = len(actual_results)
    
    # Calculate the theoretical maximum error possible
    # Worst case: predicting teams in completely reverse order
    max_possible_error = (team_count * team_count) // 2 if team_count % 2 == 0 else ((team_count * team_count) - 1) // 2
    
    for user, predictions in bets.items():
        total_error = 0
        user_team_errors = {}  # Track error for each team
        
        for predicted_pos, team in enumerate(predictions):
            # Skip if the team isn't in actual results
            if team not in actual_results:
                continue
                
            # Get actual position (0-indexed in the list)
            actual_pos = actual_results.index(team)
            
            # Calculate absolute error for this team
            error = abs(predicted_pos - actual_pos)
            total_error += error
            
            user_team_errors[team] = {
                'predicted': predicted_pos + 1,  # +1 for display position
                'actual': actual_pos + 1,        # +1 for display position
                'error': error
            }
        
        # Find best and worst predictions
        if user_team_errors:
            best_prediction = min(user_team_errors.items(), key=lambda x: x[1]['error'])
            worst_prediction = max(user_team_errors.items(), key=lambda x: x[1]['error'])
        else:
            best_prediction = None
            worst_prediction = None
        
        # Convert error to a positive score (higher is better)
        positive_score = max_possible_error - total_error
        
        scores[user] = {
            'score': positive_score,
            'max_possible': max_possible_error,
            'raw_error': total_error,
            'percent': round((positive_score / max_possible_error) * 100, 1),
            'best_prediction': best_prediction,
            'worst_prediction': worst_prediction
        }
    
    return scores

def get_leaderboard(scores):
    """
    Create a sorted leaderboard from scores (higher is better)
    """
    return sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)

def generate_live_standings_html(standings, bets):
    """
    Generate HTML for the live standings section
    """
    if not standings:
        return ""
    
    # Get current date and time
    now = datetime.now()
    formatted_date = now.strftime("%B %d, %Y at %H:%M")
    
    # Calculate scores
    scores = calculate_prediction_scores(bets, standings)
    leaderboard = get_leaderboard(scores)
    
    # Get the full standings data if available
    full_standings_data = getattr(get_allsvenskan_standings, 'full_data', None)
    
    html = f"""
    <!-- Live Standings Section -->
    <section class="section" id="live-standings-section">
        <h2 class="section-title"><span class="icon">📊</span> Current Allsvenskan Standings</h2>
        <p class="section-description">Latest standings as of {formatted_date}</p>
        
        <div class="table-wrapper">
            <table id="live-standings-table">
                <thead>
                    <tr>
                        <th>Position</th>
                        <th>Team</th>
                        <th>Matches</th>
                        <th>W</th>
                        <th>D</th>
                        <th>L</th>
                        <th>GF</th>
                        <th>GA</th>
                        <th>GD</th>
                        <th>Points</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    team_count = len(standings)
    
    # If we have the full data, use it for enhanced display
    if full_standings_data:
        for team_data in full_standings_data:
            position = team_data['position']
            team_name = team_data['displayName']
            logo_url = team_data['logoUrl']
            stats = team_data.get('stats', {})
            
            # Convert list of stats to dict if needed
            if isinstance(stats, list):
                stats_dict = {}
                for stat in stats:
                    stat_name = stat.get('name', '')
                    stat_value = stat.get('value', 0)
                    stats_dict[stat_name] = stat_value
                stats = stats_dict
            
            # Get statistics
            matches = stats.get('gp', 0)
            wins = stats.get('w', 0)
            draws = stats.get('t', 0)  # t for ties/draws
            losses = stats.get('l', 0)
            goals_for = stats.get('gf', 0)
            goals_against = stats.get('ga', 0)
            goal_diff = stats.get('d', 0)  # d for goal difference
            points = stats.get('pts', 0)
            
            # Determine row class based on position
            row_class = ""
            if position == 1:
                row_class = "europaleague"  # 1st place - Europa League
            elif position in [2, 3]:
                row_class = "conference-league"  # 2nd and 3rd place - Conference League
            elif position >= team_count - 1:  # Bottom 2 teams (direct relegation)
                row_class = "relegation-direct"
            elif position == team_count - 2:  # 3rd from bottom (playoff)
                row_class = "relegation-playoff"
            
            # Create the team cell with logo
            team_cell = f"""<td>
                        <div style="display: flex; align-items: center;">
                            <img src="{logo_url}" alt="{team_name} logo" style="height: 24px; margin-right: 10px;">
                            <span>{team_name}</span>
                        </div>
                    </td>"""
            
            html += f"""
                    <tr class="{row_class}">
                        <td>{position}</td>
                        {team_cell}
                        <td>{matches}</td>
                        <td>{wins}</td>
                        <td>{draws}</td>
                        <td>{losses}</td>
                        <td>{goals_for}</td>
                        <td>{goals_against}</td>
                        <td>{goal_diff}</td>
                        <td><strong>{points}</strong></td>
                    </tr>"""
    else:
        # Fallback to simple display if full data isn't available
        for pos, team in enumerate(standings):
            position_display = pos + 1
            row_class = ""
            
            # Add classes for European qualification and relegation
            if pos == 0:
                row_class = "europaleague"  # 1st place - Europa League
            elif pos == 1 or pos == 2:
                row_class = "conference-league"  # 2nd and 3rd place - Conference League
            elif pos >= team_count - 2:  # Bottom 2 teams (direct relegation)
                row_class = "relegation-direct"
            elif pos == team_count - 3:  # 3rd from bottom (playoff)
                row_class = "relegation-playoff"
            
            html += f"""
                    <tr class="{row_class}">
                        <td>{position_display}</td>
                        <td>{team}</td>
                        <td>0</td>
                        <td>0</td>
                        <td>0</td>
                        <td>0</td>
                        <td>0</td>
                        <td>0</td>
                        <td>0</td>
                        <td>0</td>
                    </tr>"""
    
    html += """
                </tbody>
            </table>
        </div>
    </section>
    
    <!-- Current Leaderboard Section -->
    <section class="section" id="current-leaderboard-section">
        <h2 class="section-title"><span class="icon">🏆</span> Current Prediction Scores</h2>
        <p class="section-description">Based on current standings. Higher scores are better!</p>
        
        <div class="table-wrapper">
            <table id="current-leaderboard-table">
                <thead>
                    <tr>
                        <th>Position</th>
                        <th>Participant</th>
                        <th>Score</th>
                        <th>Percentage</th>
                        <th>Best Prediction</th>
                        <th>Worst Prediction</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for index, (user, score_data) in enumerate(leaderboard):
        position = index + 1
        medal_class = f"medal-{position}" if position <= 3 else ""
        
        # Format best and worst predictions
        best_team = "N/A"
        best_details = ""
        if score_data['best_prediction']:
            team, details = score_data['best_prediction']
            best_team = team
            best_details = f" (P:{details['predicted']}, A:{details['actual']})"
        
        worst_team = "N/A"
        worst_details = ""
        if score_data['worst_prediction']:
            team, details = score_data['worst_prediction']
            worst_team = team
            worst_details = f" (P:{details['predicted']}, A:{details['actual']})"
        
        html += f"""
                <tr class="{medal_class}">
                    <td>{position}{' 🏆' if position <= 3 else ''}</td>
                    <td>{user}</td>
                    <td>{score_data['score']} pts</td>
                    <td>{score_data['percent']}%</td>
                    <td class="best-prediction">{best_team}{best_details}</td>
                    <td class="worst-prediction">{worst_team}{worst_details}</td>
                </tr>"""
    
    html += """
                </tbody>
            </table>
        </div>
    </section>
    """
    
    return html

# For testing
if __name__ == '__main__':
    standings = get_allsvenskan_standings()
    if standings:
        print(f"Successfully fetched {len(standings)} teams:")
        for i, team in enumerate(standings, 1):
            print(f"{i}. {team}")
    else:
        print("Failed to fetch standings")