# System Architecture Design for Academic Evaluator

## 1. Overview

The Academic Evaluator system is designed to automate the assessment of academic papers based on a configurable set of criteria. It leverages Large Language Models (LLMs) from OpenAI and Gemini, with individual AI agents responsible for evaluating specific aspects of a paper. Langgraph will be used to orchestrate these agents.

## 2. System Components

1.  **Configuration Module (`config/criteria.json`)**: 
    *   Stores evaluation criteria, points, LLM provider (OpenAI/Gemini), model names, and any reference documents for specific criteria.
    *   Allows users to define and modify evaluation rubrics without code changes.

2.  **Input Module (PDFs)**:
    *   Academic papers in PDF format will be placed in the `academic_evaluator/pdfs/` directory.

3.  **PDF Processing Module (`src/pdf_parser.py`)**:
    *   Responsible for extracting text content from PDF files.
    *   Will use `pypdf` library primarily.
    *   For complex PDFs (e.g., with many images/tables or extraction issues), it might need a fallback or a note for manual review (or use browser-based viewing if necessary, as per knowledge).

4.  **Reference Material Module (`academic_evaluator/reference_materials/`)**:
    *   Stores reference documents like the 'State of AI Report 2024.pptx'.
    *   The `python-pptx` library will be used to extract text/content from PPTX files if needed by an agent.

5.  **Evaluation Agents (`src/agents/`)**:
    *   A separate Python module/class for each evaluation criterion defined in `criteria.json`.
    *   Each agent will be a Langchain (or compatible) agent.
    *   Each agent will receive the relevant text from the academic paper and any specific reference material (e.g., content from 'State of AI Report 2024').
    *   It will use the specified LLM (OpenAI GPT-4.1 or Gemini 1.5 Flash) to assess the paper against its assigned criterion.
    *   The agent will output a score (within the `max_points` for that criterion) and a textual justification for the score.
    *   **Strict Source Adherence**: Agents using reference documents (like the 'State of AI Report' agent) must be designed to *only* use information from that specific document for its evaluation, as per user requirements and knowledge items `user_4`, `user_5`, and `user_6`.

6.  **Orchestration Module (`src/orchestrator.py` using Langgraph)**:
    *   Loads the criteria from `config/criteria.json`.
    *   For each PDF, it initializes and runs the sequence of evaluation agents using Langgraph.
    *   The Langgraph graph will define the flow: PDF text -> Agent 1 -> Agent 2 -> ... -> Agent N -> Aggregate Results.
    *   It will manage the state (e.g., extracted text, intermediate evaluations) as it passes through the graph.

7.  **Reporting Module (`src/reporter.py`)**:
    *   Collects the scores and justifications from all agents for each paper.
    *   Generates a CSV file in the `academic_evaluator/reports/` directory.
    *   The CSV will have columns like: `Paper_Filename`, `Criterion_ID`, `Criterion_Name`, `Assigned_LLM`, `Score`, `Max_Points`, `Justification`.

8.  **Main Script (`src/main.py`)**:
    *   Entry point of the application.
    *   Handles command-line arguments (if any, e.g., path to PDF folder, config file).
    *   Initializes and calls the Orchestration Module for each paper.
    *   Handles API key management (e.g., reading from environment variables or a secure config, user will provide these).

## 3. Data Flow

1.  User places PDF papers into `academic_evaluator/pdfs/` and the 'State of AI Report 2024.pptx' into `academic_evaluator/reference_materials/`.
2.  User ensures `config/criteria.json` is correctly set up.
3.  User runs `src/main.py`.
4.  `main.py` reads `config/criteria.json`.
5.  For each PDF in `academic_evaluator/pdfs/`:
    a.  `pdf_parser.py` extracts text from the PDF.
    b.  If the 'State of AI Report 2024' is needed for a criterion, its content is extracted (e.g., using `python-pptx`).
    c.  The Orchestrator (`langgraph`) invokes the defined sequence of evaluation agents.
    d.  Each agent receives the PDF text (and reference material text if applicable) and returns a score and justification.
    e.  The Orchestrator collects all evaluations.
6.  `reporter.py` compiles all evaluations into a single CSV file in `academic_evaluator/reports/`.

## 4. Langgraph Workflow Structure (Conceptual)

*   **Nodes**: 
    *   `extract_pdf_text`: Takes PDF path, returns text.
    *   `extract_reference_text` (conditional): Takes reference doc path, returns text (e.g., for State of AI Report).
    *   `evaluate_criterion_<criterion_id>`: One node for each agent. Takes PDF text, (optional) reference text, criterion details. Returns score and justification.
    *   `aggregate_results`: Takes all individual evaluations, prepares data for CSV.
*   **Edges**: Define the flow from text extraction to individual evaluations, and finally to aggregation.
*   **State**: The graph will maintain a state object containing the PDF filename, extracted text, reference text (if any), and a list of evaluation results.

## 5. Agent Structure (Conceptual for each agent)

```python
# Example for an agent in src/agents/base_agent.py or specific agent files

class EvaluationAgent:
    def __init__(self, llm_provider, model_name, criterion_details, api_keys):
        self.llm = self._initialize_llm(llm_provider, model_name, api_keys)
        self.criterion = criterion_details

    def _initialize_llm(self, llm_provider, model_name, api_keys):
        if llm_provider == "openai":
            # Initialize OpenAI LLM with api_keys["openai"]
            pass
        elif llm_provider == "gemini":
            # Initialize Gemini LLM with api_keys["gemini"]
            pass
        return llm_instance

    def evaluate(self, paper_text, reference_text=None):
        prompt = self._construct_prompt(paper_text, reference_text)
        # LLM call
        response = self.llm.invoke(prompt)
        score, justification = self._parse_response(response)
        return {"score": score, "justification": justification, "criterion_id": self.criterion["id"]}

    def _construct_prompt(self, paper_text, reference_text=None):
        # Prompt engineering specific to the criterion
        # If reference_text is provided, ensure prompt instructs LLM to *only* use it.
        # Example:
        # "You are an AI assistant evaluating an academic paper based on the criterion: {self.criterion['name']}."
        # "The maximum score for this criterion is {self.criterion['max_points']}."
        # "Here is the relevant section of the paper:\n{paper_text}"
        # If reference_text:
        # "You MUST base your evaluation for this specific criterion SOLELY on the following provided reference material: {reference_text}. Do not use any other information."
        # "Provide a score (integer) between 0 and {self.criterion['max_points']} and a brief justification for your score."
        # "Format your response as: Score: [score]\nJustification: [justification]"
        pass

    def _parse_response(self, response):
        # Parse score and justification from LLM response
        pass
```

## 6. Configuration for Flexibility

*   `criteria.json` will be the primary way to add/modify criteria and agents.
*   The orchestrator will dynamically create and wire agents based on this file.

## 7. API Key Management

*   API keys for OpenAI and Gemini will be expected as environment variables (e.g., `OPENAI_API_KEY`, `GEMINI_API_KEY`) or loaded from a secure `.env` file (not committed to repo). The user will be responsible for setting these up in their environment.

This design document provides a high-level plan. Details will be refined during implementation of each module.

