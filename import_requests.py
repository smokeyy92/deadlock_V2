import requests
from bs4 import BeautifulSoup
import pandas as pd

heroes = [
"abrams","apollo","bebop","billy","calico","celeste","drifter","dynamo",
"graves","grey-talon","haze","holliday","infernus","ivy","kelvin",
"lady-geist","lash","mcginnis","mina","mirage","mo-and-krill",
"paige","paradox","pocket","rem","seven","shiv","silver",
"sinclair","the-doorman","venator","victor","vindicta",
"viscous","vyper","warden","wraith","yamato"
]

base = "https://statlocker.gg/heroes/hero-library/{}/overview"

rows = []

for hero in heroes:

    url = base.format(hero)
    print("Fetching", url)

    html = requests.get(url).text
    soup = BeautifulSoup(html,"lxml")

    abilities = []

    # ability names appear as headers near ability descriptions
    for h in soup.find_all(["h2","h3","h4"]):
        text = h.get_text(strip=True)

        if text and len(text) < 40:
            abilities.append(text)

    # remove duplicates and keep first 4
    abilities = list(dict.fromkeys(abilities))[:4]

    if len(abilities) < 4:
        abilities = ["","","",""]

    hero_name = hero.replace("-"," ").title()

    rows.append([
        hero_name,
        abilities[0],
        abilities[1],
        abilities[2],
        abilities[3]
    ])

df = pd.DataFrame(
    rows,
    columns=["Hero","Ability1","Ability2","Ability3","Ultimate"]
)

df.to_excel("/Users/tantig/Documents/deadlock/excel/deadlock_competitive_system.xlsx",index=False)

print("Excel created: deadlock_heroes.xlsx")