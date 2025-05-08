# Avaliador Acadêmico com LLMs e Langgraph

## 1. Visão Geral

Este projeto implementa um sistema para avaliar trabalhos acadêmicos (em formato PDF) utilizando Modelos de Linguagem de Grande Escala (LLMs) da OpenAI (família GPT-4.1) e Gemini (Gemini 1.5 Flash). Cada critério de avaliação é tratado por um agente de IA dedicado, e a orquestração desses agentes é realizada com Langgraph. O sistema é projetado para ser configurável, permitindo que os usuários modifiquem os critérios de avaliação e, potencialmente, adicionem novos agentes.

O resultado da avaliação é um arquivo CSV detalhado, contendo a pontuação e a justificativa para cada critério avaliado por trabalho.

## 2. Funcionalidades

- Avaliação de trabalhos acadêmicos em PDF com base em critérios configuráveis.
- Utilização simultânea de modelos LLM da OpenAI e Gemini.
- Arquitetura baseada em agentes, onde cada agente é responsável por um critério específico.
- Orquestração de agentes utilizando Langgraph para um fluxo de avaliação robusto.
- Extração de texto de arquivos PDF e de materiais de referência em formato PPTX (ex: "State of AI Report 2024").
- Geração de relatórios de avaliação em formato CSV.
- Alta configurabilidade através de um arquivo JSON (`config/criteria.json`) para definir critérios, pontuações, modelos LLM e documentos de referência.

## 3. Estrutura de Diretórios

```
academic_evaluator/
├── config/
│   └── criteria.json           # Arquivo de configuração dos critérios de avaliação
├── docs/
│   └── system_architecture.md  # Documento de design da arquitetura do sistema
├── pdfs/                       # Diretório para colocar os PDFs dos trabalhos a serem avaliados
│   ├── sample_paper_1.pdf      # PDF de exemplo
│   └── another_sample_paper.pdf # Outro PDF de exemplo
├── reference_materials/        # Diretório para materiais de referência (ex: PPTX)
│   └── State_of_AI_Report_2024.pptx # Arquivo PPTX de exemplo
├── reports/                    # Diretório onde os relatórios CSV serão salvos
├── src/
│   ├── agents/
│   │   └── base_agent.py       # Lógica base para os agentes de avaliação
│   ├── __init__.py
│   ├── main.py                 # Script principal para executar a avaliação
│   ├── orchestrator.py         # Módulo de orquestração com Langgraph
│   ├── pdf_parser.py           # Módulo para extração de texto de PDFs
│   ├── reference_parser.py     # Módulo para extração de texto de PPTX
│   └── reporter.py             # Módulo para geração de relatórios CSV
├── requirements.txt            # Lista de dependências Python
└── README.md                   # Este arquivo
```

## 4. Pré-requisitos

- Python 3.10 ou superior.
- `pip` para instalar as dependências Python.

## 5. Instruções de Configuração

1.  **Clone ou Baixe o Projeto**:
    Obtenha os arquivos do projeto e extraia-os para um diretório local.

