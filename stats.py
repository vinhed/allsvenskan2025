from tabulate import tabulate
from datetime import datetime
import html

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

# Keep original README generation for compatibility
readme.write("# 🏆 Grabbarnas Allsvenskan 2025 🏆\n\n")
readme.write("## 📊 Current Standings\n`Calculated based on everyones prediction (lower score is better)`\n")
sorted_allsvenskan_tip_2025 = {k: v for k, v in sorted(allsvenskan_tip_2025.items(), key=lambda item: item[1])}
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

# Generate Dark Mode HTML with proper alternating row colors and no gold/silver/bronze
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
            --row-even: #1e1e1e;
            --row-odd: #252525;
            --row-hover: #303030;
            --header-bg: #111111;
            --border-color: #333333;
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
            line-height: 1.6;
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
            font-size: 14px;
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
            z-index: 20;
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
            padding: 12px 15px;
            border-bottom: 1px solid var(--border-color);
        }
        
        /* First column - fixed */
        td:first-child {
            font-weight: 600;
            position: sticky;
            left: 0;
            z-index: 5;
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
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
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
            
            .stats-grid {
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
        
        <!-- Current Standings Section -->
        <section class="section">
            <h2 class="section-title"><span class="icon">📊</span> Current Standings</h2>
            <p class="section-description">Calculated based on everyone's predictions. Lower score indicates higher collective ranking.</p>
            
            <div class="table-wrapper">
                <table id="standings-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Team</th>
                            <th>Score</th>
                        </tr>
                    </thead>
                    <tbody>
'''

# Add standings table rows - without medal classes
for pos, (team, value) in enumerate(sorted_allsvenskan_tip_2025.items()):
    position_display = f"{pos+1}"
    if pos == 0:
        position_display += " 🥇"
    elif pos == 1:
        position_display += " 🥈"
    elif pos == 2:
        position_display += " 🥉"
    
    html_content += f'''
                        <tr>
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

# Add prediction rows
for i in range(max_bets):
    html_content += f'                        <tr>\n'
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

print("✓ Successfully generated both files!")
print("  - index.html: Dark mode design with proper alternating row colors")
print("  - README.md: Original GitHub format preserved")