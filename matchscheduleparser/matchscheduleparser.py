import discord
import json
import requests
from redbot.core import commands
from redbot.core.utils.chat_formatting import text_to_file
from mwrogue.wiki_time_parser import time_from_str

# links
SCHEDULE = "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US&leagueId={}"

NEXT = "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=en-US&leagueId={}&pageToken={}"

LEAGUES = "https://esports-api.lolesports.com/persisted/gw/getLeagues?hl=en-US"

# templates
START = """== {0} ==
{{{{SetPatch|patch= |disabled= |hotfix= |footnote=}}}}
{{{{MatchSchedule/Start|tab={0} |bestof={1} |shownname= }}}}\n"""

MATCH = """{{{{MatchSchedule|<!-- Do not change the order of team1 and team2!! -->|team1={t1} |team2={t2} |team1score= |team2score= |winner=
|date={date} |time={time} |timezone={timezone} |dst={dst} |pbp= |color= |vodinterview= |with= |stream={stream} |reddit=\n{games}\n}}}}\n"""

BO1_GAMES = """|game1={{MatchSchedule/Game\n|blue= |red= |winner= |ssel= |ff=\n|mh=\n|riot_platform_game_id=\n|recap=\n|vodpb=\n|vodstart=\n|vodpost=\n|vodhl=\n|vodinterview=\n|with=\n|mvp=\n}}"""

BO2_GAMES = """|game1={{MatchSchedule/Game\n|blue= |red= |winner= |ssel= |ff=\n|mh=\n|riot_platform_game_id=\n|recap=\n|vodpb=\n|vodstart=\n|vodpost=\n|vodhl=\n|vodinterview=\n|with=\n|mvp=\n}}
|game2={{MatchSchedule/Game\n|blue= |red= |winner= |ssel= |ff=\n|mh=\n|riot_platform_game_id=\n|recap=\n|vodpb=\n|vodstart=\n|vodpost=\n|vodhl=\n|vodinterview=\n|with=\n|mvp=\n}}"""

BO3_GAMES = """|game1={{MatchSchedule/Game\n|blue= |red= |winner= |ssel= |ff=\n|mh=\n|riot_platform_game_id=\n|recap=\n|vodpb=\n|vodstart=\n|vodpost=\n|vodhl=\n|vodinterview=\n|with=\n|mvp=\n}}
|game2={{MatchSchedule/Game\n|blue= |red= |winner= |ssel= |ff=\n|mh=\n|riot_platform_game_id=\n|recap=\n|vodpb=\n|vodstart=\n|vodpost=\n|vodhl=\n|vodinterview=\n|with=\n|mvp=\n}}
|game3={{MatchSchedule/Game\n|blue= |red= |winner= |ssel= |ff=\n|mh=\n|riot_platform_game_id=\n|recap=\n|vodpb=\n|vodstart=\n|vodpost=\n|vodhl=\n|vodinterview=\n|with=\n|mvp=\n}}"""

BO5_GAMES = """|game1={{MatchSchedule/Game\n|blue= |red= |winner= |ssel= |ff=\n|mh=\n|riot_platform_game_id=\n|recap=\n|vodpb=\n|vodstart=\n|vodpost=\n|vodhl=\n|vodinterview=\n|with=\n|mvp=\n}}
|game2={{MatchSchedule/Game\n|blue= |red= |winner= |ssel= |ff=\n|mh=\n|riot_platform_game_id=\n|recap=\n|vodpb=\n|vodstart=\n|vodpost=\n|vodhl=\n|vodinterview=\n|with=\n|mvp=\n}}
|game3={{MatchSchedule/Game\n|blue= |red= |winner= |ssel= |ff=\n|mh=\n|riot_platform_game_id=\n|recap=\n|vodpb=\n|vodstart=\n|vodpost=\n|vodhl=\n|vodinterview=\n|with=\n|mvp=\n}}
|game4={{MatchSchedule/Game\n|blue= |red= |winner= |ssel= |ff=\n|mh=\n|riot_platform_game_id=\n|recap=\n|vodpb=\n|vodstart=\n|vodpost=\n|vodhl=\n|vodinterview=\n|with=\n|mvp=\n}}
|game5={{MatchSchedule/Game\n|blue= |red= |winner= |ssel= |ff=\n|mh=\n|riot_platform_game_id=\n|recap=\n|vodpb=\n|vodstart=\n|vodpost=\n|vodhl=\n|vodinterview=\n|with=\n|mvp=\n}}"""

END = "{{MatchSchedule/End}}\n"


ERROR_MESSAGE = "An error has occured. {} might not exist. If your input contains spaces, try again using quotes!"


