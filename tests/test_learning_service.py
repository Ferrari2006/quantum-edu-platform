import tempfile
import unittest
from pathlib import Path

import backend.db as db
from backend.learning.service import (
    build_learning_profile,
    get_learning_timeline,
    get_recommendations,
    submit_learning_event,
)

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from backend.api.learning_routes import router as learning_router
except ModuleNotFoundError:
    FastAPI = None
    TestClient = None
    learning_router = None


class LearningServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = db.DB_PATH
        db.DB_PATH = Path(self.temp_dir.name) / "learning-test.db"
        db.init_db()
        self.user = db.create_user("learner", "password123")
        self.token, _session = db.create_session(self.user["id"])
        self.client = None
        if FastAPI and TestClient and learning_router:
            app = FastAPI()
            app.include_router(learning_router, prefix="/api")
            self.client = TestClient(app)
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        db.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_article_completion_creates_mastery(self):
        event = submit_learning_event(
            self.user["id"],
            "superposition",
            "article_completed",
            "knowledge_base",
            0.72,
            idempotency_key="article:superposition:complete",
        )

        self.assertTrue(event["created"])
        self.assertAlmostEqual(event["mastery"]["mastery_score"], 0.72)
        self.assertEqual(event["mastery"]["evidence_count"], 1)

    def test_idempotency_prevents_duplicate_progress(self):
        for _ in range(2):
            last_event = submit_learning_event(
                self.user["id"],
                "measurement",
                "article_completed",
                "knowledge_base",
                0.68,
                idempotency_key="article:measurement:complete",
            )

        profile = build_learning_profile(self.user["id"])
        measurement = next(
            item for item in profile["concepts"] if item["concept_id"] == "measurement"
        )
        self.assertFalse(last_event["created"])
        self.assertEqual(measurement["evidence_count"], 1)

    def test_lab_evidence_is_combined_with_article_evidence(self):
        submit_learning_event(
            self.user["id"],
            "bell-state",
            "article_completed",
            "knowledge_base",
            0.5,
        )
        submit_learning_event(
            self.user["id"],
            "bell-state",
            "lab_completed",
            "quantum_lab",
            1.0,
        )

        profile = build_learning_profile(self.user["id"])
        bell = next(
            item for item in profile["concepts"] if item["concept_id"] == "bell-state"
        )
        expected = (0.5 * 0.8 + 1.0 * 1.0) / 1.8
        self.assertAlmostEqual(bell["mastery_score"], expected)
        self.assertEqual(bell["evidence_count"], 2)

    def test_recommendations_prioritize_weak_concepts(self):
        submit_learning_event(
            self.user["id"],
            "superposition",
            "lab_completed",
            "quantum_lab",
            0.4,
        )

        result = get_recommendations(self.user["id"], limit=3)

        self.assertEqual(result["items"][0]["concept_id"], "superposition")
        self.assertIn("40%", result["items"][0]["reason"])
        self.assertEqual(result["items"][0]["actions"][1]["path"], "/lab")
        self.assertEqual(len(result["items"]), 3)

    def test_prerequisites_unlock_next_concept(self):
        submit_learning_event(
            self.user["id"],
            "what-is-quantum-computing",
            "quiz_attempt",
            "knowledge_quiz",
            0.9,
        )

        result = get_recommendations(self.user["id"], limit=4)
        classical = next(
            item
            for item in result["items"]
            if item["concept_id"] == "classical-bit-and-qubit"
        )
        self.assertTrue(classical["ready"])
        self.assertIn("前置概念", classical["reason"])

    def test_profile_summarizes_evidence_and_mastery_levels(self):
        submit_learning_event(
            self.user["id"],
            "measurement",
            "quiz_attempt",
            "knowledge_quiz",
            0.3,
        )
        profile = build_learning_profile(self.user["id"])

        self.assertEqual(profile["summary"]["total_evidence"], 1)
        self.assertEqual(profile["summary"]["needs_review_concepts"], 1)
        self.assertEqual(profile["concepts"][0]["mastery_level"], "needs_review")

        timeline = get_learning_timeline(self.user["id"])
        self.assertEqual(timeline["items"][0]["concept_title"], "测量：从概率到结果")

    def test_invalid_event_type_is_rejected(self):
        with self.assertRaises(ValueError):
            submit_learning_event(
                self.user["id"],
                "superposition",
                "invented_event",
                "test",
                1.0,
            )

    @unittest.skipIf(FastAPI is None, "FastAPI is not installed in the test runtime")
    def test_authenticated_learning_api_roundtrip(self):
        response = self.client.post(
            "/api/learning/events",
            headers=self.headers,
            json={
                "concept_id": "measurement",
                "event_type": "quiz_attempt",
                "source": "knowledge_quiz",
                "score": 0.9,
                "metadata": {"correct": True},
            },
        )

        self.assertEqual(response.status_code, 201)
        mastery = self.client.get("/api/learning/mastery", headers=self.headers)
        recommendations = self.client.get(
            "/api/learning/recommendations?limit=2",
            headers=self.headers,
        )
        self.assertEqual(mastery.status_code, 200)
        self.assertEqual(mastery.json()["summary"]["covered_concepts"], 1)
        self.assertEqual(len(recommendations.json()["items"]), 2)

    @unittest.skipIf(FastAPI is None, "FastAPI is not installed in the test runtime")
    def test_learning_api_requires_login(self):
        response = self.client.get("/api/learning/mastery")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
