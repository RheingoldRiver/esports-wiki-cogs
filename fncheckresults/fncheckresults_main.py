from mwrogue.esports_client import EsportsClient
from mwrogue.auth_credentials import AuthCredentials


def check_results(site: EsportsClient, title):
    title = site.target(title)
    tables = [
        'TournamentResults=TR',
        'TournamentResults__RosterLinks=RL',
        'PlayerRedirects=PR',
        'Players=P',
    ]
    join = [
        'TR._ID=RL._rowID',
        'RL._value=PR.AllName',
        'PR._pageName=P._pageName',
    ]
    result = site.cargo_client.query(
        tables=','.join(tables),
        join_on=','.join(join),
        fields='TR.Team=Team,RL._value=Player',
        where='TR.Team != P.Team AND TR._pageName="Data:{}"'.format(title)
    )
    return result


if __name__ == '__main__':
    credentials = AuthCredentials(user_file="me")
    fn_site = EsportsClient('fortnite', credentials=credentials)
    final_result = check_results(fn_site, "Fortnite Champion Series: Chapter 2 Season 4/Heat 3/Europe")
    print(final_result)
    print(len(final_result))
