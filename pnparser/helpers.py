import re as Regex
from bs4 import Tag

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Iterator


EXCEPTIONS: 'list[str]' = ["and", "or", "the", "a", "of", "in"]
UPPER_WORDS: 'list[str]' = ["aram"]

class Helper:
    @staticmethod
    def capitalize(text: str) -> str:
        lower_case_words: 'list[str]' = Regex.split(" ", text.lower())
        final_words: 'list[str]' = [word if word in EXCEPTIONS else Helper.__change_state(word) for word in lower_case_words]
        return " ".join(final_words)

    @staticmethod
    def __change_state(word: str) -> str:
        index: int = -1
        
        if '"' in word:
            index = word.index('"')
            word = word.replace('"', "")

        if word in UPPER_WORDS:
            word = word.upper()
        else:
            word = word.capitalize()

        if not index == -1:
            return word[:index] + '"' + word[index:]
        else:
            return word


class Filters:
    @staticmethod
    def tags(array: 'Iterator[Any]') -> 'Iterator[Tag]':
        return filter(lambda tag: isinstance(tag, Tag), array)

    @staticmethod
    def tags_by_name(tag_name: str, array: 'Iterator[Tag]') -> 'Iterator[Tag]':
        return filter(lambda tag: tag.name == tag_name, array)

    @staticmethod
    def tags_by_class(class_name: str, array: 'Iterator[Tag]') -> 'Iterator[Tag]':
        tags: 'Iterator[Tag]' = filter(lambda tag: tag.has_attr("class"), Filters.tags(array))
        return filter(lambda tag: class_name in tag["class"], tags)