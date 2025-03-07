from tabulate import tabulate

allsvenskan_tip_2025 = {}

with open('README.md', 'r', encoding='utf8') as f:
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

print("# Grabbarnas Allsvenska 2025")

sorted_allsvenskan_tip_2025 = {k: v for k, v in sorted(allsvenskan_tip_2025.items(), key=lambda item: item[1])}
table_data = [(team, value) for team, value in sorted_allsvenskan_tip_2025.items()]
print(tabulate(table_data, headers=["Team", "Value"], tablefmt="github") + "\n")

print("# Grabbarns Bet")
for user in bets.keys():
    print(f"## {user}")
    for i, bet in enumerate(bets[user]):
        if bet not in list(allsvenskan_tip_2025.keys()):
            allsvenskan_tip_2025[bet] = i
        else:
            allsvenskan_tip_2025[bet] += i
        print(f"{i + 1}. {bet}")
    print("")