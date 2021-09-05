import mwparserfromhell
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
        vod_options = ['MSG.{}'.format(_) for _ in self.vod_params]
        fields = [
            'COALESCE({})=Vod'.format(', '.join(vod_options)),
            'MSG._pageName=MSGPage',
            'SG._pageName=SBPage',
            'SG.N_MatchInPage=N_MatchInPage',
            'SG.N_GameInMatch=N_GameInMatch'
        ]
        result = self.site.cargo_client.query(
            tables="MatchScheduleGame=MSG,ScoreboardGames=SG",
            join_on="MSG.GameId=SG.GameId",
            where="SG.VOD IS NULL AND SG._pageName IS NOT NULL AND ({})".format(where_condition),
            fields=', '.join(fields),
            order_by='SG._pageName, SG.N_MatchInPage',  # this is just to group same pages consecutively
            limit=5000
        )
        
        current_page = {
            'page': None,
            'wikitext': None,
            'page_name': None,
        }
        for item in result:
            if current_page['page_name'] != item['SBPage']:
                if current_page['page'] is not None:
                    self.save_page(current_page)
                current_page['page_name'] = item['SBPage']
                current_page['page'] = self.site.client.pages[current_page['page_name']]
                current_page['wikitext'] = mwparserfromhell.parse(current_page['page'].text())
                print('Discovered page {}'.format(current_page['page_name']))
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
            # print('Game: {}, Target: {}, Match: {}, Target: {}'.format(str(n_game_in_match), str(n_game_target), str(n_match), str(n_match_target)))
            if n_game_in_match != n_game_target or n_match != n_match_target:
                continue
            template.add('vodlink', item['Vod'])
    
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
    
    def save_page(self, page):
        new_text = str(page['wikitext'])
        if new_text != page['page'].text():
            self.site.save(page['page'], new_text, summary=self.summary)


if __name__ == '__main__':
    credentials = AuthCredentials(user_file='me')
    site = EsportsClient('lol', credentials=credentials)  # Set wiki
    VodsToSbRunner(site, ['VodPB', 'VodGameStart', 'Vod', 'VodPostgame']).run()
