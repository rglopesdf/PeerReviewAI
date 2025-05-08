# src/orchestrator.py

import json
import os
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

from .pdf_parser import PDFParser
from .reference_parser import ReferenceParser
from .agents.base_agent import BaseEvaluationAgent

# Define the state for the graph
class EvaluationState(TypedDict):
    pdf_path: str
    pdf_text: str
    reference_material_path: str | None
    reference_material_text: str | None
    criteria_config: List[Dict[str, Any]]
    current_criterion_index: int
    evaluation_results: List[Dict[str, Any]]
    api_keys: Dict[str, str]
    error_messages: List[str]

class AcademicPaperOrchestrator:
    def __init__(self, config_path="/home/ubuntu/academic_evaluator/config/criteria.json"):
        self.config_path = config_path
        self.criteria = self._load_criteria()
        self.pdf_parser = PDFParser()
        self.reference_parser = ReferenceParser()
        self.workflow = self._build_graph()

    def _load_criteria(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get("criteria", [])
        except FileNotFoundError:
            print(f"Error: Configuration file not found at {self.config_path}")
            return []
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {self.config_path}")
            return []

    # Define node functions
    def start_evaluation_node(self, state: EvaluationState) -> EvaluationState:
        print(f"Starting evaluation for: {state['pdf_path']}")
        state["current_criterion_index"] = 0
        state["evaluation_results"] = []
        state["error_messages"] = []
        return state

    def extract_pdf_text_node(self, state: EvaluationState) -> EvaluationState:
        print(f"Extracting text from PDF: {state['pdf_path']}")
        try:
            text = self.pdf_parser.extract_text(state['pdf_path'])
            if not text:
                state["error_messages"].append(f"Failed to extract text from PDF: {state['pdf_path']}. Content is empty.")
            state["pdf_text"] = text
        except Exception as e:
            error_msg = f"Error during PDF text extraction for {state['pdf_path']}: {str(e)}"
            print(error_msg)
            state["error_messages"].append(error_msg)
            state["pdf_text"] = ""
        return state

    def extract_reference_material_node(self, state: EvaluationState) -> EvaluationState:
        criterion_index = state["current_criterion_index"]
        if criterion_index < len(state["criteria_config"]):
            current_criterion = state["criteria_config"][criterion_index]
            ref_doc_name = current_criterion.get("reference_document")
            
            if ref_doc_name:
                # Assuming reference materials are in a fixed directory
                # This path might need to be more flexible or passed in state
                ref_path = os.path.join("/home/ubuntu/academic_evaluator/reference_materials", ref_doc_name)
                state["reference_material_path"] = ref_path
                print(f"Extracting text from reference material: {ref_path} for criterion: {current_criterion['name']}")
                if not os.path.exists(ref_path):
                    error_msg = f"Reference document {ref_doc_name} not found at {ref_path} for criterion {current_criterion['name']}."
                    print(error_msg)
                    state["error_messages"].append(error_msg)
                    state["reference_material_text"] = None # Ensure it's None if not found
                    return state
                try:
                    if ref_doc_name.lower().endswith(".pptx"):
                        text = self.reference_parser.extract_text_from_pptx(ref_path)
                    # Add other reference types here if needed (e.g., .txt, .md)
                    # elif ref_doc_name.lower().endswith(".txt"):
                    #    with open(ref_path, 'r', encoding='utf-8') as f:
                    #        text = f.read()
                    else:
                        error_msg = f"Unsupported reference document type: {ref_doc_name}"
                        print(error_msg)
                        state["error_messages"].append(error_msg)
                        text = None
                    
                    if not text and os.path.exists(ref_path): # File exists but no text extracted
                         state["error_messages"].append(f"Failed to extract text from reference: {ref_doc_name}. Content is empty.")
                    state["reference_material_text"] = text
                except Exception as e:
                    error_msg = f"Error during reference material extraction for {ref_doc_name}: {str(e)}"
                    print(error_msg)
                    state["error_messages"].append(error_msg)
                    state["reference_material_text"] = None
            else:
                state["reference_material_text"] = None # No reference doc for this criterion
        return state

    def evaluate_criterion_node(self, state: EvaluationState) -> EvaluationState:
        criterion_index = state["current_criterion_index"]
        current_criterion = state["criteria_config"][criterion_index]
        print(f"Evaluating criterion: {current_criterion['name']}")

        if not state.get("pdf_text"):
            print(f"Skipping criterion {current_criterion['name']} due to missing PDF text.")
            # Add a placeholder result indicating failure due to missing PDF text
            result = {
                "criterion_id": current_criterion["id"],
                "criterion_name": current_criterion["name"],
                "score": 0,
                "max_points": current_criterion["max_points"],
                "justification": "Avaliação não pôde ser realizada: Falha ao extrair texto do PDF.",
                "llm_provider": current_criterion.get("llm_provider"),
                "model_name": current_criterion.get("model_name")
            }
            state["evaluation_results"].append(result)
            return state

        agent = BaseEvaluationAgent(criterion_config=current_criterion, api_keys=state["api_keys"])
        
        # For simplicity, we pass the whole PDF text. 
        # In a more advanced setup, we might pass only relevant sections.
        paper_segment = state["pdf_text"]
        ref_text = state.get("reference_material_text") # This will be None if not applicable or extraction failed

        # If reference material was required but failed to load, reflect this in the justification
        if current_criterion.get("reference_document") and not ref_text:
            print(f"Reference material {current_criterion.get('reference_document')} was required for {current_criterion['name']} but could not be loaded/parsed.")
            result = {
                "criterion_id": current_criterion["id"],
                "criterion_name": current_criterion["name"],
                "score": 0,
                "max_points": current_criterion["max_points"],
                "justification": f"Avaliação não pôde ser realizada: Material de referência obrigatório '{current_criterion.get('reference_document')}' não pôde ser carregado ou processado.",
                "llm_provider": current_criterion.get("llm_provider"),
                "model_name": current_criterion.get("model_name")
            }
        else:
            try:
                result = agent.evaluate(paper_text_segment=paper_segment, reference_material_text=ref_text)
            except Exception as e:
                error_msg = f"Error during agent evaluation for criterion {current_criterion['name']}: {str(e)}"
                print(error_msg)
                state["error_messages"].append(error_msg)
                result = {
                    "criterion_id": current_criterion["id"],
                    "criterion_name": current_criterion["name"],
                    "score": 0,
                    "max_points": current_criterion["max_points"],
                    "justification": f"Erro crítico durante a avaliação pelo agente: {str(e)}",
                    "llm_provider": current_criterion.get("llm_provider"),
                    "model_name": current_criterion.get("model_name")
                }

        state["evaluation_results"].append(result)
        return state

    def decide_next_criterion_node(self, state: EvaluationState) -> str:
        state["current_criterion_index"] += 1
        if state["current_criterion_index"] < len(state["criteria_config"]):
            # Clear reference text for the next criterion, it will be re-extracted if needed
            state["reference_material_text"] = None
            state["reference_material_path"] = None
            return "extract_reference_material"
        else:
            return "end_evaluation"

    def _build_graph(self):
        graph_builder = StateGraph(EvaluationState)

        graph_builder.add_node("start_evaluation", self.start_evaluation_node)
        graph_builder.add_node("extract_pdf_text", self.extract_pdf_text_node)
        graph_builder.add_node("extract_reference_material", self.extract_reference_material_node)
        graph_builder.add_node("evaluate_criterion", self.evaluate_criterion_node)

        graph_builder.set_entry_point("start_evaluation")
        graph_builder.add_edge("start_evaluation", "extract_pdf_text")
        graph_builder.add_edge("extract_pdf_text", "extract_reference_material") # Always try to extract ref for the first criterion
        graph_builder.add_edge("extract_reference_material", "evaluate_criterion")
        graph_builder.add_edge("evaluate_criterion", "decide_next_criterion")
        
        graph_builder.add_conditional_edges(
            "decide_next_criterion",
            self.decide_next_criterion_node,
            {
                "extract_reference_material": "extract_reference_material",
                "end_evaluation": END
            }
        )
        return graph_builder.compile()

    def run_evaluation(self, pdf_path: str, api_keys: Dict[str, str]) -> Dict[str, Any]:
        if not self.criteria:
            print("No criteria loaded. Cannot run evaluation.")
            return {"pdf_path": pdf_path, "evaluations": [], "errors": ["No criteria loaded from configuration."]}

        initial_state = EvaluationState(
            pdf_path=pdf_path,
            pdf_text="",
            reference_material_path=None,
            reference_material_text=None,
            criteria_config=self.criteria,
            current_criterion_index=0,
            evaluation_results=[],
            api_keys=api_keys,
            error_messages=[]
        )
        
        final_state = self.workflow.invoke(initial_state)
        
        return {
            "pdf_path": pdf_path,
            "evaluations": final_state.get("evaluation_results", []),
            "errors": final_state.get("error_messages", [])
        }

if __name__ == '__main__':
    # This is a placeholder for testing.
    # Actual testing requires API keys, a config file, a PDF, and potentially a reference PPTX.
    print("AcademicPaperOrchestrator class defined.")
    print("To test, you would typically call run_evaluation from main.py with a PDF path and API keys.")

    # Example of how it might be called (requires setup):
    # orchestrator = AcademicPaperOrchestrator()
    # dummy_api_keys = {
    #     "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"), 
    #     "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY")
    # }
    # if not dummy_api_keys["OPENAI_API_KEY"] or not dummy_api_keys["GEMINI_API_KEY"]:
    #     print("Please set OPENAI_API_KEY and GEMINI_API_KEY environment variables to test.")
    # else:
    #     # Create dummy files and dirs for a minimal test
    #     if not os.path.exists("/home/ubuntu/academic_evaluator/pdfs"): os.makedirs("/home/ubuntu/academic_evaluator/pdfs")
    #     if not os.path.exists("/home/ubuntu/academic_evaluator/config"): os.makedirs("/home/ubuntu/academic_evaluator/config")
    #     if not os.path.exists("/home/ubuntu/academic_evaluator/reference_materials"): os.makedirs("/home/ubuntu/academic_evaluator/reference_materials")
        
    #     # Create a dummy criteria.json
    #     dummy_criteria_content = {"criteria": [
    #         {
    #             "id": "test_crit", "name": "Test Criterion", "description": "Test desc", 
    #             "max_points": 1, "llm_provider": "openai", "model_name": "gpt-4.1-turbo"
    #         }
    #     ]}
    #     with open("/home/ubuntu/academic_evaluator/config/criteria.json", "w") as f:
    #         json.dump(dummy_criteria_content, f)

    #     # Create a dummy PDF (actual PDF parsing needs a real PDF)
    #     # For a simple test, we can mock the pdf_parser or use a very simple real PDF.
    #     # This example will likely fail on PDF parsing if a real PDF isn't there.
    #     dummy_pdf = "/home/ubuntu/academic_evaluator/pdfs/test.pdf"
    #     # from pypdf import PdfWriter # Create a simple PDF for testing
    #     # writer = PdfWriter()
    #     # writer.add_blank_page(width=8.5 * 72, height=11 * 72) # Standard letter size
    #     # # writer.updatePageFormFieldValues(writer.page_labels[0], {"sometextfield": "Hello World"})
    #     # with open(dummy_pdf, "wb") as f_pdf:
    #     #     writer.write(f_pdf)
    #     print(f"Please create a dummy PDF at {dummy_pdf} for a more complete test.")

    #     if os.path.exists(dummy_pdf): # Only run if dummy PDF exists
    #        results = orchestrator.run_evaluation(dummy_pdf, dummy_api_keys)
    #        print("\nEvaluation Results:", json.dumps(results, indent=2, ensure_ascii=False))
    #     else:
    #        print(f"Skipping run_evaluation as dummy PDF {dummy_pdf} not found.")

