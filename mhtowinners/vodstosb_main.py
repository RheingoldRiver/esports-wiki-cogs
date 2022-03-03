import mwparserfromhell
from mwcleric.errors import RetriedLoginAndStillFailed
from mwclient.errors import AssertUserFailedError
from mwrogue.auth_credentials import AuthCredentials
from mwrogue.esports_client import EsportsClient


class VodsToSbRunner(object):
    def __init__(self, site: EsportsClient, vod_params):
        self.site = site
        self.summary = 'Discover & auto-add vods to SB - Please double-check for accuracy!'
        self.vod_params = vod_params
    
    def run(self):
        where_condition = ' OR '.join(['MSG.{} IS NOT NULL'.format(_) for _ in self.vod_params])
        vod_options_string = ', '.join(['MSG.{}'.format(_) for _ in self.vod_params])
        fields = [
            'COALESCE({})=Vod'.format(vod_options_string),
            'MSG._pageName=MSGPage',
            'SG._pageName=SBPage',
            'SG.N_MatchInPage=N_MatchInPage',
            'SG.N_GameInMatch=N_GameInMatch',
            'COALESCE(SG.VOD)=SGVod',
        ]
        result = self.site.cargo_client.query(
            tables="MatchScheduleGame=MSG,ScoreboardGames=SG",
            join_on="MSG.GameId=SG.GameId",
            where=f"(SG.VOD IS NULL AND SG._pageName IS NOT NULL AND ({where_condition}))"
                  f" OR (COALESCE(SG.VOD) != COALESCE({vod_options_string}))",
            fields=', '.join(fields),
            order_by='SG._pageName, SG.N_MatchInPage',  # this is just to group same pages consecutively
        )
        
        current_page = {
            'page': None,
            'wikitext': None,
            'page_name': None,
            'old_text': None,
        }
        for item in result:
            if current_page['page_name'] != item['SBPage']:
                if current_page['page'] is not None:
                    self.save_page(current_page)
                current_page['page_name'] = item['SBPage']
                current_page['page'] = self.site.client.pages[current_page['page_name']]
                old_text = current_page['page'].text()
                current_page['old_text'] = old_text
                current_page['wikitext'] = mwparserfromhell.parse(old_text)
                # print('Discovered page {}'.format(current_page['page_name']))
            self.add_vod_to_page(item, current_page['wikitext'])
        
        # we need to catch the last iteration too (assuming we actually did anything)
        if current_page['page'] is not None:
            self.save_page(current_page)
    
    def add_vod_to_page(self, item, wikitext):
        # Modify wikitext in place
        n_match_target = int(item['N_MatchInPage'])
        n_game_target = int(item['N_GameInMatch'])
        n_match = 0
        n_game_in_match = 0
        for template in wikitext.filter_templates(recursive=False):
            name = template.name.strip()
            if 'Header' in name or self.is_match_placeholder(template):
                n_match += 1
                n_game_in_match = 0
                continue
            if self.is_game_placeholder(template):
                n_game_in_match += 1
                continue
            if not name.startswith('Scoreboard/Season') and not name.startswith('MatchRecapS8'):
                continue
            n_game_in_match += 1
            if n_game_in_match != n_game_target or n_match != n_match_target:
                continue
            # print(item['Vod'])
            template.add('vodlink', item['Vod'].replace('&amp;', '&'))
    
    @staticmethod
    def is_match_placeholder(template):
        if template.name != 'Scoreboard/Placeholder':
            return False
        if not template.has(1):
            return False
        return template.get(1).value.strip() == 'Match'
    
    @staticmethod
    def is_game_placeholder(template):
        if template.name != 'Scoreboard/Placeholder':
            return False
        if not template.has(1):
            return False
        return template.get(1).value.strip() == 'Game'
    
    def save_page(self, page_dict):
        new_text = str(page_dict['wikitext'])
        if new_text != page_dict['old_text']:
            try:
                self.site.save(page_dict['page'], new_text, summary=self.summary)
            except RetriedLoginAndStillFailed:
                pass


if __name__ == '__main__':
    credentials = AuthCredentials(user_file='bot')
    lol_site = EsportsClient('lol', credentials=credentials)  # Set wiki
    VodsToSbRunner(lol_site, ['VodPB', 'VodGameStart', 'Vod', 'VodPostgame']).run()
