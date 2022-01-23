from mwrogue.esports_client import EsportsClient
from mwrogue.auth_credentials import AuthCredentials
import mwparserfromhell


class SbToWinners:
    summary = "Discover sides & winners from the SB & populate in the row"
    
    def __init__(self, site: EsportsClient):
        self.site = site
    
    def run(self):
        fields = [
            "SG.Team1",
            "SG.Team2",
            "SG.WinTeam",
            "SG.MatchHistory",
            "MSG.N_MatchInTab",
            "MSG.N_TabInPage",
            "MSG.N_GameInMatch",
            "MSG._pageName=DataPage",
        ]
        result = self.site.cargo_client.query(
            tables="ScoreboardGames=SG, MatchScheduleGame=MSG",
            fields=fields,
            join_on="MSG.GameId=SG.GameId",
            where=f"(MSG.Blue IS NULL OR MSG.Red IS NULL OR MSG.Winner IS NULL) "
                  f"AND (SG.Team1 IS NOT NULL OR SG.Team2 IS NOT NULL OR SG.WinTeam IS NOT NULL)",
            order_by='MSG._pageName'
        )
        
        current_page = {
            'page': None,
            'wikitext': None,
            'page_name': None,
            'old_text': None,
        }
        
        for item in result:
            tab_target = int(item['N TabInPage'])
            match_target = int(item['N MatchInTab'])
            game_target = int(item['N GameInMatch'])
            
            if current_page['page_name'] != item['DataPage']:
                if current_page['page'] is not None:
                    self.save_page(current_page)
                current_page['page_name'] = item['DataPage']
                current_page['page'] = self.site.client.pages[current_page['page_name']]
                old_text = current_page['page'].text()
                current_page['old_text'] = old_text
                current_page['wikitext'] = mwparserfromhell.parse(old_text)
            
            tab_counter = 0
            match_counter = 0
            game_counter = 0
            for template in current_page['wikitext'].filter_templates():
                if template.name.matches("MatchSchedule/Start"):
                    tab_counter += 1
                    match_counter = 0
                elif template.name.matches("MatchSchedule"):
                    match_counter += 1
                    game_counter = 0
                elif template.name.matches("MatchSchedule/Game"):
                    game_counter += 1
                    if (tab_counter, match_counter, game_counter) == (tab_target, match_target, game_target):
                        if not template.has("blue", ignore_empty=True):
                            template.add("blue", item['Team1'])
                        if not template.has("red", ignore_empty=True):
                            template.add("red", item['Team2'])
                        if not template.has("winner", ignore_empty=True):
                            template.add("winner", item['WinTeam'])
                        if not template.has("mh"):
                            template.add('mh', item['MatchHistory'])
        
        # we need to catch the last iteration too (assuming we actually did anything)
        if current_page['page'] is not None:
            self.save_page(current_page)
    
    def save_page(self, page_dict):
        new_text = str(page_dict['wikitext'])
        if new_text != page_dict['old_text']:
            self.site.save(page_dict['page'], new_text, summary=self.summary)


if __name__ == '__main__':
    credentials = AuthCredentials(user_file='me')
    lol_site = EsportsClient('lol', credentials=credentials)  # Set wiki
    SbToWinners(lol_site).run()
