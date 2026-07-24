"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import sys
from datetime import date
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def pull_prompts_from_langsmith() -> Optional[Dict[str, Any]]:
    """
    Faz pull do prompt v1 do LangSmith Hub e monta o dicionário local
    no mesmo formato do arquivo prompts/bug_to_user_story_v1.yml.

    Returns:
        Dicionário com o prompt v1 ou None em caso de erro
    """
    prompt_identifier = "leonanluppi/bug_to_user_story_v1"

    try:
        print(f"   Puxando prompt do LangSmith Hub: {prompt_identifier}")
        prompt = hub.pull(prompt_identifier)

        system_prompt = ""
        user_prompt = ""

        for message in prompt.messages:
            template = message.prompt.template
            role_name = message.__class__.__name__

            if "System" in role_name:
                system_prompt = template
            elif "Human" in role_name:
                user_prompt = template

        print(f"   ✓ Prompt carregado com sucesso")

        return {
            "bug_to_user_story_v1": {
                "description": "Prompt para converter relatos de bugs em User Stories",
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "version": "v1",
                "created_at": date.today().isoformat(),
                "tags": ["bug-analysis", "user-story", "product-management"],
            }
        }

    except Exception as e:
        print(f"\n{'=' * 70}")
        print(f"❌ ERRO: Não foi possível puxar o prompt '{prompt_identifier}'")
        print(f"{'=' * 70}\n")
        print(f"Erro técnico: {e}\n")
        print("Verifique:")
        print("- LANGSMITH_API_KEY está configurada corretamente no .env")
        print("- Você tem acesso ao workspace do LangSmith")
        print("- O prompt existe no Hub com esse identificador")
        print("- Sua conexão com a internet está funcionando")
        print(f"\n{'=' * 70}\n")
        return None


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    result = pull_prompts_from_langsmith()
    if result is None:
        return 1

    output_path = "prompts/bug_to_user_story_v1.yml"
    if not save_yaml(result, output_path):
        return 1

    print(f"✓ Prompt salvo em {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
