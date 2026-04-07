import tempfile
import unittest
from pathlib import Path

from md2word_agent.llm import KimiClient, MinimaxClient, ZhipuClient, create_json_client


class LLMFactoryTests(unittest.TestCase):
    def test_creates_moonshot_client(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("LLM_PROVIDER=moonshot\nMOONSHOT_API_KEY=test\n", encoding="utf-8")
            client = create_json_client(env_path=env_path)
            self.assertIsInstance(client, KimiClient)

    def test_creates_minimax_client(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("LLM_PROVIDER=minimax\nMINIMAX_API_KEY=test\n", encoding="utf-8")
            client = create_json_client(env_path=env_path)
            self.assertIsInstance(client, MinimaxClient)

    def test_creates_zhipu_client(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("LLM_PROVIDER=zhipu\nZHIPU_API_KEY=test\n", encoding="utf-8")
            client = create_json_client(env_path=env_path)
            self.assertIsInstance(client, ZhipuClient)


if __name__ == "__main__":
    unittest.main()
