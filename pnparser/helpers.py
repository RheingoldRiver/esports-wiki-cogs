import re as Regex
from bs4 import Tag

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Iterator


EXCEPTIONS: 'list[str]' = ["and", "or", "the", "a", "of", "in", "ARAM", "QoL"]

class Helper:
    @staticmethod
    def capitalize(text: str) -> str:
        words: 'list[str]' = Regex.split("( |-|\"|/)", text)
        final_words: 'list[str]' = [word if word in EXCEPTIONS else word.lower().capitalize() for word in words]
        return "".join(final_words)


class Filters:
    @staticmethod
    def tags(array: 'list[Any]') -> 'Iterator[Tag]':
        return filter(lambda tag: isinstance(tag, Tag), array)

    @staticmethod
    def tags_with_classes(array: 'list[Tag]') -> 'Iterator[Tag]':
        return filter(lambda tag: tag.has_attr("class"), array)

    @staticmethod
    def tags_by_name(tag_name: str, array: 'list[Tag]') -> 'Iterator[Tag]':
        return filter(lambda tag: tag.name == tag_name, array)

    @staticmethod
    def tags_by_class(class_name: str, array: 'list[Tag]') -> 'Iterator[Tag]':
        return filter(lambda tag: class_name in tag["class"], Filters.tags_with_classes(array))