import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.rag.chain import answer
from backend.rag.chunking import chunk_document
from backend.rag.llm import LLMClient
from backend.rag.retriever import retrieve
from backend.rag.schema import Chunk, RetrievedChunk, SourceDocument


class _FakeCompletions:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Grover 提供平方级查询加速 [1]。"))]
        )


class _FakeOpenAIClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=_FakeCompletions())


class _FakeLLM:
    def generate(self, query, contexts):
        self.query = query
        self.contexts = contexts
        return "基于课程文档的回答 [1]。"


class RagPipelineTests(unittest.TestCase):
    def test_markdown_chunking_removes_frontmatter_and_splits_long_sections(self):
        document = SourceDocument(doc_id="example.md", path="example.md", title="Example")
        text = "---\ntitle: Example\n---\n\n# First\n\n" + ("alpha " * 80) + "\n\n# Second\n\nbeta"

        chunks = chunk_document(document, text, max_chars=200)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertNotIn("title: Example", chunks[0].text)
        self.assertTrue(chunks[0].chunk_id.endswith("#chunk-0"))
        self.assertTrue(all(len(chunk.text) <= 200 for chunk in chunks))

    def test_local_retrieval_finds_grover_document(self):
        contexts = retrieve("Grover search oracle")

        self.assertTrue(contexts)
        self.assertEqual(contexts[0].retrieval_method, "lexical")
        self.assertIn("grover_overview.md", contexts[0].chunk.doc_id)

    def test_llm_client_builds_grounded_chat_request(self):
        fake_client = _FakeOpenAIClient()
        llm = LLMClient(client=fake_client, model="test-model")
        context = RetrievedChunk(
            chunk=Chunk(
                chunk_id="grover.md#chunk-0",
                doc_id="grover.md",
                text="Grover uses an oracle and diffusion.",
                source="grover.md",
                title="Grover",
            ),
            score=3.0,
            retrieval_method="lexical",
        )

        result = llm.generate("What is Grover search?", [context])

        self.assertIn("[1]", result)
        request = fake_client.chat.completions.kwargs
        self.assertEqual(request["model"], "test-model")
        self.assertIn("grover.md", request["messages"][1]["content"])

    def test_answer_returns_citations_from_retrieved_chunks(self):
        context = RetrievedChunk(
            chunk=Chunk(
                chunk_id="grover.md#chunk-0",
                doc_id="grover.md",
                text="Grover context",
                source="grover.md",
                title="Grover",
            ),
            score=2.0,
            retrieval_method="lexical",
        )
        with patch("backend.rag.chain.retrieve", return_value=[context]):
            result = answer("Grover?", llm_client=_FakeLLM())

        self.assertEqual(result["citations"][0]["chunk_id"], "grover.md#chunk-0")
        self.assertEqual(result["confidence"], "medium")


if __name__ == "__main__":
    unittest.main()