2.  **Crie um Ambiente Virtual (Recomendado)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Linux/macOS
    # venv\Scripts\activate    # No Windows
    ```

3.  **Instale as Dependências**:
    Navegue até o diretório raiz do projeto (`academic_evaluator`) e execute:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Chaves de API**:
    Este sistema requer chaves de API para OpenAI e Gemini. Você deve configurá-las como variáveis de ambiente:
    ```bash
    export OPENAI_API_KEY="sua_chave_openai_aqui"
    export GEMINI_API_KEY="sua_chave_gemini_aqui"
    ```
    Substitua `"sua_chave_openai_aqui"` e `"sua_chave_gemini_aqui"` pelas suas chaves reais.

## 6. Configuração do Sistema

### Arquivo de Critérios (`config/criteria.json`)

Este arquivo JSON define os critérios de avaliação. Você pode modificar os critérios existentes ou adicionar novos. Cada critério é um objeto com os seguintes campos:

-   `id`: Um identificador único para o critério (string).
-   `name`: O nome do critério a ser exibido (string).
-   `description`: Uma descrição detalhada do que o agente deve avaliar para este critério (string).
-   `max_points`: A pontuação máxima para este critério (inteiro).
-   `llm_provider`: O provedor do LLM a ser usado ("openai" ou "gemini") (string).
-   `model_name`: O nome específico do modelo LLM (ex: "gpt-4.1-turbo", "gemini-1.5-flash-latest") (string).
-   `reference_document` (opcional): O nome do arquivo de referência (ex: "State_of_AI_Report_2024.pptx") localizado no diretório `reference_materials/`. Se especificado, o conteúdo deste documento será fornecido ao agente para este critério específico.

**Exemplo de um critério no `criteria.json`**:
```json
{
  "id": "introducao_contextualizacao",
  "name": "Introdução e contextualização do tema",
  "description": "Avaliar a clareza e profundidade da introdução, a contextualização do tema de pesquisa e a relevância do problema abordado.",
  "max_points": 2,
  "llm_provider": "openai",
  "model_name": "gpt-4.1-turbo"
}
```

### Adicionando Novos Agentes/Critérios

Para adicionar um novo critério (e, portanto, um novo agente para avaliá-lo):

1.  Adicione uma nova entrada de objeto ao array `criteria` no arquivo `config/criteria.json` seguindo o formato descrito acima.
2.  A lógica do `base_agent.py` é genérica o suficiente para lidar com novos critérios definidos no JSON, incluindo o uso de documentos de referência, desde que os prompts sejam bem elaborados na descrição do critério.
3.  Se um critério exigir uma lógica de prompt muito especializada que não possa ser coberta pela descrição e pelas instruções gerais no `base_agent.py`, pode ser necessário modificar o método `_construct_prompt` em `src/agents/base_agent.py` para adicionar tratamento condicional para o novo `id` do critério, ou criar uma nova classe de agente especializada herdando de `BaseEvaluationAgent` e ajustar o `orchestrator.py` para usá-la (embora o design atual vise evitar isso para novos critérios simples).

## 7. Uso

1.  **Prepare os Arquivos de Entrada**:
    *   Coloque os trabalhos acadêmicos em formato PDF que você deseja avaliar no diretório `academic_evaluator/pdfs/`.
    *   Se algum critério em `config/criteria.json` especificar um `reference_document`, certifique-se de que este arquivo (ex: `State_of_AI_Report_2024.pptx`) esteja presente no diretório `academic_evaluator/reference_materials/`.

2.  **Execute o Script Principal**:
    Navegue até o diretório raiz do projeto (`academic_evaluator`). A maneira recomendada de executar é como um módulo, o que ajuda o Python a resolver as importações corretamente:
    ```bash
    python -m academic_evaluator.src.main
    ```
    Alternativamente, se você estiver no diretório `academic_evaluator/src/`, você pode tentar executar `python main.py`, mas a abordagem de módulo é mais robusta.

    O script `main.py` aceita os seguintes argumentos de linha de comando (com valores padrão já configurados):
    *   `--pdf_dir`: Diretório contendo os arquivos PDF (padrão: `/home/ubuntu/academic_evaluator/pdfs`). **Ajuste este caminho se necessário para o seu ambiente.**
    *   `--config_file`: Caminho para o arquivo de configuração dos critérios (padrão: `/home/ubuntu/academic_evaluator/config/criteria.json`). **Ajuste este caminho se necessário.**
    *   `--reports_dir`: Diretório para salvar os relatórios de avaliação (padrão: `/home/ubuntu/academic_evaluator/reports`). **Ajuste este caminho se necessário.**
    *   `--ref_materials_dir`: Diretório contendo os materiais de referência (padrão: `/home/ubuntu/academic_evaluator/reference_materials`). **Ajuste este caminho se necessário.**

    Exemplo de execução especificando o diretório de PDFs (útil se você não estiver usando os caminhos padrão ou o nome de usuário `ubuntu`):
    ```bash
    python -m academic_evaluator.src.main --pdf_dir ./pdfs --config_file ./config/criteria.json --reports_dir ./reports --ref_materials_dir ./reference_materials
    ```

3.  **Verifique os Resultados**:
    Após a execução, um arquivo CSV com os resultados da avaliação será gerado no diretório `academic_evaluator/reports/`. O nome do arquivo incluirá um timestamp (ex: `evaluation_report_20250508_123045.csv`).
    O CSV conterá colunas como: `Paper_Filename`, `Criterion_ID`, `Criterion_Name`, `Score`, `Max_Points`, `Justification`, `Assigned_LLM_Provider`, `Assigned_LLM_Model`, e `Evaluation_Errors`.

## 8. Solução de Problemas

-   **Erro de Chave de API**: Certifique-se de que as variáveis de ambiente `OPENAI_API_KEY` e `GEMINI_API_KEY` estão corretamente configuradas e exportadas no seu terminal antes de executar o script.
-   **Arquivo Não Encontrado**: Verifique se os caminhos para os diretórios de PDFs, configuração, relatórios e materiais de referência estão corretos. Use os argumentos de linha de comando se os padrões não corresponderem à sua estrutura.
-   **Falha na Extração de PDF/PPTX**: Alguns PDFs (especialmente os baseados em imagem ou com formatação complexa) ou PPTXs podem não ser totalmente processados. O sistema tenta lidar com erros, mas a qualidade da extração pode variar.
-   **Problemas de Dependência**: Se encontrar erros relacionados a módulos não encontrados, certifique-se de que você ativou o ambiente virtual (se estiver usando um) e que todas as dependências em `requirements.txt` foram instaladas corretamente.

## 9. Feedback e Relato de Problemas

Se você encontrar problemas ao executar este sistema no seu ambiente, por favor, relate-os para que possam ser investigados.

