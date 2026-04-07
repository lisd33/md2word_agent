import tempfile
import unittest
from pathlib import Path

from md2word_agent.llm import load_kimi_config, load_minimax_config, load_zhipu_config, resolve_provider


class LLMConfigTests(unittest.TestCase):
    def test_loads_kimi_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "LLM_PROVIDER=moonshot\nMOONSHOT_API_KEY=test-key\nMOONSHOT_BASE_URL=https://api.moonshot.ai/v1\nMOONSHOT_MODEL=kimi-k2.5\nMOONSHOT_TEMPERATURE=0\n",
                encoding="utf-8",
            )
            config = load_kimi_config(env_path)
            self.assertEqual(config.api_key, "test-key")
            self.assertEqual(config.model, "kimi-k2.5")
            self.assertEqual(config.temperature, 1.0)
            self.assertEqual(resolve_provider(env_path), "moonshot")

    def test_normalizes_kimi_k25_temperature_for_moonshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "LLM_PROVIDER=moonshot\nMOONSHOT_API_KEY=test-key\nMOONSHOT_MODEL=kimi-k2.5\nMOONSHOT_TEMPERATURE=0\n",
                encoding="utf-8",
            )
            config = load_kimi_config(env_path)
            self.assertEqual(config.temperature, 1.0)

    def test_loads_minimax_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "LLM_PROVIDER=minimax\nMINIMAX_API_KEY=test-minimax\nMINIMAX_BASE_URL=https://api.minimax.io/v1\nMINIMAX_MODEL=MiniMax-M2.5\nMINIMAX_TEMPERATURE=1.0\n",
                encoding="utf-8",
            )
            config = load_minimax_config(env_path)
            self.assertEqual(config.api_key, "test-minimax")
            self.assertEqual(config.model, "MiniMax-M2.5")
            self.assertEqual(config.temperature, 1.0)
            self.assertEqual(resolve_provider(env_path), "minimax")

    def test_loads_zhipu_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "LLM_PROVIDER=zhipu\nZHIPU_API_KEY=test-zhipu\nZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4\nZHIPU_MODEL=glm-4.5\nZHIPU_TEMPERATURE=0.6\n",
                encoding="utf-8",
            )
            config = load_zhipu_config(env_path)
            self.assertEqual(config.api_key, "test-zhipu")
            self.assertEqual(config.model, "glm-4.5")
            self.assertEqual(config.temperature, 0.6)
            self.assertEqual(resolve_provider(env_path), "zhipu")

    def test_aliases_kimi_to_moonshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("LLM_PROVIDER=kimi\n", encoding="utf-8")
            self.assertEqual(resolve_provider(env_path), "moonshot")

    def test_aliases_zhipuai_to_zhipu(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("LLM_PROVIDER=zhipuai\n", encoding="utf-8")
            self.assertEqual(resolve_provider(env_path), "zhipu")


if __name__ == "__main__":
    unittest.main()
