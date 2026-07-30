import unittest

from sync_team_logos import (
    build_logo_lookup_wikitext,
    logo_extension,
    parse_logo_lookup_html,
)
from team_repository import normalize_team_name


SAMPLE_HTML = """
<div id="mvp-team-0">
  <span data-highlightingclass="Natus Vincere" class="team-template-team-icon">
    <span class="team-template-image-icon lightmode">
      <img src="/commons/images/navi-light.png">
    </span>
    <span class="team-template-image-icon darkmode">
      <a href="/counterstrike/Natus_Vincere">
        <img src="/commons/images/thumb/9/95/Navi.png/57px-Navi.png"
             srcset="/commons/images/thumb/9/95/Navi.png/85px-Navi.png 1.5x,
                     /commons/images/thumb/9/95/Navi.png/114px-Navi.png 2x">
      </a>
    </span>
  </span>
</div>
"""


class TeamLogoTests(unittest.TestCase):
    def test_normalizes_team_names(self):
        self.assertEqual(normalize_team_name("Natus Vincere"), "natus-vincere")
        self.assertEqual(normalize_team_name("MOUZ"), "mouz")

    def test_builds_safe_batched_lookup(self):
        result = build_logo_lookup_wikitext(["navi", "bad|template"])
        self.assertIn("{{TeamIcon|navi}}", result)
        self.assertNotIn("bad|template", result)

    def test_parses_dark_logo_and_canonical_name(self):
        logos = parse_logo_lookup_html(SAMPLE_HTML, ["navi"])
        self.assertEqual(len(logos), 1)
        self.assertEqual(logos[0].canonical_name, "Natus Vincere")
        self.assertEqual(logos[0].theme, "dark")
        self.assertTrue(logos[0].source_url.endswith("114px-Navi.png"))
        self.assertTrue(logos[0].liquipedia_page.endswith("/counterstrike/Natus_Vincere"))

    def test_detects_original_extension_from_thumbnail(self):
        url = "https://liquipedia.net/commons/images/thumb/9/95/Navi.png/114px-Navi.png"
        self.assertEqual(logo_extension(url, "image/png"), ".png")


if __name__ == "__main__":
    unittest.main()
