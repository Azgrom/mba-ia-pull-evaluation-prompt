"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        chat_prompt_template = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data["user_prompt"]),
        ])

        tags = prompt_data.get("tags", []) + prompt_data.get("techniques_applied", [])

        url = Client().push_prompt(
            prompt_name,
            object=chat_prompt_template,
            is_public=True,
            description=prompt_data.get("description", ""),
            tags=tags,
        )

        print(f"   ✓ Prompt publicado com sucesso")
        print(f"   URL: {url}")

        return True

    except Exception as e:
        print(f"\n{'=' * 70}")
        print(f"❌ ERRO: Não foi possível publicar o prompt '{prompt_name}'")
        print(f"{'=' * 70}\n")
        print(f"Erro técnico: {e}\n")
        print("Verifique:")
        print("- LANGSMITH_API_KEY está configurada corretamente no .env")
        print("- USERNAME_LANGSMITH_HUB corresponde ao seu usuário no LangSmith Hub")
        print("- Sua conexão com a internet está funcionando")
        print(f"\n{'=' * 70}\n")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    return validate_prompt_structure(prompt_data)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml("prompts/bug_to_user_story_v2.yml")
    if data is None:
        return 1

    prompt_data = data["bug_to_user_story_v2"]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    prompt_name = f"{os.getenv('USERNAME_LANGSMITH_HUB')}/bug_to_user_story_v2"

    if not push_prompt_to_langsmith(prompt_name, prompt_data):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
