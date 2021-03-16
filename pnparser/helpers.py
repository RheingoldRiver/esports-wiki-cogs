import re as Regex
from bs4 import Tag

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Iterator
    from re import Match


EXCEPTIONS: 'list[str]' = ["and", "or", "the", "a", "of", "in", "ARAM", "QoL"]


class Helper:
    @staticmethod
    def capitalize(text: str) -> str:
        words: 'list[str]' = Regex.split(r"( |-|\"|/)", text)
        lowered_words: 'list[str]' = [word if word in EXCEPTIONS else word.lower() for word in words]
        print(lowered_words)
        final_words: 'list[str]' = [word if word in EXCEPTIONS else word.capitalize() for word in lowered_words]
        print(final_words)
        return "".join(final_words)

    @staticmethod
    def try_match_ability_name(text: str) -> 'Match[str] | None':
        return Regex.search(r"([QWER]|(PASSIVE))\s-\s", text, Regex.IGNORECASE)


class Filters:
    @staticmethod
    def tags(array: 'list[Any]') -> 'Iterator[Tag]':
        return filter(lambda tag: isinstance(tag, Tag), array)

    @staticmethod
    def tags_with_classes(array: 'list[Any]') -> 'Iterator[Tag]':
        return filter(lambda tag: tag.has_attr("class"), Filters.tags(array))

    @staticmethod
    def tags_by_name(tag_name: str, array: 'list[Tag]') -> 'Iterator[Tag]':
        return filter(lambda tag: tag.name == tag_name, array)

    @staticmethod
    def tags_by_class(class_name: str, array: 'list[Tag]') -> 'Iterator[Tag]':
        return filter(lambda tag: class_name in tag["class"], Filters.tags_with_classes(array))