from mwrogue.esports_client import EsportsClient
import requests as HttpClient
from typing import Any
import os.path as Path
from bs4 import Tag
import re as Regex
import os as OS


class StringHelper:
    EXCEPTIONS: 'list[str]' = ["and", "or", "the", "a", "of", "in", "ARAM", "DX11", "DX9", "QoL", "In-Game", "Mid-Patch"]

    def capitalize(self, text: str) -> str:
        words: 'list[str]' = Regex.split(r"( |\"|/)", text)
        lowered_words: 'list[str]' = [word if word in self.EXCEPTIONS else word.lower() for word in words]
        final_words: 'list[str]' = [word if word in self.EXCEPTIONS else word.capitalize() for word in lowered_words]
        return "".join(final_words)

    def try_match_ability_name(self, text: str) -> 'Regex.Match[str] | None':
        return Regex.search(r"([QWER]|(PASSIVE))\s-\s", text, Regex.IGNORECASE)


class ImageHelper:
    def __init__(self, file_name: str) -> None:
        self.file_path: str = Path.join(Path.dirname(__file__), "data/images/", file_name)
        self.file_name: str = file_name
        self.url: str = ""
        
    def download(self, image_url: str) -> bool:
        response = HttpClient.get(image_url)
        self.url = image_url

        if response.ok:
            with open(self.file_path, "wb") as file:
                file.write(response.content)
            return True
        return False

    def upload(self, site: EsportsClient, address: str, summary: str, comment: str) -> bool:
        try:
            with open(self.file_path, "rb") as file:
                site.client.upload(file, filename=address, description=summary, comment=comment)
            return True
        except Exception as e:
            print(e)
            return False
        finally:
            OS.remove(self.file_path)


class Filters:
    @staticmethod
    def tags(array: 'list[Any]') -> 'list[Tag]':
        return list(filter(lambda tag: isinstance(tag, Tag), array))

    @staticmethod
    def tags_with_classes(array: 'list[Any]') -> 'list[Tag]':
        return list(filter(lambda tag: tag.has_attr("class"), Filters.tags(array)))

    @staticmethod
    def tags_by_name(tag_name: str, array: 'list[Tag]') -> 'list[Tag]':
        return list(filter(lambda tag: tag.name == tag_name, array))

    @staticmethod
    def first_tag_by_name(tag_name: str, array: 'list[Tag]') -> 'Tag | None':
        tags: 'list[Tag]' = Filters.tags_by_name(tag_name, array)
        return (tags[0] if len(tags) > 0 else None)

    @staticmethod
    def tags_by_class(class_name: str, array: 'list[Tag]') -> 'list[Tag]':
        return list(filter(lambda tag: class_name in tag["class"], Filters.tags_with_classes(array)))
