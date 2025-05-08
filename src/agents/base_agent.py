# src/agents/base_agent.py

import os
import re
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

class BaseEvaluationAgent:
    def __init__(self, criterion_config, api_keys):
        self.criterion_config = criterion_config
        self.api_keys = api_keys
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        provider = self.criterion_config.get("llm_provider", "openai") # Default to openai if not specified
        model_name = self.criterion_config.get("model_name")

        if provider == "openai":
            if not self.api_keys.get("OPENAI_API_KEY"):
                raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
            return ChatOpenAI(
                model_name=model_name or "gpt-4.1-turbo", # Default model if not specified
                api_key=self.api_keys["OPENAI_API_KEY"],
                temperature=0.2 # Low temperature for more deterministic output
            )
        elif provider == "gemini":
            if not self.api_keys.get("GEMINI_API_KEY"):
                raise ValueError("Gemini API key not found. Please set the GEMINI_API_KEY environment variable.")
            return ChatGoogleGenerativeAI(
                model=model_name or "gemini-1.5-flash-latest", # Default model if not specified
                google_api_key=self.api_keys["GEMINI_API_KEY"],
                temperature=0.2 # Low temperature for more deterministic output
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _construct_prompt(self, paper_text_segment, reference_material_text=None):
        criterion_name = self.criterion_config["name"]
        criterion_desc = self.criterion_config["description"]
        max_points = self.criterion_config["max_points"]

        prompt_lines = [
            f"Você é um assistente de IA especializado na avaliação de trabalhos acadêmicos. Sua tarefa é avaliar um segmento de um trabalho acadêmico com base no seguinte critério específico:",
            f"Critério: {criterion_name}",
            f"Descrição do Critério: {criterion_desc}",
            f"Pontuação Máxima para este critério: {max_points} pontos.",
            "---INÍCIO DO SEGMENTO DO TRABALHO ACADÊMICO---",
            paper_text_segment,
            "---FIM DO SEGMENTO DO TRABALHO ACADÊMICO---"
        ]

        if reference_material_text and self.criterion_config.get("reference_document"):
            prompt_lines.extend([
                "---INÍCIO DO MATERIAL DE REFERÊNCIA OBRIGATÓRIO---",
                reference_material_text,
                "---FIM DO MATERIAL DE REFERÊNCIA OBRIGATÓRIO---",
                "IMPORTANTE: Sua avaliação para este critério DEVE ser baseada EXCLUSIVAMENTE no MATERIAL DE REFERÊNCIA OBRIGATÓRIO fornecido acima e no segmento do trabalho acadêmico. Não utilize conhecimento externo ou outras fontes."
            ])
        
        # Incorporate knowledge for specific criteria if applicable
        if self.criterion_config["id"] == "analise_critica":
            prompt_lines.extend([
                "Para o critério de 'Análise Crítica das referências e SOTA', considere o seguinte:",
                "- A análise deve ir além de uma simples descrição, identificando lacunas, contradições ou oportunidades para futuras pesquisas.",
                "- Verifique se o trabalho inclui resultados quantitativos relevantes (ex: tabelas com métricas de desempenho) ao descrever trabalhos relacionados, para enriquecer a análise comparativa.",
                "- Verifique se há uma análise de lacunas no campo de estudo, destacando oportunidades de investigação científica. Uma tabela comparativa para visualizar essas lacunas é preferível."
            ])

        prompt_lines.extend([
            "Instruções para Resposta:",
            f"1. Atribua uma pontuação inteira de 0 a {max_points}.",
            "2. Forneça uma justificativa clara e concisa para a pontuação atribuída, explicando como o trabalho atende (ou não) aos requisitos do critério.",
            "3. Sua resposta DEVE seguir RIGOROSAMENTE o seguinte formato (NÃO inclua nenhuma outra informação ou formatação):",
            "Pontuação: [sua pontuação aqui]",
            "Justificativa: [sua justificativa aqui]"
        ])
        
        return "\n\n".join(prompt_lines)

    def _parse_response(self, response_text):
        try:
            score_match = re.search(r"Pontuação:\s*(\d+)", response_text, re.IGNORECASE)
            justification_match = re.search(r"Justificativa:\s*(.+)", response_text, re.IGNORECASE | re.DOTALL)

            score = int(score_match.group(1)) if score_match else None
            justification = justification_match.group(1).strip() if justification_match else None

            if score is None or justification is None:
                print(f"Error parsing LLM response. Could not find score or justification. Response: {response_text}")
                return 0, "Erro ao processar a resposta do modelo: formato inesperado."
            
            max_points = self.criterion_config["max_points"]
            if not (0 <= score <= max_points):
                print(f"Warning: Score {score} is outside the valid range [0, {max_points}]. Clipping score.")
                score = max(0, min(score, max_points))
                justification += f" (Nota: Pontuação original {score_match.group(1)} foi ajustada para o intervalo válido de 0-{max_points})"

            return score, justification
        except Exception as e:
            print(f"Error parsing LLM response: {e}. Response: {response_text}")
            return 0, f"Erro ao processar a resposta do modelo: {e}"

    def evaluate(self, paper_text_segment, reference_material_text=None):
        prompt = self._construct_prompt(paper_text_segment, reference_material_text)
        
        try:
            response = self.llm.invoke(prompt)
            response_content = response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            print(f"Error during LLM call for criterion {self.criterion_config['id']}: {e}")
            return {
                "criterion_id": self.criterion_config["id"],
                "criterion_name": self.criterion_config["name"],
                "score": 0,
                "max_points": self.criterion_config["max_points"],
                "justification": f"Erro ao contatar o modelo de linguagem: {e}",
                "llm_provider": self.criterion_config.get("llm_provider"),
                "model_name": self.criterion_config.get("model_name")
            }

        score, justification = self._parse_response(response_content)
        
        return {
            "criterion_id": self.criterion_config["id"],
            "criterion_name": self.criterion_config["name"],
            "score": score,
            "max_points": self.criterion_config["max_points"],
            "justification": justification,
            "llm_provider": self.criterion_config.get("llm_provider"),
            "model_name": self.criterion_config.get("model_name")
        }

if __name__ == '__main__':
    # This is a placeholder for testing. 
    # Actual testing requires API keys and a proper configuration.
    print("BaseEvaluationAgent class defined.")
    print("To test, you would typically instantiate this from an orchestrator with a criterion config and API keys.")
    
    # Example of how it might be called (requires dummy config and keys)
    # dummy_api_keys = {"OPENAI_API_KEY": "sk-yourkey", "GEMINI_API_KEY": "yourkey"} # Replace with actual keys for testing
    # dummy_criterion = {
    #     "id": "introducao_contextualizacao",
    #     "name": "Introdução e contextualização do tema",
    #     "description": "Avaliar a clareza e profundidade da introdução...",
    #     "max_points": 2,
    #     "llm_provider": "openai", # or "gemini"
    #     "model_name": "gpt-4.1-turbo" # or a gemini model
    # }
    # try:
    #     agent = BaseEvaluationAgent(dummy_criterion, dummy_api_keys)
    #     sample_text = "Este é um exemplo de texto de um trabalho acadêmico para avaliação da introdução."
    #     evaluation = agent.evaluate(sample_text)
    #     print("Evaluation result:", evaluation)
    # except ValueError as e:
    #     print(f"Error initializing agent: {e}")
    # except Exception as e:
    #     print(f"An unexpected error occurred: {e}")

