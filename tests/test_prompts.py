"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestPrompts:
    def _load_prompt_data(self):
        """Carrega o dicionário interno do prompt v2."""
        prompts_path = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
        return load_prompts(str(prompts_path))["bug_to_user_story_v2"]

    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompt_data = self._load_prompt_data()
        assert "system_prompt" in prompt_data
        assert prompt_data["system_prompt"].strip() != ""

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        prompt_data = self._load_prompt_data()
        system_prompt = prompt_data["system_prompt"]
        assert "Você é" in system_prompt
        assert "Product Owner" in system_prompt

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        prompt_data = self._load_prompt_data()
        system_prompt = prompt_data["system_prompt"]
        assert "Como um" in system_prompt
        assert "eu quero" in system_prompt
        assert "para que" in system_prompt

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        prompt_data = self._load_prompt_data()
        system_prompt = prompt_data["system_prompt"]
        assert "Exemplo 1" in system_prompt
        assert "Exemplo 2" in system_prompt

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        prompt_data = self._load_prompt_data()
        assert "TODO" not in prompt_data["system_prompt"]

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        prompt_data = self._load_prompt_data()
        assert len(prompt_data.get("techniques_applied", [])) >= 2

        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, errors
        assert errors == []

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])