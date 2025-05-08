# src/main.py

import os
import argparse
import json
import pandas as pd
from datetime import datetime

from academic_evaluator.src.orchestrator import AcademicPaperOrchestrator
from academic_evaluator.src.reporter import CSVReporter

def main():
    parser = argparse.ArgumentParser(description="Academic Paper Evaluator using LLMs and Langgraph.")
    parser.add_argument("--pdf_dir", type=str, default="/home/ubuntu/academic_evaluator/pdfs",
                        help="Directory containing PDF files to evaluate.")
    parser.add_argument("--config_file", type=str, default="/home/ubuntu/academic_evaluator/config/criteria.json",
                        help="Path to the criteria configuration JSON file.")
    parser.add_argument("--reports_dir", type=str, default="/home/ubuntu/academic_evaluator/reports",
                        help="Directory to save the evaluation reports.")
    parser.add_argument("--ref_materials_dir", type=str, default="/home/ubuntu/academic_evaluator/reference_materials",
                        help="Directory containing reference material files (e.g., State of AI Report PPTX).")
    
    args = parser.parse_args()

    print("--- Academic Paper Evaluator --- Kicking off ---")

    # Load API Keys (ensure these are set in your environment)
    api_keys = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY")
    }

    if not api_keys["OPENAI_API_KEY"] or not api_keys["GEMINI_API_KEY"]:
        print("Error: OPENAI_API_KEY and/or GEMINI_API_KEY environment variables not set.")
        print("Please set these API keys to proceed with evaluations.")
        return

    # Initialize Orchestrator
    # The orchestrator now internally handles reference material paths based on config
    orchestrator = AcademicPaperOrchestrator(config_path=args.config_file)
    if not orchestrator.criteria:
        print(f"Could not load criteria from {args.config_file}. Exiting.")
        return

    # List PDF files
    if not os.path.isdir(args.pdf_dir):
        print(f"Error: PDF directory not found: {args.pdf_dir}")
        return
    
    pdf_files = [os.path.join(args.pdf_dir, f) for f in os.listdir(args.pdf_dir) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"No PDF files found in {args.pdf_dir}. Exiting.")
        return

    print(f"Found {len(pdf_files)} PDF(s) to evaluate in {args.pdf_dir}")

    all_results_for_report = []

    for pdf_path in pdf_files:
        print(f"\nProcessing: {os.path.basename(pdf_path)}...")
        try:
            evaluation_output = orchestrator.run_evaluation(pdf_path=pdf_path, api_keys=api_keys)
            all_results_for_report.append(evaluation_output)
            print(f"Finished processing: {os.path.basename(pdf_path)}")
            if evaluation_output.get("errors"):
                print(f"  Errors encountered for {os.path.basename(pdf_path)}: {evaluation_output["errors"]}")
        except Exception as e:
            print(f"Critical error during evaluation of {os.path.basename(pdf_path)}: {e}")
            # Add error to report structure
            all_results_for_report.append({
                "pdf_path": pdf_path,
                "evaluations": [],
                "errors": [f"Critical error in main loop: {str(e)}"]
            })

    # Generate CSV Report
    if all_results_for_report:
        reporter = CSVReporter(report_dir=args.reports_dir)
        report_file_path = reporter.generate_report(all_results_for_report)
        if report_file_path:
            print(f"\nOverall evaluation complete. Report saved to: {report_file_path}")
        else:
            print("\nOverall evaluation complete, but report generation failed.")
    else:
        print("\nNo results to report.")
    
    print("--- Academic Paper Evaluator --- Finished ---")

if __name__ == "__main__":
    # Make sure the src package structure is recognized if running main.py directly
    # This might require setting PYTHONPATH or running as a module `python -m academic_evaluator.src.main`
    # For simplicity in this environment, we assume direct execution might work if paths are relative
    # or the package is installed/PYTHONPATH is set.
    
    # Adjusting sys.path for direct execution if academic_evaluator is the root for modules
    import sys
    # Assuming main.py is in /home/ubuntu/academic_evaluator/src/
    # and we want to import from /home/ubuntu/academic_evaluator/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) # This should be /home/ubuntu/academic_evaluator
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    main()

