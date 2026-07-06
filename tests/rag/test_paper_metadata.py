import unittest

from backend.rag.sources.arxiv import build_arxiv_id_url, normalize_arxiv_id, parse_arxiv_feed
from backend.rag.sources.openalex import parse_openalex_response
from backend.rag.sources.paper_metadata import PaperMetadata, paper_to_markdown


class PaperMetadataTests(unittest.TestCase):
    def test_paper_markdown_policy_mentions_no_pdf_download(self):
        paper = PaperMetadata(
            title="Bell states for learners",
            abstract="A short abstract.",
            authors=["Alice Example"],
            source="arXiv",
            source_url="https://arxiv.org/abs/0000.00000",
            arxiv_id="0000.00000",
        )

        markdown = paper_to_markdown(paper)

        self.assertIn("metadata and abstract text only", markdown)
        self.assertIn("Full-text PDF storage is not enabled", markdown)
        self.assertIn('decision: "approved_api_metadata"', markdown)

    def test_parse_arxiv_feed_metadata_only(self):
        payload = b"""<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
          <entry>
            <id>http://arxiv.org/abs/quant-ph/9605043v3</id>
            <updated>1996-07-08T00:00:00Z</updated>
            <published>1996-05-28T00:00:00Z</published>
            <title>A fast quantum mechanical algorithm for database search</title>
            <summary>Grover search abstract.</summary>
            <author><name>Lov K. Grover</name></author>
            <arxiv:primary_category term="quant-ph" />
            <category term="quant-ph" />
          </entry>
        </feed>
        """

        papers = parse_arxiv_feed(payload)

        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0].arxiv_id, "quant-ph/9605043v3")
        self.assertEqual(papers[0].primary_category, "quant-ph")
        self.assertEqual(papers[0].authors, ["Lov K. Grover"])

    def test_parse_openalex_abstract_inverted_index(self):
        payload = {
            "results": [
                {
                    "title": "Quantum Example",
                    "publication_year": 2024,
                    "ids": {"doi": "https://doi.org/10.123/example", "openalex": "W1"},
                    "authorships": [{"author": {"display_name": "Alice Example"}}],
                    "abstract_inverted_index": {"Quantum": [0], "works": [1]},
                    "open_access": {"is_oa": True},
                    "best_oa_location": {"license": "cc-by"},
                }
            ]
        }

        papers = parse_openalex_response(payload)

        self.assertEqual(papers[0].abstract, "Quantum works")
        self.assertEqual(papers[0].doi, "https://doi.org/10.123/example")
        self.assertEqual(papers[0].license, "cc-by")

    def test_arxiv_id_normalization(self):
        self.assertEqual(normalize_arxiv_id("arXiv:quant-ph/9605043"), "quant-ph/9605043")
        self.assertEqual(normalize_arxiv_id("https://arxiv.org/abs/1804.03719"), "1804.03719")
        self.assertEqual(normalize_arxiv_id("https://arxiv.org/pdf/1804.03719.pdf"), "1804.03719")

    def test_build_arxiv_id_url(self):
        url = build_arxiv_id_url(["https://arxiv.org/abs/1804.03719"])
        self.assertIn("id_list=1804.03719", url)


if __name__ == "__main__":
    unittest.main()
