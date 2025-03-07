from tabulate import tabulate
from datetime import datetime

allsvenskan_tip_2025 = {}
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

readme.write("# 🏆 Grabbarnas Allsvenskan 2025 🏆\n\n")

readme.write("## 📊 Current Standings\n")

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

table_result = tabulate(table_data, headers=["Position", "Team", "Value"], tablefmt="github")
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

headers = ["Position"] + list(bets.keys())

readme.write(tabulate(predictions_table, headers=headers, tablefmt="github") + "\n")

if len(predictions_table) != 16:
    print(f"!!! Warning: Too many teams ({len(predictions_table)}) in table, someone spelled it wrong!!!")