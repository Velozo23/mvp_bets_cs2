import unittest

from event_context import event_context_from_page, match_stage, parse_match_datetime


class EventContextTests(unittest.TestCase):
    def test_extracts_numbered_stage(self):
        self.assertEqual(
            event_context_from_page(
                "Intel_Extreme_Masters/2026/Cologne/Stage_1"
            ),
            ("IEM Cologne Major 2026", "Stage 1"),
        )

    def test_extracts_playoffs(self):
        self.assertEqual(
            event_context_from_page(
                "Intel_Extreme_Masters/2026/Cologne/Playoffs"
            ),
            ("IEM Cologne Major 2026", "Playoffs"),
        )

    def test_keeps_season_as_part_of_event_name(self):
        self.assertEqual(
            event_context_from_page("BLAST/Open/2026/Spring"),
            ("BLAST Open Rotterdam 2026", None),
        )

    def test_handles_simple_event(self):
        self.assertEqual(
            event_context_from_page("CS_Asia_Championships/2026"),
            ("CS Asia Championships 2026", None),
        )

    def test_parses_cest_datetime(self):
        result = parse_match_datetime(
            "March 29, 2026 - 12:30 {{Abbr/CEST}}"
        )
        self.assertEqual(result.isoformat(), "2026-03-29T12:30:00+02:00")

    def test_uses_china_offset_for_liquipedia_cst(self):
        result = parse_match_datetime(
            "May 20, 2026 - 14:30 {{Abbr/CST}}"
        )
        self.assertEqual(result.isoformat(), "2026-05-20T14:30:00+08:00")

    def test_identifies_iem_showmatch(self):
        self.assertEqual(
            match_stage(
                "IEM Cologne Major 2026", None, "germany", "poland", None
            ),
            "Showmatch",
        )

    def test_identifies_blast_grand_final(self):
        date = parse_match_datetime(
            "March 29, 2026 - 12:30 {{Abbr/CEST}}"
        )
        self.assertEqual(
            match_stage(
                "BLAST Open Rotterdam 2026", None, "navi", "vit", date
            ),
            "Grand Final",
        )


if __name__ == "__main__":
    unittest.main()
