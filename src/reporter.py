# src/reporter.py

import os
import pandas as pd
from datetime import datetime

class CSVReporter:
    def __init__(self, report_dir="/home/ubuntu/academic_evaluator/reports"):
        self.report_dir = report_dir
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)

    def generate_report(self, all_evaluations_data, filename_prefix="evaluation_report"):
        """Generates a CSV report from the evaluation data.

        Args:
            all_evaluations_data (list): A list of dictionaries, where each dictionary 
                                         contains evaluation data for one paper 
                                         (including 'pdf_path', 'evaluations', 'errors').
            filename_prefix (str): Prefix for the report filename.

        Returns:
            str: The absolute path to the generated CSV report, or None if generation failed.
        """
        if not all_evaluations_data:
            print("No evaluation data to generate report.")
            return None

        flat_data = []
        for paper_eval_data in all_evaluations_data:
            pdf_path = paper_eval_data.get("pdf_path", "Unknown PDF")
            paper_filename = os.path.basename(pdf_path)
            evaluations = paper_eval_data.get("evaluations", [])
            errors = paper_eval_data.get("errors", [])
            
            if not evaluations and not errors:
                flat_data.append({
                    "Paper_Filename": paper_filename,
                    "Criterion_ID": "N/A",
                    "Criterion_Name": "N/A",
                    "Assigned_LLM_Provider": "N/A",
                    "Assigned_LLM_Model": "N/A",
                    "Score": "N/A",
                    "Max_Points": "N/A",
                    "Justification": "No evaluations or errors reported for this paper.",
                    "Evaluation_Errors": ""
                })
                continue

            if evaluations:
                for eval_result in evaluations:
                    flat_data.append({
                        "Paper_Filename": paper_filename,
                        "Criterion_ID": eval_result.get("criterion_id", "N/A"),
                        "Criterion_Name": eval_result.get("criterion_name", "N/A"),
                        "Assigned_LLM_Provider": eval_result.get("llm_provider", "N/A"),
                        "Assigned_LLM_Model": eval_result.get("model_name", "N/A"),
                        "Score": eval_result.get("score", "N/A"),
                        "Max_Points": eval_result.get("max_points", "N/A"),
                        "Justification": eval_result.get("justification", "N/A"),
                        "Evaluation_Errors": ""
                    })
            
            if errors:
                 for error_msg in errors:
                    flat_data.append({
                        "Paper_Filename": paper_filename,
                        "Criterion_ID": "ERROR",
                        "Criterion_Name": "System Error",
                        "Assigned_LLM_Provider": "N/A",
                        "Assigned_LLM_Model": "N/A",
                        "Score": "N/A",
                        "Max_Points": "N/A",
                        "Justification": "An error occurred during processing.",
                        "Evaluation_Errors": error_msg
                    })

        if not flat_data:
            print("No data to write to CSV after processing.")
            return None

        df = pd.DataFrame(flat_data)
        # Define column order for better readability
        column_order = [
            "Paper_Filename", "Criterion_ID", "Criterion_Name", 
            "Score", "Max_Points", "Justification", 
            "Assigned_LLM_Provider", "Assigned_LLM_Model", "Evaluation_Errors"
        ]
        # Reorder columns, only including those present in the DataFrame to avoid errors
        df = df.reindex(columns=[col for col in column_order if col in df.columns])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{filename_prefix}_{timestamp}.csv"
        report_path = os.path.join(self.report_dir, report_filename)
        
        try:
            df.to_csv(report_path, index=False, encoding='utf-8')
            print(f"Report generated successfully: {report_path}")
            return report_path
        except Exception as e:
            print(f"Error generating CSV report: {e}")
            return None

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    print("CSVReporter class defined.")
    # Create a dummy reports directory
    if not os.path.exists("/home/ubuntu/academic_evaluator/reports"): 
        os.makedirs("/home/ubuntu/academic_evaluator/reports")

    reporter = CSVReporter()
    sample_data = [
        {
            "pdf_path": "/path/to/paper1.pdf",
            "evaluations": [
                {"criterion_id": "intro", "criterion_name": "Introduction", "score": 1, "max_points": 2, "justification": "Good intro.", "llm_provider": "openai", "model_name": "gpt-4.1-turbo"},
                {"criterion_id": "sota", "criterion_name": "SOTA", "score": 2, "max_points": 3, "justification": "Excellent SOTA.", "llm_provider": "gemini", "model_name": "gemini-1.5-flash"}
            ],
            "errors": []
        },
        {
            "pdf_path": "/path/to/paper2.pdf",
            "evaluations": [],
            "errors": ["Failed to parse PDF."]
        }
    ]
    report_file = reporter.generate_report(sample_data, filename_prefix="test_evaluation_report")
    if report_file:
        print(f"Test report generated: {report_file}")
        # You can then check the content of this file.
        # For example, using file_read tool or by inspecting it manually if you have access.
    else:
        print("Test report generation failed.")

