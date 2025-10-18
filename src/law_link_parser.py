from typing import List
import re

import pymorphy3
from .models import LawLink, RawLawLink


def normalize_input_text(morph: pymorphy3.MorphAnalyzer, input_text_corpus: str) -> str:
    """Convert all words to normal form with pymorphy"""
    normalized_text = " ".join(
        morph.parse(word.strip())[0].normal_form
        for word in input_text_corpus.replace("\n", " ").split()
    )
    normalized_text = (
        normalized_text.replace("»", '"')
        .replace("«", '"')
        .replace("ё", "е")
        .replace("e", "е")
        .replace("a", "а")
        .replace("c", "с")
        .replace("'", '"')
    )
    return normalized_text


def extract_raw_links(input_text_corpus: str) -> List[RawLawLink]:
    patterns = {
        "article": r"(?:ст\.|статья|в статья)\s*(\d+[\.\d]*)\s*",
        "law_source": r"(.*?)(?=\s*(?:ст\.|статья|п\.|пп\.|подпункт|в статья|$))",
        "point_article": r"в*\s*(?:\sп\.|пункт|пунт|часть)\s*([\.\dа-я]+),*\s*",
        # Pattern to identify many points
        "many_point_article": r"\s*(?:пункт|п\.)\s*((?:[а-яa-z]|\d+[\.\d]*)(?:\s*,\s*(?:[а-яa-z]|\d+[\.\d]*))*(?:\s*и\s*(?:[а-яa-z]|\d+[\.\d]*))?)\s*",
        "subpoint_article": r"\s*(?:пп\.|подпункт)\s*([\.\d]+)",
        # Pattern to identify many subpoints
        "many_subpoint_article": r"(?:подпункт|пп\.)\s*([а-яa-z\d](?:\s*,\s*[а-яa-z\d])*(?:\s*и\s*[а-яa-z\d])?)",
    }
    # which patterns to combine and how
    patterns_combinations = [
        ("many_subpoint_article", "point_article", "article", "law_source"),
        ("many_subpoint_article", "many_point_article", "article", "law_source"),
        ("subpoint_article", "point_article", "article", "law_source"),
        ("point_article", "article", "law_source"),
        ("article", "law_source"),
        ("point_article", "law_source"),
    ]

    found_links: list[RawLawLink] = []

    # iteratively extract substrings using patterns
    for combination in patterns_combinations:
        combination_found_links = []
        combination_pattern = re.compile(
            "".join(patterns[item] for item in combination)
        )
        for found_list_of_items in combination_pattern.findall(input_text_corpus):
            link = RawLawLink(
                **{
                    item_name.replace("many_", ""): item
                    for item, item_name in zip(found_list_of_items, combination)
                }
            )
            combination_found_links.append(link)
        # Append only new links. Link is new if any field is new or None
        for new_link in combination_found_links:
            link_exists = False
            for old_link in found_links:
                link_exists = all(
                    getattr(new_link, field_name) == getattr(old_link, field_name)
                    or getattr(new_link, field_name) is None
                    for field_name in RawLawLink().__pydantic_fields__.keys()
                )
                if link_exists:
                    break
            if not link_exists:
                found_links.append(new_link)

    return found_links


def extract_list_of_items_from_string(input_string: str) -> List[str]:
    """Function to convert string like '1, 2 и 3' to ['1', '2', '3']"""

    output_list_of_items = []
    for substr in input_string.split(","):
        for item in substr.strip().split():
            clear_item = item.strip()
            if clear_item != "и":
                output_list_of_items.append(clear_item)
    return output_list_of_items


def process_raw_links(
    links: list[RawLawLink], law_alias_to_id: dict[str, str]
) -> List[LawLink]:
    """Function generates from RawLawLink LawLink objects"""

    processed_links: list[LawLink] = []
    for link in links:
        if link.law_source is not None:
            link_source = re.sub(r"\s+", " ", link.law_source)
            if link_source and link_source in law_alias_to_id:
                # easy check - if link source is in dict -> add id
                law_id = law_alias_to_id[link_source]
            else:
                # case when real link source can't be identified, trying to understand,
                # maybe found source startswith the real law alias (we expect it after regexp)
                law_id = -1
                for law_alias, current_law_id in law_alias_to_id.items():
                    if link_source.startswith(law_alias) or (
                        "федеральный " + link_source
                    ).startswith(law_alias):
                        law_id = current_law_id
                        break

            if law_id != -1:
                if link.subpoint_article is not None:
                    subpoint_articles = extract_list_of_items_from_string(
                        link.subpoint_article
                    )
                else:
                    subpoint_articles = [None]
                if link.point_article is not None:
                    point_articles = extract_list_of_items_from_string(
                        link.point_article
                    )
                else:
                    point_articles = [None]

                # Generate new object for every point and subpoint
                for point_article in point_articles:
                    for subpoint_article in subpoint_articles:
                        link = LawLink(
                            law_id=law_id,
                            article=link.article,
                            point_article=point_article,
                            subpoint_article=subpoint_article,
                        )
                        if link not in processed_links:
                            processed_links.append(link)
    return processed_links
