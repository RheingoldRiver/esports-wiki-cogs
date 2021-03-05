from .parser_errors import ParserError, ParserFormatError, ParserHttpError
from .dragon import Dragon
from .templates import *

from dateutil import parser as DatetimeParser
from datetime import datetime as DateTime

from bs4 import BeautifulSoup, Tag
import requests as HttpClient
import re as Regex

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from river_mwclient.esports_client import EsportsClient
    from typing import Iterator


RIOT_ADDRESS: str = "https://na.leagueoflegends.com/en-us/news/game-updates/patch-{}-notes"
SUMMARY: str = "Auto-parse League of Legends patch notes."
WIKI_PAGE: str = "User:Bruno_Blanes/Patch_{}"


# known champion ability base attributes
def ability_base_attributes() -> 'list[str]':
    return ["Cooldown",
            "First Hit Bonus Damage",
            "Damage",
            "Cost",
            "Move Speed",
            "Second Hit Healing Vs. Minions"]


class PatchNotes:
    def __init__(self, site: 'EsportsClient') -> None:
        self.context: str = ""
        self.page_url: str = ""
        self.patch_version: str = ""
        self.site: 'EsportsClient' = site
        self.patch_url: 'str | None' = None
        self.sections: 'list[Section]' = []
        self.published_date = DateTime.now()
        self.designers: 'list[Designer]' = []

    def __validate_patch(self, patch_version: str) -> bool:
        if Regex.search(r'^\s*[1-9]{1,2}(\.|,|-)[1-9]{1,2}\s*$', patch_version):
            self.patch_version = patch_version.strip().replace(',', '.').replace('-', '.')
            return True
        return False

    def midpatch(self, border: 'Border | None', section: Section, content_list: 'Iterator[Tag]') -> None:
        change: 'Pnb | None' = None
        ability: 'Pai | None' = None

        # loop through all the mid-patch updates
        for content in content_list:
            if "change-title" in content["class"]:
                # border is not defined or its title is
                # different from the current border title
                if border is None or border.title != content.text.strip():
                    border = Border(content.text.strip())
                    section.borders.append(border)
                    continue

            # could not find the border title
            if border.title is None or border.title.isspace():
                raise ParserError(self, "Could not locate an HTML node with class 'change-title'.")

            # border context text
            elif "context" in content["class"]:
                border.context = content.text.strip()

            # attribute is from a champion ability
            elif "ability-title" in content["class"]:
                change = Pnb(content.text.strip())
                
                # simplified borders don't have changes
                if not border.simplified:
                    border.changes.append(change)

            # handles champion or item attribute change
            elif "attribute-change" in content["class"]:
                attribute: 'Pbc | None' = None
                if change is None: raise ParserError(self, 'HTML node with class="attribute-change" found '
                                                    'before the first "ability-title" was defined.')

                # get all the properties of the current attribute
                for attribute_tag in filter(lambda tag:
                                            isinstance(tag, Tag) and
                                            tag.has_attr("class"),
                                            content.children):
                    if "attribute" in attribute_tag["class"]:
                        attribute_info: str = attribute_tag.text.strip().title()

                        # the current change reffers to a champion
                        if any(x["name"] == change.name for x in Dragon.champions):

                            # attribute is from an ability
                            result = Regex.search(r'([QWER]|(PASSIVE))\s-\s', attribute_info)
                            if result is not None:

                                # get a substring that contains only the ability name and base attribute
                                ability_info: str = attribute_info[result.span()[0] + len(result.group(0)):]
                                ability_name: str = ""

                                # loop through all of the known ability base attributes
                                for type in ability_base_attributes():
                                    if type in ability_info:

                                        # get the substring that contains only the ability name
                                        ability_name = ability_info[:ability_info.index(type)].rstrip()
                                        attribute = Pbc(type)
                                        break
                                
                                # attribute not found
                                if attribute is None:
                                    
                                    # check if it was an ability bugfix
                                    if "Bugfix" in ability_info:
                                        ability_name = ability_info[:ability_info.index("Bugfix")].rstrip()
                                        attribute = Pbc("Bugfix")
                                    else:
                                        raise ParserError(self, "Could not find attribute type "
                                                        f"from ability '{ability_info}'.")

                                # avoid duplicate ability
                                if ability is None or ability.name != ability_name:
                                    ability = Pai(ability_name)
                                    change.abilities.append(ability)

                                # add the attribute to the ability
                                ability.attributes.append(attribute)
                            
                            # attribute is from the champion's base stats
                            elif "Base" in attribute_info:

                                # don't create duplicate base stats
                                if ability is None or ability.name != "Base Stats":
                                    ability = Pai("Base Stats")
                                    change.abilities.append(ability)

                                # add the attribute to the base stats
                                attribute = Pbc(attribute_info)
                                ability.attributes.append(attribute)

                            # check if it was a champion bugfix
                            elif "Bugfix" in attribute_info:
                                attribute = Pbc("Bugfix")
                                change.attributes.append(attribute)

                            # no fucking clue of what it is
                            else: raise ParserError(self, "Was not expecting any more champion "
                                                    f"attributes but found '{attribute_info}'.")

                        # the current change reffers to an item
                        elif any(x["name"] == change.name for x in Dragon.items):
                            attribute = Pbc(attribute_info)
                            change.attributes.append(attribute)
                        
                        else:
                            # handle as simplified list
                            if border is None or border.context and border.context != change.name:
                                border = Border(context=change.name, simplified=True)
                                section.borders.append(border)
                            
                            # reuse existing border
                            elif border.context != change.name:
                                border.context = change.name
                                border.simplified = True
                                border.changes = []

                            # create simplified attribute
                            attribute = Pbc(attribute_info)
                            border.attributes.append(attribute)

                    elif attribute is None:
                        raise ParserError(self, "Field 'attribute' was not defined.")

                    # handle previous attribute value and "attribute removed" text
                    elif "attribute-before" or "attribute-removed" in attribute_tag["class"]:
                        attribute.before = attribute_tag.text.strip()

                    # handle new attribute value
                    elif "attribute-after" in attribute_tag["class"]:
                        attribute.after = attribute_tag.text.strip().replace("<strong>", "'''").replace("</strong>", "'''")

            # reset values at the end of a change
            elif "divider" in content["class"]:
                change = None
                ability = None

    def parse_all(self, patch_version: str) -> 'PatchNotes':
        # validate patch notes version number format
        if not self.__validate_patch(patch_version):
            raise ParserFormatError(self, "Incorrect patch notes version number format.")

        self.patch_url = RIOT_ADDRESS.format(self.patch_version.replace('.', '-'))
        response = HttpClient.get(self.patch_url)

        # something went wrong
        if not response.status_code == 200:
            # TODO: Try trice and then report
            raise ParserHttpError(self, "Expected response of type `HTTP 200`, "
                                f"but got back `HTTP {response.status_code}`.")

        # assert ddragon is loaded
        Dragon.load_data()

        # load the html contents of the page
        soup = BeautifulSoup(response.text, "html.parser")

        # set the date the patch notes were published
        time: 'Tag | None' = soup.find("time")
        if time is not None:
            self.published_date = DatetimeParser.parse(time["datetime"]).date()
        else: raise ParserError(self, "Could not get article published date.")

        # patch notes context
        context: 'Tag | None' = soup.find("blockquote", {"class": "context"})
        for line in context.text.strip().split("\n")[:-1]:
            line_text: str = line.strip()
            if line_text and not line_text.isspace():
                self.context += f"{line_text}\n\n"
        self.context = self.context.rstrip()

        # patch notes designers
        designer_elements: 'list[Tag]' = soup.find_all("span", {"class": "context-designer"})
        for designer_span in designer_elements:
            designer = Designer(designer_span.text.strip().title())
            if designer.username is None:
                raise ParserError(self, f"Could not extract username from `context-designer`.")
            if designer.icon is None:
                # TODO: Somehow try to automate this process
                raise ParserError(self, f"Could not parse {designer.username}'s designer icon.")
            self.designers.append(designer)

        # gets the root div where all the patch notes are
        root: 'Tag | None' = soup.find("div", {"class": "style__Content-tkcm0t-1"})
        if root is None: raise ParserError(self, "Could not locate the main patch notes `<div>`.")

        section_id: int = 1
        border: 'Border | None' = None
        section: 'Section | None' = None
        container: 'list[Tag]' = root.find_all("div", recursive=False)

        if len(container) == 1:
            # everything is under "patch-notes-container"
            # it isn't always like this though
            # TODO: handle the other case
            container = list(filter(lambda tag:
                                    isinstance(tag, Tag) and
                                    tag.has_attr("class"),
                                    container[0].children))

        for tag in container:            
            # section headers
            if "header-primary" in tag["class"]:
                section = Section(section_id, tag.text.strip().title())
                self.sections.append(section)
                section_id += 1
                border = None
            
            # section content
            elif "content-border" in tag["class"]:
                if section is None:
                    raise ParserError(self, 'HTML node with `class="content-border"` '
                                    'found before the `"header-primary"` was defined.')
                content_list: 'Iterator[Tag]' = filter(lambda tag:
                                                    isinstance(tag, Tag),
                                                    tag.div.div.children)

                # handles mid-patch updates
                if section.title == "Mid-Patch Updates":
                    self.midpatch(border, section, content_list)
            
                # handles patch highlights
                elif section.title == "Patch Highlights":
                    border_context = list(filter(lambda tag: tag.name == "p", content_list))
                    border = Border()
                    
                    if len(border_context) > 0:
                        border.context = border_context[-1].text.strip()

                    # context might be nested in html
                    if not border.context or border.context.isspace():
                        border_context = list(filter(lambda tag: tag.name == "div", content_list))
                        if len(border_context) > 0:
                            border.context = border_context[-1].p.text.strip()
                    section.borders.append(border)
        
        # parse and save to wiki
        self.print()
        return self
        
    def print(self) -> None:
        # header
        result: str = PATCH_TABS_HEADER
        result += ONLY_INCLUDE
        result += BOX_START

        # context
        result += f"{{{{pnbh|patch_number={self.patch_version}|date={self.published_date}\n"
        result += f"|context={self.context}\n"
        result += THEMATIC_BREAK
        result += HYPERLINK.format(self.patch_url, "Official Patch Notes Link")
        result += NEW_LINE

        # print context designers
        for designer in self.designers:
            result += designer.print()
        
        result += TEMPLATE_END
        result += BOX_BREAK
        result += NEW_LINE

        # tables of content
        result += "{{PatchNotesTOC"
        for section in self.sections:
            result += section.print_toc()
        
        result += TEMPLATE_END
        result += BOX_END
        result += NEW_LINE

        # patch notes
        for section in self.sections:
            result += TITLE.format(section.title)

            if section.title == "Patch Highlights":
                result += OPEN_BORDER_DIV
                result += '<div style="border:1px solid #BBB; padding:.33em">\n'
                result += PATCH_HIGHLIGHTS.format(self.patch_version)
                result += CLOSE_DIV + CLOSE_DIV
                result += NEW_LINE
                continue

            elif section.title == "Upcoming Skins & Chromas":
                result += OPEN_BORDER_DIV

                for border in section.borders:
                    result += f"''<span style=\"color:#555\">{border.context}</span>''\n"
                    result += LINE_BREAK
                    result += "{{{{PatchSplashTable|br=2\n"

                    if section.borders.index(border) == len(section.borders) - 1:
                        pass

                    else:
                        pass
                continue
            
            for border in section.borders:
                context: str = border.print(section)

                if context and not context.isspace():
                    result += context
                
                for change in border.changes:
                    result += change.print()

                    for attribute in change.attributes:
                        result += attribute.print()
                    
                    if any(x["name"] == change.name for x in Dragon.champions):
                        for ability in change.abilities:
                            result += ability.print()

                            for attribute in ability.attributes:
                                result += attribute.print()
                        
                        if result[:1] == "=":
                            result = result[:9]
                    else:
                        for inner_change in change.changes:
                            if any(x["name"] == change.name for x in Dragon.champions):
                                if result[:1] == "=":
                                    result = result[:9]

                                result += CI.format(inner_change.name)
                                for ability in inner_change.abilities:
                                    result += ability.print()
                            else:
                                result += ANCHOR.format(inner_change)
                                for attribute in inner_change.attributes:
                                    result += attribute.print()
                    result += TEMPLATE_END
            result += NEW_LINE
        result += PATCH_LIST_NAVBOX
        
        # save to wiki
        self.page_url = WIKI_PAGE.format(self.patch_version)
        self.site.save_tile(self.page_url, result, SUMMARY)