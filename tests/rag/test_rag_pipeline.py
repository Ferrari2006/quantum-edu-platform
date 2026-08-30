import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import backend.db as database
from backend.rag.chain import answer
from backend.rag.chunking import chunk_document
from backend.rag.domain_tools import analyze_qiskit_code
from backend.rag.llm import LLMClient
from backend.rag.reranker import rerank
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
    def generate(self, query, contexts, memories=None, route="concept", task_context=None):
        self.query = query
        self.contexts = contexts
        return "基于课程文档的回答 [1]。"


class _RepairingFakeLLM:
    def generate(self, query, contexts, memories=None, route="concept", task_context=None):
        return "这个初稿没有引用，需要被审查智能体退回修正。"

    def revise(
        self,
        query,
        answer,
        contexts,
        issues,
        memories=None,
        route="concept",
        task_context=None,
    ):
        self.issues = issues
        return "修正后，Grover 算法使用 oracle 与扩散算子 [1]。"


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
        self.assertIn("lexical", contexts[0].retrieval_method)
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
        self.assertEqual(
            [step["agent"] for step in result["agent_trace"]],
            ["retrieval", "validation", "generation", "review"],
        )

    def test_review_agent_triggers_one_correction_pass(self):
        context = RetrievedChunk(
            chunk=Chunk(
                chunk_id="grover.md#chunk-0",
                doc_id="grover.md",
                text="Grover uses an oracle and diffusion operator.",
                source="qiskit-official",
                title="Grover",
            ),
            score=2.0,
            retrieval_method="lexical",
        )
        fake_llm = _RepairingFakeLLM()
        with patch("backend.rag.chain.retrieve", return_value=[context]):
            result = answer("Grover?", llm_client=fake_llm)

        self.assertIn("missing_valid_citation", fake_llm.issues)
        self.assertEqual(result["review"]["status"], "passed")
        self.assertEqual(result["review"]["attempts"], 2)
        self.assertIn("correction", [step["agent"] for step in result["agent_trace"]])

    def test_reranker_uses_source_authority_and_deduplicates(self):
        community = RetrievedChunk(
            chunk=Chunk(
                chunk_id="community#1",
                doc_id="community.md",
                text="Grover search overview from a community note.",
                source="community",
            ),
            score=1.0,
            retrieval_method="lexical",
        )
        official = RetrievedChunk(
            chunk=Chunk(
                chunk_id="official#1",
                doc_id="qiskit-official.md",
                text="Grover search uses amplitude amplification.",
                source="IBM Quantum official Qiskit documentation",
            ),
            score=1.0,
            retrieval_method="lexical",
        )
        duplicate = RetrievedChunk(
            chunk=Chunk(
                chunk_id="community#2",
                doc_id="copy.md",
                text="Grover search overview from a community note.",
                source="copy",
            ),
            score=0.8,
            retrieval_method="lexical",
        )

        ranked = rerank("Grover search", [community, official, duplicate], top_k=3)

        self.assertEqual(ranked[0].chunk.chunk_id, "official#1")
        self.assertEqual(len(ranked), 2)
        self.assertTrue(all("validated" in item.retrieval_method for item in ranked))

    def test_qiskit_static_analysis_never_executes_and_flags_bad_index(self):
        analysis = analyze_qiskit_code(
            "from qiskit import QuantumCircuit\nqc = QuantumCircuit(2)\nqc.h(3)"
        )

        self.assertFalse(analysis["execution_performed"])
        self.assertIn(
            "qubit_index_out_of_range",
            [item["code"] for item in analysis["diagnostics"]],
        )

    def test_session_history_round_trip(self):
        original_path = database.DB_PATH
        try:
            with TemporaryDirectory() as directory:
                database.DB_PATH = Path(directory) / "test-platform.db"
                database.init_db()
                database.record_qa(
                    None,
                    "什么是量子叠加？",
                    "量子叠加回答 [1]。",
                    "concept",
                    session_id="guest-session-123",
                    review_status="passed",
                    metadata={"confidence": "medium"},
                )

                history = database.list_qa_history("guest-session-123")

                self.assertEqual(len(history), 1)
                self.assertEqual(history[0]["review_status"], "passed")
                self.assertEqual(history[0]["metadata"]["confidence"], "medium")
                self.assertEqual(database.clear_qa_history("guest-session-123"), 1)
                self.assertEqual(database.list_qa_history("guest-session-123"), [])
        finally:
            database.DB_PATH = original_path


if __name__ == "__main__":
    unittest.main()
