from mwrogue.esports_client import EsportsClient
from mwrogue.auth_credentials import AuthCredentials
import mwparserfromhell

credentials = AuthCredentials(user_file="bot")
site = EsportsClient("lol", credentials=credentials)

response = site.cargo_client.query(
    tables="ScoreboardGames=SG, MatchScheduleGame=MSG",
    fields="SG.Team1,SG.Team2,SG.WinTeam,MSG.N_MatchInTab,MSG.N_TabInPage,MSG.N_GameInMatch,MSG._pageName=Page",
    join_on="MSG.GameId=SG.GameId",
    where=f"(MSG.Blue IS NULL OR MSG.Red IS NULL OR MSG.Winner IS NULL) AND (SG.Team1 IS NOT NULL OR SG.Team2 IS NOT NULL OR SG.WinTeam IS NOT NULL)",
)

datapages = []

for item in response:
    datapage = item["Page"]
    if datapage not in datapages:
        datapages.append(datapage)

for datapage in datapages:
    page = site.client.pages[datapage]
    page_text = page.text()
    page_wikitext = mwparserfromhell.parse(page_text)
    items = {}
    for item in response:
        if item["Page"] != datapage:
            continue
        match_in_tab = str(item["N MatchInTab"])
        tab_in_page = str(item["N TabInPage"])
        game_in_match = str(item["N GameInMatch"])
        blue = item["Team1"].strip()
        red = item["Team2"].strip()
        if item["WinTeam"] == item["Team1"]:
            winner = "1"
        elif item["WinTeam"] == item["Team2"]:
            winner = "2"
        else:
            winner = ""
        items[f"{tab_in_page}_{match_in_tab}_{game_in_match}"] = [blue, red, winner]
    tab_counters = 0
    match_counters = 0
    game_counters = 0
    for template in page_wikitext.filter_templates():
        if template.name.matches("MatchSchedule/Start"):
            tab_counters += 1
            match_counters = 0
        elif template.name.matches("MatchSchedule"):
            match_counters += 1
            game_counters = 0
        elif template.name.matches("MatchSchedule/Game"):
            game_counters += 1
            if f"{tab_counters}_{match_counters}_{game_counters}" in items:
                blue, red, winner = items.get(f"{tab_counters}_{match_counters}_{game_counters}")
                if not template.has("blue", ignore_empty=True):
                    if blue != "":
                        template.add("blue", blue)
                if not template.has("red", ignore_empty=True):
                    if red != "":
                        template.add("red", red)
                if not template.has("winner", ignore_empty=True):
                    if winner != "":
                        template.add("winner", winner)
        else:
            continue
    if str(page_wikitext) != page_text:
        page.edit(str(page_wikitext), summary="Automatically adding Winners from Scoreboards")