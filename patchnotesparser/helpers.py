from typing import Any
from bs4 import Tag
import re as Regex


EXCEPTIONS: 'list[str]' = ["and", "or", "the", "a", "of", "in", "ARAM", "DX11", "DX9", "QoL", "In-Game", "Mid-Patch"]


class Helper:
    @staticmethod
    def capitalize(text: str) -> str:
        words: 'list[str]' = Regex.split(r"( |\"|/)", text)
        lowered_words: 'list[str]' = [word if word in EXCEPTIONS else word.lower() for word in words]
        final_words: 'list[str]' = [word if word in EXCEPTIONS else word.capitalize() for word in lowered_words]
        return "".join(final_words)

    @staticmethod
    def try_match_ability_name(text: str) -> 'Regex.Match[str] | None':
        return Regex.search(r"([QWER]|(PASSIVE))\s-\s", text, Regex.IGNORECASE)


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
    def first_tag_by_name(class_name: str, array: 'list[Tag]') -> 'Tag | None':
        tags: 'list[Tag]' = Filters.tags_by_name(class_name, array)
        return (tags[0] if len(tags) > 0 else None)

    @staticmethod
    def tags_by_class(class_name: str, array: 'list[Tag]') -> 'list[Tag]':
        return list(filter(lambda tag: class_name in tag["class"], Filters.tags_with_classes(array)))
