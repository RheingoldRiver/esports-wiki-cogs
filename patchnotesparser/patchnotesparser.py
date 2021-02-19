from redbot.core import commands
from bs4 import BeautifulSoup
import requests as client
import re as regex

# links
BASE_ADDRESS = "https://na.leagueoflegends.com/en-us/news/game-updates/patch-{}-notes"
DATA_DRAGON_RUNES = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/runesReforged.json"
DATA_DRAGON_ITEMS = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/item.json"
DATA_DRAGON_CHAMPIONS = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json"

class PatchNotesParser(commands.Cog):
	@commands.group()
	async def patchnotesparser(self, ctx):
		"""Commands to parse League of Legends patch notes"""

	@patchnotesparser.command()
	async def parse(self, ctx, patch_version):
		self.patch_version = validate_patch(patch_version)
		if not self.patch_version:
			await ctx.send("Incorrect patch number format, please use one of the following as the version major/minor separator: ```[ . , - ; ]```")
		#response = client.get(self.base_url)

		# something went wrong
		#if response.status_code != 200:
		#	raise ValueError(f"Expected HTTP 200 code, but got back {response.status_code}.")

		#soup = BeautifulSoup(response.text, 'html.parser')

	def validate_patch(patch_version):
		match = regex.search('^\s*[1-9]{1,2}(\.|,|-|;)[1-9]{1,2}\s*$', patch_version)
		if match:
			return patch_version.strip().Replace(",", ".").Replace("-", ".").Replace(";", ".")