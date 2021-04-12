from patchnotesparser.exceptions import ParserError, ParserHttpError, ParserTimeoutError
from patchnotesparser.helpers import Helper, Filters
from patchnotesparser.dragon import Dragon

from patchnotesparser.templates.splash import SplashTableEntry
from patchnotesparser.templates.pnb import Pnb, ComplexPnb
from patchnotesparser.templates.designer import Designer
from patchnotesparser.templates.section import Section
from patchnotesparser.templates.border import Border
from patchnotesparser.templates.common import *
from patchnotesparser.templates.pai import Pai
from patchnotesparser.templates.pbc import Pbc

from dateutil import parser as DatetimeParser
from datetime import datetime as DateTime
import sys as System

from river_mwclient.esports_client import EsportsClient
from bs4 import BeautifulSoup, Tag
import requests as HttpClient
from typing import Iterator

RIOT_ADDRESS: str = "https://na.leagueoflegends.com/en-us/news/game-updates/patch-{}-notes"
SUMMARY: str = "Auto-parse League of Legends patch notes."
WIKI_PAGE: str = "User:Bruno_Blanes/Patch_{}"

# TODO: ask for help with this shit
# known champion ability base attributes
def ability_base_attributes() -> 'list[str]':
    return ["Cooldown",
            "First Hit Bonus Damage",
            "Damage",
            "Cost",
            "Move Speed",
            "Second Hit Healing Vs. Minions",
            "Dash Speed",
            "Cast Range",
            "Duration",
            "Toggle Abilities Bugfix",
            "Hecarim Bugfix"]


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
        
    def _print(self) -> None:
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
        result += "{{PatchNotesTOC\n"
        for section in self.sections:
            toc_section: str = section.print_toc()

            # remove extra line breaks
            if result[-2] == "\n" and toc_section[0] == "\n":
                toc_section = toc_section[1:]
            result += toc_section
        
        result += TEMPLATE_END
        result += BOX_END
        result += NEW_LINE

        # patch notes
        for section in self.sections:
            result += section.print()

            if section.title == "Patch Highlights":
                result += OPEN_BORDER_DIV
                result += '<div style="border:1px solid #BBB;padding:.33em">'
                result += PATCH_HIGHLIGHTS.format(self.patch_version) + CLOSE_DIV
                result += section.borders[0].context + NEW_LINE + CLOSE_DIV
                result += NEW_LINE
                continue

            elif section.title == "Upcoming Skins & Chromas":
                result += OPEN_BORDER_DIV

                for border in section.borders:
                    result += f"''<span style=\"color:#555\">{border.context}</span>''\n"
                    result += LINE_BREAK
                    result += "{{PatchSplashTable|br=2\n"

                    if section.borders.index(border) == len(section.borders) - 1:
                        for i, skin in enumerate(border.skins):
                            result += f'|s{i + 1}=<div style="border:1px solid #BBB; padding:.33em"">'
                            # TODO: save files to wiki
                            result += f"[[File:.jpg|350px]]</div>'''{skin.title}'''\n"
                        
                        result += TEMPLATE_END
                        result += CLOSE_DIV

                    else:
                        for i, skin in enumerate(border.skins):
                            result += f"|s{i + 1}={{{{SplashTableEntry|{skin.title}}}}}\n"

                        result += TEMPLATE_END
                        result += LINE_BREAK
                        result += NEW_LINE
                continue
            
            for border in section.borders:
                context: str = border.print(section)

                if context and not context.isspace():
                    result += context
                
                for change in border.changes:
                    result += change.print()
            result += NEW_LINE
        result += PATCH_LIST_NAVBOX
        
        # save to wiki
        self.page_url = WIKI_PAGE.format(self.patch_version)
        self.site.save_tile(self.page_url, result, SUMMARY)

    def _aram(self, border: 'Border | None', section: Section, content_list: 'list[Tag]') -> None:
        # loop through all the changes
        for content_info in content_list:

            # set the header, usually nerfs and buffs
            if content_info.name == "h3" or "ability-title" in content_info["class"]:
                border = Border(context=content_info.text.strip(), simplified=True)
                section.borders.append(border)

            # handle the changes
            elif "attribute-change" in content_info["class"]:
                if border is None:
                    raise ParserError(self, "Field \"border\" was not defined.")
                
                attribute: Pbc = Pbc()
                border.attributes.append(attribute)

                # loop through all the properties of the current attribute
                for attribute_info in Filters.tags(list(content_info.children)):
                    
                    # handle previous attribute value
                    if "attribute-before" in attribute_info["class"]:
                        attribute.before = attribute_info.text.strip()
                    
                    # handle new attribute value
                    elif "attribute-after" in attribute_info["class"]:
                        attribute.after = attribute_info.text.strip()
                    
                    # sets the name of the attribute
                    elif "attribute" in attribute_info["class"]:
                        attribute.name = attribute_info.text.strip()

    def _changes(self, border: 'Border | None', section: Section, content_list: 'list[Tag]') -> None:
        ability: 'Pai | None' = None
        inner_change: 'Pnb | None' = None
        new: bool = any("new" in x["class"] for x in Filters.tags_with_classes(content_list))
        removed: bool = any("removed" in x["class"] for x in Filters.tags_with_classes(content_list))
        change: Pnb = Pnb(new=new, removed=removed, date=self.published_date)

        # loop through all the patch changes
        for content in Filters.tags(content_list):

            # sets the change title
            if content.has_attr("class") and "change-title" in content["class"]:
                change.name = content.text.strip()

            # handles complex changes
            # see Xin Zhao on patch notes 11.6 for reference
            elif not content.has_attr("class") and content.name == "h2":
                
                # sometimes the group title will be a simple "h2" tag
                # that doesn't mean this is a complex change
                if not change.name or change.name.isspace():
                    change.name = content.text.strip()
                    continue

                title: str = content.text.strip()
                context: str = ""

                # gets all the following paragraphs if any is present
                for i in range(1, System.maxsize):
                    element: Tag = content_list[content_list.index(content) + i]
                    if not element.name == "p":
                        break
                    context += element.text.strip() + NEW_LINE
                
                if change.complex_changes is None:
                    change.complex_changes = list()
                change.complex_changes.append(ComplexPnb(title, context))

            # sets the change summary
            elif content.has_attr("class") and "summary" in content["class"]:
                change.summary = content.text.strip()

            # sets the change context
            elif content.has_attr("class") and "context" in content["class"]:
                if change.complex_changes is None:
                    change.context = content.text.strip()
                    continue

                # if this is a complex change, then the context goes elsewhere
                complex_content: 'list[str]' = change.complex_changes[-1].text
                for context in content.text.split("\n"):
                    if context and not context.isspace():
                        complex_content.append(context.strip())

            # handle aditional context links
            elif content.name == "ul":
                
                # loop through all the list items found
                for item in Filters.tags_by_name("li", list(content.children)):

                    # format the link into the context and escape the vertical bar
                    for link in Filters.tags_by_name("a", list(item.children)):
                        address: str = link["href"].strip()
                        description: str = link.text.strip().replace("|", "{{!}}")
                        change.context += f"\n*[{address} {description}]"

            # handles attributes
            # attribute is from a champion ability
            elif content.has_attr("class") and "ability-title" in content["class"]:
                ability_info: str = content.text.strip()

                if any(x["name"] == change.name for x in Dragon.champions):
                    
                    # gets a substring that contains only the ability name
                    result = Helper.try_match_ability_name(ability_info)
                    if result is None:
                        raise ParserError(self, f"Was not expecting ability name '{ability_info}'.")
                    
                    ability = Pai(ability_info[result.span()[0] + len(result.group(0)):])

                    if change.complex_changes is None:
                        change.abilities.append(ability)
                        continue

                    # complex changes goes elsewhere
                    change.complex_changes[-1].abilities.append(ability)

                else:
                    inner_change = Pnb(ability_info)
                    change.changes.append(inner_change)

            # handle base stats attributes
            elif content.has_attr("class") and ability is None and "change-detail-title" in content["class"]:
                ability = Pai(content.text.strip())
                change.abilities.append(ability)

            # handles attribute changes
            elif content.has_attr("class") and "attribute-change" in content["class"]:
                attribute: 'Pbc | None' = None
                
                # loop through all the attributes that changed
                for attribute_info in Filters.tags_with_classes(list(content.children)):
                    if "attribute" in attribute_info["class"]:
                        attribute = Pbc(attribute_info.find(text=True, recursive=False).strip())

                        # gets the attribute status
                        for tag in Filters.tags_with_classes(list(attribute_info.children)):
                            if "new" in tag["class"]:
                                attribute.status = "new"
                                break
                            elif "removed" in tag["class"]:
                                attribute.status = "removed"
                                break
                            elif "updated" in tag["class"]:
                                attribute.status = "updated"
                                break

                    # handles previous attribute value and attribute removed text
                    elif "attribute-before" in attribute_info["class"]\
                        or "attribute-removed" in attribute_info["class"]:
                        if attribute is None:
                            raise ParserError(self, "Field 'attribute' was not defined.")
                        attribute.before = attribute_info.text.strip()

                    # handles new attribute value
                    elif "attribute-after" in attribute_info["class"]:
                        if attribute is None:
                            raise ParserError(self, "Field 'attribute' was not defined.")
                        attribute.after = attribute_info.text.strip()

                    # when champion updates are nested into other changes
                    elif "ability-title" in attribute_info["class"]:
                        ability_info: str = attribute_info.text.strip()

                        # gets a substring that contains only the ability name
                        result = Helper.try_match_ability_name(ability_info)
                        if result is not None:
                            inner_ability = Pai(ability_info[result.span()[0] + len(result.group(0)):])

                            if inner_change is not None:
                                inner_change.abilities.append(inner_ability)
                            else:
                                raise ParserError(self, "Field 'inner_change' was not defined.")
            
                # attribute is from an ability
                if ability is not None and attribute is not None:
                    ability.attributes.append(attribute)

                # attribute is from some inner change
                elif inner_change is not None and attribute is not None:
                    inner_change.attributes.append(attribute)

                # attribute is from a champion
                elif attribute is not None:
                    if change.complex_changes is None:
                        change.attributes.append(attribute)
                        continue

                    # complex changes goes elsewhere
                    change.complex_changes[-1].attributes.append(attribute)

        # for these, the border is empty
        border = Border()
        border.changes.append(change)
        section.borders.append(border)

    def midpatch(self, border: 'Border | None', section: Section, content_list: 'list[Tag]') -> None:
        change: 'Pnb | None' = None
        ability: 'Pai | None' = None

        # loop through all the mid-patch updates
        for content in content_list:
            if content.has_attr("class") and "change-title" in content["class"]:
                # border is not defined or its title is
                # different from the current border title
                if border is None or border.title != content.text.strip():
                    border = Border(content.text.strip())
                    section.borders.append(border)
                    continue

            if border is None:
                # border title is sometimes defined in an h2 tag
                h2: 'Tag | None' = Filters.first_tag_by_name("h2", content_list)
                if h2 is None:
                    raise ParserError(self, "Could not locate the border title.")

                border = Border(h2.text.strip())
                section.borders.append(border)

            # border context text
            if content.has_attr("class") and "context" in content["class"]:
                border.context = content.text.strip()

            # attribute is from a champion ability
            elif content.has_attr("class") and "ability-title" in content["class"]:
                change = Pnb(content.text.strip())
                
                # simplified borders don't have changes
                if not border.simplified:
                    border.changes.append(change)

            # handles champion or item attribute change
            elif content.has_attr("class") and "attribute-change" in content["class"]:
                attribute: 'Pbc | None' = None
                if change is None: raise ParserError(self, 'HTML node with class="attribute-change" found '
                                                    'before the first "ability-title" was defined.')

                # get all the properties of the current attribute
                for attribute_tag in Filters.tags_with_classes(list(content.children)):
                    if "context" in attribute_tag["class"]:
                        change.context = attribute_tag.text.strip()

                    elif "attribute" in attribute_tag["class"]:

                        # handles simplified mid patch changes
                        if change is None:
                            border.simplified = True
                                
                        attribute_info: str = Helper.capitalize(attribute_tag.text.strip())

                        # the current change reffers to a champion
                        if change is not None and any(x["name"] == change.name for x in Dragon.champions):

                            # attribute is from an ability
                            result = Helper.try_match_ability_name(attribute_info)
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
                        elif change is not None and any(x["name"] == change.name for x in Dragon.items):
                            attribute = Pbc(attribute_info)
                            change.attributes.append(attribute)
                        
                        else:
                            # handle as simplified list
                            if border is None or border.context and border.context != change.name:
                                border = Border(context=change.name, simplified=True)
                                section.borders.append(border)
                            
                            # reuse existing border
                            elif change is not None and border.context != change.name:
                                border.context = change.name
                                border.simplified = True
                                border.changes = []

                            # create simplified attribute
                            attribute = Pbc(attribute_info)
                            border.attributes.append(attribute)

                    elif attribute is None:
                        raise ParserError(self, f"Field 'attribute' for {change.name} was not defined.")

                    # handle previous attribute value and "attribute removed" text
                    elif any(x in attribute_tag["class"] for x in ["attribute-before", "attribute-removed"]):
                        attribute.before = attribute_tag.text.strip()

                    # handle new attribute value
                    elif "attribute-after" in attribute_tag["class"]:
                        attribute.after = attribute_tag.text.strip()

            # reset values at the end of a change
            elif content.has_attr("class") and "divider" in content["class"]:
                change = None
                ability = None

    def parse_all(self, patch_version: str) -> 'PatchNotes':
        self.patch_version = patch_version
        self.patch_url = RIOT_ADDRESS.format(self.patch_version.replace('.', '-'))
        response = HttpClient.get(self.patch_url)

        # something went wrong
        if not response.status_code == 200:
            # TODO: Try trice and then report
            raise ParserHttpError(self, "Expected response of type `HTTP 200`, "
                                f"but got back `HTTP {response.status_code}`.")

        # assert dragon is loaded
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
            designer = Designer(Helper.capitalize(designer_span.text.strip()))
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
                section = Section(section_id, Helper.capitalize(tag.text.strip()))
                self.sections.append(section)
                section_id += 1
                border = None
            
            # section content
            elif "content-border" in tag["class"]:
                if section is None:
                    raise ParserError(self, 'HTML node with `class="content-border"` '
                                    'found before the `"header-primary"` was defined.')
                content_list: 'list[Tag]' = Filters.tags(list(tag.div.div.children))

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

                # handles ARAM changes
                elif section.title == "ARAM Balance Changes":
                    self._aram(border, section, content_list)

                # handles future skins and chromas
                elif section.title == "Upcoming Skins & Chromas":
                    border = Border()
                    section.borders.append(border)
                    border_context = list(Filters.tags_by_class("summary", content_list))

                    if len(border_context) > 0:
                        border.context = border_context[0].text.strip()

                    # loop through all the skin containers
                    for skin_container in Filters.tags_by_class("gs-container", content_list):

                        # loop through all the skins inside the container
                        for skin in Filters.tags_by_class("skin-box", list(skin_container.children)):
                            border.skins.append(SplashTableEntry(skin.h4.text.strip()))

                # handle pretty printed changes    
                elif any("attribute-change" in x["class"] for x in Filters.tags_with_classes(content_list)):
                    self._changes(border, section, content_list)

                else:
                    # most likely plain text boxes
                    border = Border(simplified=True)
                    section.borders.append(border)

                    # adds the context to the border
                    border_context = list(Filters.tags_by_class("context", content_list))
                    if len(border_context) > 0:
                        border.context = f"{border_context[0].text.strip()}\n"

                    # handles lists inside the block
                    for items_list in Filters.tags_by_name("ul", content_list):
                        # TODO: fix <strong> not being captured
                        # appends the items from the list to the context
                        for item in Filters.tags_by_name("li", list(items_list.children)):
                            text: str = item.text.strip().replace("<strong>", "'''").replace("</strong>", "'''")
                            border.context += f"*{text}\n"

                    # handles attribute changes
                    for content_info in Filters.tags_with_classes(content_list):
                        if "attribute-change" in content_info["class"]:
                            attribute: Pbc = Pbc()
                            border.attributes.append(attribute)

                            # loop through the properties of the current attribute
                            for attribute_info in Filters.tags(list(content_info.children)):
                                
                                # handle previous attribute value
                                if "attribute-before" in attribute_info["class"]:
                                    attribute.before = attribute_info.text.strip()
                                
                                # handle new attribute value
                                elif "attribute-after" in attribute_info["class"]:
                                    attribute.after = attribute_info.text.strip()
                
                                # sets the name of the attribute
                                elif "attribute" in attribute_info["class"]:
                                    attribute.name = attribute_info.text.strip()

        try:
            # parse and save to wiki
            self._print()
            return self
        except HttpClient.ReadTimeout:
            raise ParserTimeoutError(self, "Whoops, the site is taking too long to respond, try again later.")
