import re as Regex


EXCEPTIONS: 'list[str]' = ["and", "or", "the", "a", "of", "in"]

class Helper:
    @staticmethod
    def capitalize(text: str) -> str:
        lower_case_words: 'list[str]' = Regex.split(" ", text.lower())
        final_words: 'list[str]' = [lower_case_words[0].capitalize()]
        final_words += [word if word in EXCEPTIONS else word.capitalize() for word in lower_case_words[1:]]
        return " ".join(final_words)
