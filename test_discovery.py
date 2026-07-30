import unittest

from collect_matches import discover_pages
from liquipedia_client import LiquipediaClient


PREFIXES = {
    "BLAST": ("BLAST/",),
    "ESL/IEM": ("ESL/", "Intel_Extreme_Masters/"),
    "PGL": ("PGL/",),
    "CCT": ("CCT/",),
    "Circuit X": ("Circuit_X/", "Circuit_Stars/"),
}


class FakeClient:
    def __init__(self, pages, rendered_links=None):
        self.pages = pages
        self.rendered_links = rendered_links or {}
        self.parser = LiquipediaClient()

    def get_page_content(self, page_title):
        return self.pages.get(page_title)

    def get_page_links(self, page_title):
        return self.rendered_links.get(page_title, [])

    def extract_candidate_pages(self, wikitext):
        return self.parser.extract_candidate_pages(wikitext)

    def filter_organizer_pages(self, pages, prefixes, years_back=1):
        return self.parser.filter_organizer_pages(pages, prefixes, years_back)

    def has_match_content(self, wikitext):
        return self.parser.has_match_content(wikitext)


class DiscoveryTests(unittest.TestCase):
    def test_extracts_template_catalog_entries(self):
        client = LiquipediaClient()
        text = """
        **BLAST/Bounty/2026/Summer|BLAST Bounty Summer 2026|iconfile=x.png
        **BLAST/Bounty/2026/Summer/Qualifier|BLAST Bounty Summer Qual|iconfile=x.png
        """
        self.assertEqual(
            client.extract_candidate_pages(text),
            [
                "BLAST/Bounty/2026/Summer",
                "BLAST/Bounty/2026/Summer/Qualifier",
            ],
        )

    def test_filters_supported_organizers_and_recent_years(self):
        client = LiquipediaClient()
        candidates = [
            "BLAST/Bounty/2026/Summer",
            "Intel_Extreme_Masters/2026/Atlanta",
            "PGL/2026/Astana",
            "CCT/2026/Europe/Series_5",
            "Circuit_X/2026/Finals",
            "Other_Event/2026/Summer",
            "BLAST/Bounty/2022/Spring",
        ]
        result = client.filter_organizer_pages(candidates, PREFIXES, years_back=1)
        self.assertNotIn("Other_Event/2026/Summer", result)
        self.assertNotIn("BLAST/Bounty/2022/Spring", result)
        self.assertIn("BLAST/Bounty/2026/Summer", result)
        self.assertIn("Circuit_X/2026/Finals", result)

    def test_discovers_bounty_and_qualifier_from_catalog(self):
        match = "{{Match|opponent1=A|opponent2=B|date=July 1, 2026}}"
        pages = {
            "Liquipedia:Tournaments": """
                **BLAST/Bounty/2026/Summer|BLAST Bounty Summer
                **BLAST/Bounty/2026/Summer/Qualifier|Qualifier
                **Unrelated/2026/Event|Ignored
            """,
            "BLAST/Bounty/2026/Summer": match,
            "BLAST/Bounty/2026/Summer/Qualifier": match,
        }
        result = discover_pages(
            FakeClient(pages),
            initial_pages=[],
            catalog_pages=["Liquipedia:Tournaments"],
            rendered_catalog_pages=[],
            organizer_prefixes=PREFIXES,
        )
        self.assertEqual(
            result,
            [
                "BLAST/Bounty/2026/Summer",
                "BLAST/Bounty/2026/Summer/Qualifier",
            ],
        )

    def test_discovers_cct_from_rendered_portal(self):
        match = "{{Match|opponent1=A|opponent2=B|date=July 1, 2026}}"
        page = "CCT/2026/Europe/Series_5"
        client = FakeClient(
            {page: match},
            {"Portal:Tournaments": [page, "Unrelated/2026/Event"]},
        )
        result = discover_pages(
            client,
            initial_pages=[],
            catalog_pages=[],
            rendered_catalog_pages=["Portal:Tournaments"],
            organizer_prefixes=PREFIXES,
        )
        self.assertEqual(result, [page])


if __name__ == "__main__":
    unittest.main()