class MatchScheduleParser(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def lolesportsparser(self, ctx):
        """Commands to parse lolesports match schedules"""

    @lolesportsparser.command()
    async def parse(self, ctx, tournament, stream=""):
        try:
            schedule = get_schedule(tournament, stream)
        except TypeError:
            try:
                schedule = get_schedule(tournament.upper(), stream)
            except TypeError:
                await ctx.send(ERROR_MESSAGE.format(tournament))
                return
        await ctx.author.send(file=text_to_file(schedule, filename="matchschedule.txt"))
        if not isinstance(ctx.channel, discord.channel.DMChannel):
            await ctx.send("Check your DMs!")

    @lolesportsparser.command()
    async def list(self, ctx):
        leagues = get_leagues()
        await ctx.send(leagues)


def get_headers():
    api_key = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"  # Todo: Get API Key from website but probably not
    headers = {"x-api-key": api_key}
    return headers


def get_json(json_type, headers):
    request = requests.get(json_type, headers=headers)
    json_file = json.loads(request.text)
    return json_file


def get_all_jsons(first_json, league_id, headers):
    jsons = [first_json]
    next_token = filter_json(first_json, "data", "schedule", "pages", "newer")
    while next_token is not None:
        next_json = get_json(NEXT.format(league_id, next_token), headers)
        jsons.append(next_json)
        next_token = filter_json(next_json, "data", "schedule", "pages", "newer")
    return jsons


def get_league(league_name, headers):
    json_leagues = get_json(LEAGUES, headers)
    json_leagues = filter_json(json_leagues, "data", "leagues")
    league_dict = next((league_dict for league_dict in json_leagues if league_dict["name"] == league_name), None)
    league_id = league_dict["id"]
    return league_id


def get_leagues():
    headers = get_headers()
    leagues = "Leagues available on lolesports.com are:\n```"
    json_leagues = get_json(LEAGUES, headers)
    json_leagues = filter_json(json_leagues, "data", "leagues")
    for league in json_leagues:
        print(type(league))
        print(league)
        leagues = leagues + league["name"] + "\n"
    leagues = leagues + "```"
    return leagues


def filter_json(json_file, *args):
    new_json = json_file
    for arg in args:
        try:
            new_json = new_json[arg]
        except KeyError:
            print("Couldn't find '{}'. Original json returned.".format(arg))
            return json_file
    return new_json


def parse_schedule(jsons, stream=""):
    schedule, current_tab = "", ""
    for json_file in jsons:
        json_schedule = filter_json(json_file, "data", "schedule", "events")
        for game in json_schedule:
            parsed_time = time_from_str(game["startTime"], tz="UTC")
            display = game["blockName"]
            team1 = game["match"]["teams"][0]["name"]
            team2 = game["match"]["teams"][1]["name"]
            bestof = game["match"]["strategy"]["count"]
            if display != current_tab:
                schedule = schedule + END + START.format(display, bestof)
                current_tab = display
            if bestof == 1:
                schedule = schedule + MATCH.format(t1=team1, t2=team2, date=parsed_time.cet_date, time=parsed_time.cet_time,
                                                   timezone="CET", dst=parsed_time.dst, stream=stream, games=BO1_GAMES)
            elif bestof == 2:
                schedule = schedule + MATCH.format(t1=team1, t2=team2, date=parsed_time.cet_date, time=parsed_time.cet_time,
                                                   timezone="CET", dst=parsed_time.dst, stream=stream, games=BO2_GAMES)
            elif bestof == 3:
                schedule = schedule + MATCH.format(t1=team1, t2=team2, date=parsed_time.cet_date, time=parsed_time.cet_time,
                                                   timezone="CET", dst=parsed_time.dst, stream=stream, games=BO3_GAMES)
            elif bestof == 5:
                schedule = schedule + MATCH.format(t1=team1, t2=team2, date=parsed_time.cet_date, time=parsed_time.cet_time,
                                                   timezone="CET", dst=parsed_time.dst, stream=stream, games=BO5_GAMES)
            else:
                # Todo: Throw an exception or something
                schedule = schedule + MATCH.format(t1=team1, t2=team2, date=parsed_time.cet_date, time=parsed_time.cet_time,
                                                   timezone="CET", dst=parsed_time.dst, stream=stream, games=BO1_GAMES)
    schedule = schedule.replace("{{MatchSchedule/End}}\n", "", 1)
    schedule = schedule + END
    return schedule


def get_schedule(league_name, stream):
    headers = get_headers()
    league_id = get_league(league_name, headers)
    json_schedule = get_json(SCHEDULE.format(league_id), headers)
    jsons = get_all_jsons(json_schedule, league_id, headers)
    schedule = parse_schedule(jsons, stream=stream)
    return schedule
