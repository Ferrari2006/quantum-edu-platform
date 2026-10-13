import unittest
from unittest.mock import MagicMock, patch

from backend.api.routes import rag_index_status


class IndexStatusTests(unittest.TestCase):
    @patch('backend.api.routes.VectorStore')
    @patch('backend.api.routes.settings')
    def test_missing_index_does_not_create_database(self, settings, store):
        settings.vector_store_path.exists.return_value = False
        settings.embedding_model = 'hashing'
        settings.retrieval_mode = 'hybrid'
        result = rag_index_status()
        self.assertEqual(result['indexed_chunks'], 0)
        self.assertFalse(result['ready'])
        store.assert_not_called()

    @patch('backend.api.routes.VectorStore')
    @patch('backend.api.routes.settings')
    def test_index_status_omits_filesystem_paths(self, settings, store):
        settings.vector_store_path.exists.return_value = True
        settings.embedding_model = 'hashing'
        settings.retrieval_mode = 'hybrid'
        store.return_value.stats.return_value = {'chunks': 289, 'path': 'private-path'}
        result = rag_index_status()
        self.assertTrue(result['ready'])
        self.assertEqual(result['indexed_chunks'], 289)
        self.assertNotIn('path', result)


if __name__ == '__main__':
    unittest.main()
