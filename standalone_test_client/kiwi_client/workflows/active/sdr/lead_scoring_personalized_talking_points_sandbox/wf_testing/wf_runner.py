import json
import asyncio
import csv
import argparse
import sys
import time
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any, Literal
import logging

# --- Test Execution Logic ---
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

from kiwi_client.workflows.active.sdr.lead_scoring_personalized_talking_points_sandbox.wf_lead_scoring_personalized_talking_points_json import (
    workflow_graph_schema
)

logger = logging.getLogger(__name__)

def load_csv_data(csv_filename: str, start_row: int = 0, end_row: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load CSV data and convert to the required format for workflow processing.
    
    Args:
        csv_filename: Path to the CSV file containing lead data
        start_row: Starting row index (0-based, excluding header)
        end_row: Ending row index (0-based, exclusive). If None, process all rows from start_row
        
    Returns:
        List of lead dictionaries with required fields
        
    Expected CSV columns (supports aliases):
        - linkedinUrl: LinkedIn profile URL (aliases: 'linkedinUrl', 'LinkedIn URL', 'LinkedIn')
        - Company: Company name (aliases: 'Company', 'Company Name', 'Organization')
        - firstName: First name (aliases: 'firstName', 'First Name', 'First')
        - lastName: Last name (aliases: 'lastName', 'Last Name', 'Last')
        - companyWebsite: Company website URL (aliases: 'companyWebsite', 'Company website', 'Website', 'Company Website')
        - emailId: Email address (aliases: 'emailId', 'Email ID', 'Email', 'Email Address')
        - jobTitle: Job title/role (aliases: 'jobTitle', 'Job Title', 'Title', 'Position')
    """
    try:
        # Read CSV file using pandas for better handling
        df = pd.read_csv(csv_filename)
        
        # Apply row range filtering
        if end_row is not None:
            df = df.iloc[start_row:end_row]
        else:
            df = df.iloc[start_row:]
            
        logger.info(f"Loaded {len(df)} rows from CSV file: {csv_filename}")
        logger.info(f"Row range: {start_row} to {end_row if end_row else 'end'}")
        logger.info(f"Available columns: {list(df.columns)}")
        
        # Define column aliases mapping - maps standard field names to possible CSV column names
        column_aliases = {
            'linkedinUrl': ['linkedinUrl', 'LinkedIn URL', 'LinkedIn', 'linkedin_url', 'linkedin'],
            'Company': ['Company', 'Company Name', 'Organization', 'company', 'company_name'],
            'firstName': ['firstName', 'First Name', 'First', 'first_name', 'first'],
            'lastName': ['lastName', 'Last Name', 'Last', 'last_name', 'last'],
            'companyWebsite': ['companyWebsite', 'Company website', 'Website', 'Company Website', 'company_website', 'website'],
            'emailId': ['emailId', 'Email ID', 'Email', 'Email Address', 'email_id', 'email', 'email_address'],
            'jobTitle': ['jobTitle', 'Job Title', 'Title', 'Position', 'job_title', 'title', 'position']
        }
        
        # Create mapping from CSV columns to standard field names
        column_mapping = {}
        available_columns = list(df.columns)
        
        for standard_field, possible_names in column_aliases.items():
            found_column = None
            for possible_name in possible_names:
                if possible_name in available_columns:
                    found_column = possible_name
                    break
            
            if found_column:
                column_mapping[standard_field] = found_column
                logger.info(f"Mapped '{standard_field}' to CSV column '{found_column}'")
            else:
                logger.warning(f"Could not find column for '{standard_field}'. Tried: {possible_names}")
        
        # Check if all required fields have been mapped
        required_fields = ['linkedinUrl', 'Company', 'firstName', 'lastName', 'companyWebsite', 'emailId', 'jobTitle']
        missing_fields = [field for field in required_fields if field not in column_mapping]
        
        if missing_fields:
            available_cols_str = ", ".join(available_columns)
            missing_aliases = {field: column_aliases[field] for field in missing_fields}
            raise ValueError(
                f"Could not map required fields to CSV columns: {missing_fields}\n"
                f"Available CSV columns: {available_cols_str}\n"
                f"Expected column names for missing fields: {missing_aliases}"
            )
        
        # Convert to list of dictionaries using the column mapping
        leads_data = []
        
        for _, row in df.iterrows():
            lead_data = {}
            for standard_field, csv_column in column_mapping.items():
                # Handle NaN values by converting to empty string
                value = row[csv_column]
                if pd.isna(value):
                    lead_data[standard_field] = ""
                else:
                    lead_data[standard_field] = str(value).strip()
            
            leads_data.append(lead_data)
        
        logger.info(f"Successfully processed {len(leads_data)} leads from CSV")
        logger.info(f"Column mappings used: {column_mapping}")
        return leads_data
        
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_filename}")
        raise
    except Exception as e:
        logger.error(f"Error loading CSV file {csv_filename}: {str(e)}")
        raise


def save_results_to_csv(final_run_outputs: Dict[str, Any], output_csv_filename: str) -> None:
    """
    Save workflow results to CSV file with comprehensive lead data and talking points.
    
    Args:
        final_run_outputs: Final workflow outputs containing processed_leads
        output_csv_filename: Path to output CSV file
    """
    try:
        processed_leads = final_run_outputs.get('processed_leads', [])
        
        if not processed_leads:
            logger.warning("No processed leads found in workflow outputs")
            return
        
        # Prepare CSV rows with flattened data structure
        csv_rows = []
        
        for lead in processed_leads:
            row = {}
            
            # Basic lead information
            row['linkedinUrl'] = lead.get('linkedinUrl', '')
            row['Company'] = lead.get('Company', '')
            row['firstName'] = lead.get('firstName', '')
            row['lastName'] = lead.get('lastName', '')
            row['companyWebsite'] = lead.get('companyWebsite', '')
            row['emailId'] = lead.get('emailId', '')
            row['jobTitle'] = lead.get('jobTitle', '')
            
            # Qualification result fields - handle both dict and JSON string formats
            qualification_result_raw = lead.get('qualification_result', {})
            if isinstance(qualification_result_raw, str):
                try:
                    qualification_result = json.loads(qualification_result_raw)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse qualification_result as JSON: {qualification_result_raw}")
                    qualification_result = {}
            elif isinstance(qualification_result_raw, dict):
                qualification_result = qualification_result_raw
            else:
                logger.warning(f"Unexpected qualification_result type: {type(qualification_result_raw)}")
                qualification_result = {}
                
            row['industry'] = qualification_result.get('industry', '') if isinstance(qualification_result, dict) else ''
            row['company_info'] = qualification_result.get('company_info', '') if isinstance(qualification_result, dict) else ''
            row['funding_stage'] = qualification_result.get('funding_stage', '') if isinstance(qualification_result, dict) else ''
            row['individual_info'] = qualification_result.get('individual_info', '') if isinstance(qualification_result, dict) else ''
            row['employee_count_estimate'] = qualification_result.get('employee_count_estimate', '') if isinstance(qualification_result, dict) else ''
            row['qualification_reasoning'] = qualification_result.get('qualification_reasoning', '') if isinstance(qualification_result, dict) else ''
            row['qualification_check_passed'] = qualification_result.get('qualification_check_passed', False) if isinstance(qualification_result, dict) else False
            
            # ContentQ analysis (truncated for CSV readability)
            contentq_analysis = lead.get('contentq_and_content_analysis', '')
            row['contentq_analysis_summary'] = contentq_analysis[:500] + '...' if len(contentq_analysis) > 500 else contentq_analysis
            
            # Strategic analysis (truncated for CSV readability)  
            strategic_analysis = lead.get('strategic_analysis', '')
            row['strategic_analysis_summary'] = strategic_analysis[:500] + '...' if len(strategic_analysis) > 500 else strategic_analysis
            
            # Talking points result - handle both dict and JSON string formats
            talking_points_result_raw = lead.get('talking_points_result', {})
            if isinstance(talking_points_result_raw, str):
                try:
                    talking_points_result = json.loads(talking_points_result_raw)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse talking_points_result as JSON: {talking_points_result_raw}")
                    talking_points_result = {}
            elif isinstance(talking_points_result_raw, dict):
                talking_points_result = talking_points_result_raw
            else:
                logger.warning(f"Unexpected talking_points_result type: {type(talking_points_result_raw)}")
                talking_points_result = {}
                
            row['contentq_score'] = talking_points_result.get('contentq_score', 0.0) if isinstance(talking_points_result, dict) else 0.0
            row['contentq_score_text'] = talking_points_result.get('contentq_score_text', '') if isinstance(talking_points_result, dict) else ''
            row['contentq_pitch'] = talking_points_result.get('contentq_pitch', '') if isinstance(talking_points_result, dict) else ''
            row['email_subject_line'] = talking_points_result.get('email_subject_line', '') if isinstance(talking_points_result, dict) else ''
            
            # Individual talking points
            row['talking_point_1'] = talking_points_result.get('talking_point_1', '') if isinstance(talking_points_result, dict) else ''
            row['talking_point_2'] = talking_points_result.get('talking_point_2', '') if isinstance(talking_points_result, dict) else ''
            row['talking_point_3'] = talking_points_result.get('talking_point_3', '') if isinstance(talking_points_result, dict) else ''
            row['talking_point_4'] = talking_points_result.get('talking_point_4', '') if isinstance(talking_points_result, dict) else ''
            
            # Reasoning for talking points (truncated)
            for i in range(1, 5):
                reasoning_key = f'talking_point_{i}_reasoning_citations'
                reasoning = talking_points_result.get(reasoning_key, '') if isinstance(talking_points_result, dict) else ''
                row[f'talking_point_{i}_reasoning'] = reasoning[:300] + '...' if len(reasoning) > 300 else reasoning
            
            # ContentQ pitch reasoning
            pitch_reasoning = talking_points_result.get('contentq_pitch_reasoning_citations', '') if isinstance(talking_points_result, dict) else ''
            row['contentq_pitch_reasoning'] = pitch_reasoning[:300] + '...' if len(pitch_reasoning) > 300 else pitch_reasoning
            
            # Subject line reasoning
            subject_reasoning = talking_points_result.get('subject_line_reasoning', '') if isinstance(talking_points_result, dict) else ''
            row['subject_line_reasoning'] = subject_reasoning[:200] + '...' if len(subject_reasoning) > 200 else subject_reasoning
            
            csv_rows.append(row)
        
        # Write to CSV file
        if csv_rows:
            fieldnames = list(csv_rows[0].keys())
            
            with open(output_csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)
            
            logger.info(f"Successfully saved {len(csv_rows)} processed leads to: {output_csv_filename}")
            
            # Log summary statistics
            total_qualified = len([row for row in csv_rows if row['qualification_check_passed']])
            avg_score = sum(float(row['contentq_score']) for row in csv_rows if row['contentq_score']) / len(csv_rows)
            
            logger.info(f"Summary: {total_qualified}/{len(csv_rows)} leads qualified, Average ContentQ Score: {avg_score:.1f}")
        else:
            logger.warning("No data to write to CSV file")
            
    except Exception as e:
        logger.error(f"Error saving results to CSV file {output_csv_filename}: {str(e)}")
        raise


# Example Test Inputs (kept for backward compatibility)
TEST_INPUTS = {
    "leads_to_process": [
        {
            "linkedinUrl": "https://www.linkedin.com/in/ACoAAAGSbXUBOy1FuiRw9wcaJ-_24TnS_u4dgS8",
            "Company": "Metadata.Io",
            "firstName": "Dee", 
            "lastName": "Acosta 🤖",
            "companyWebsite": "metadata.io",
            "emailId": "dee.acosta@metadata.io",
            "jobTitle": "Ad AI, Sales, and GTM	"
        },
        {
            "linkedinUrl": "https://www.linkedin.com/in/ACoAAAAMYK4BCyNT23Ui4i6ijdr7-Xu2s8H1pa4",
            "Company": "Stacklok",
            "firstName": "Christine",
            "lastName": "Simonini", 
            "companyWebsite": "stacklok.com",
            "emailId": "csimonini@appomni.com",
            "jobTitle": "Advisor"
        },
        {
            "linkedinUrl": "https://www.linkedin.com/in/ACoAACngUhwBxcSAdAIis1EyHyGe0oSxoLg0lVE",
            "Company": "Cresta",
            "firstName": "Kurtis",
            "lastName": "Wagner",
            "companyWebsite": "cresta.com", 
            "emailId": "kurtis@cresta.ai",
            "jobTitle": "AI Agent Architect"
        }
    ]
}

async def validate_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """
    Custom validation function for the workflow outputs.
    
    Validates that:
    1. Leads were processed through qualification
    2. Qualified leads received ContentQ scoring and talking points
    3. Final results contain all required fields for qualified leads
    4. Output structure includes lead information and talking points
    """
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating lead scoring workflow outputs...")
    
    # Check if we have the expected output fields
    assert 'processed_leads' in outputs, "Validation Failed: 'processed_leads' key missing."
    # assert 'original_leads' in outputs, "Validation Failed: 'original_leads' key missing."
    
    # original_leads = outputs.get('original_leads', [])
    processed_results = outputs.get('processed_leads', [])
    
    # logger.info(f"Original leads count: {len(original_leads)}")
    logger.info(f"Processed results count: {len(processed_results)}")
    
    # Validate that we have some processed results
    assert len(processed_results) > 0, "Validation Failed: No leads were processed successfully."
    
    # Validate the structure of processed results
    for i, result in enumerate(processed_results):
        logger.info(f"Validating result {i+1}...")
        
        # Check for required lead information (from passthrough data)
        required_lead_fields = ['Company', 'firstName', 'lastName', 'emailId', 'jobTitle']
        for field in required_lead_fields:
            assert field in result, f"Validation Failed: Missing lead field '{field}' in result {i+1}"
        
        # Check for talking points result
        assert 'talking_points_result' in result, f"Validation Failed: Missing talking_points_result in result {i+1}"
        
        talking_points = result['talking_points_result']
        required_talking_point_fields = [
            'contentq_score', 'contentq_score_text', 'talking_point_1', 'talking_point_1_reasoning_citations', 
            'talking_point_2', 'talking_point_2_reasoning_citations', 'talking_point_3', 'talking_point_3_reasoning_citations',
            'talking_point_4', 'talking_point_4_reasoning_citations', 'contentq_pitch', 'contentq_pitch_reasoning_citations',
            'email_subject_line', 'subject_line_reasoning'
        ]
        
        for field in required_talking_point_fields:
            assert field in talking_points, f"Validation Failed: Missing talking point field '{field}' in result {i+1}"
            if field == 'contentq_score':
                assert talking_points[field] > 0, f"Validation Failed: ContentQ score is less than 0 in result {i+1}"
                continue
            assert len(talking_points[field]) > 0, f"Validation Failed: Empty talking point field '{field}' in result {i+1}"
        
        logger.info(f"  ✓ Lead: {result['firstName']} {result['lastName']} from {result['Company']}")
        logger.info(f"  ✓ Email Subject: {talking_points['email_subject_line']}")
        logger.info(f"  ✓ ContentQ Pitch: {talking_points['contentq_pitch'][:100]}...")
        
        # Check for ContentQ score from final talking points
        logger.info(f"  ✓ ContentQ Score: {talking_points['contentq_score']}")
        logger.info(f"  ✓ Talking Point 1: {talking_points['talking_point_1'][:80]}...")
        logger.info(f"  ✓ Has reasoning for all points: {len([f for f in required_talking_point_fields if 'reasoning' in f])} reasoning fields")
    
    logger.info("✓ All validation checks passed successfully!")
    return True

async def run_batch_workflow(input_csv: str,
                             output_csv: str, 
                             batch_start: int,
                             batch_end: int,
                             batch_number: int,
                             total_batches: int) -> tuple:
    """
    Run a single batch of the workflow.
    
    Returns:
        Tuple of (status, outputs, duration, leads_processed)
    """
    batch_start_time = time.time()
    batch_size = batch_end - batch_start
    test_name = f"Batch {batch_number}/{total_batches}"
    
    print(f"  Loading {batch_size} leads from rows {batch_start}-{batch_end-1}...")
    
    try:
        # Load CSV data for this batch
        leads_data = load_csv_data(input_csv, batch_start, batch_end)
        initial_inputs = {"leads_to_process": leads_data}
        
        print(f"  Running workflow for {len(leads_data)} leads...")
        
        # Run workflow for this batch
        final_run_status_obj, final_run_outputs = await run_single_workflow(
            input_data=initial_inputs,
            test_name=test_name
        )
        
        # Save batch results to file
        leads_processed = 0
        if final_run_outputs and 'processed_leads' in final_run_outputs:
            save_results_to_csv(final_run_outputs, output_csv)
            leads_processed = len(final_run_outputs['processed_leads'])
            print(f"  Saved {leads_processed} results to: {Path(output_csv).name}")
        else:
            print(f"  ⚠️  No results to save")
        
        batch_duration = time.time() - batch_start_time
        
        return final_run_status_obj, final_run_outputs, batch_duration, leads_processed
        
    except Exception as e:
        batch_duration = time.time() - batch_start_time
        print(f"  ❌ Batch failed: {str(e)}")
        return None, None, batch_duration, 0


def combine_existing_batch_files(batch_folder: str, output_csv: str) -> None:
    """
    Combine all existing batch CSV files in the batch folder into a single output file.
    
    Args:
        batch_folder: Path to folder containing batch result files
        output_csv: Path to final combined output CSV file
    """
    batch_folder_path = Path(batch_folder)
    
    if not batch_folder_path.exists():
        print(f"❌ Batch folder does not exist: {batch_folder}")
        return
    
    # Find all CSV files in the batch folder
    batch_files = list(batch_folder_path.glob("batch_*.csv"))
    
    if not batch_files:
        print(f"❌ No batch files found in: {batch_folder}")
        return
    
    # Sort batch files by name to ensure consistent ordering
    batch_files.sort()
    batch_file_paths = [str(f) for f in batch_files]
    
    print(f"📁 Found {len(batch_files)} batch files in: {batch_folder}")
    for batch_file in batch_files:
        print(f"  - {batch_file.name}")
    
    # Use existing combine function
    combine_batch_results(batch_file_paths, output_csv)
    
    print(f"✅ Combined {len(batch_files)} batch files into: {output_csv}")


def combine_batch_results(batch_output_files: List[str], final_output_csv: str) -> None:
    """
    Combine results from multiple batch CSV files into a single output file.
    
    Args:
        batch_output_files: List of batch CSV file paths
        final_output_csv: Path to final combined output CSV file
    """
    logger.info(f"Combining {len(batch_output_files)} batch result files into: {final_output_csv}")
    
    combined_rows = []
    
    for i, batch_file in enumerate(batch_output_files):
        if not Path(batch_file).exists():
            logger.warning(f"Batch file does not exist: {batch_file}")
            continue
            
        try:
            # Read batch CSV file
            batch_df = pd.read_csv(batch_file)
            logger.info(f"Loaded {len(batch_df)} results from batch file {i+1}: {batch_file}")
            
            # Convert to list of dictionaries and add to combined results
            batch_rows = batch_df.to_dict('records')
            combined_rows.extend(batch_rows)
            
        except Exception as e:
            logger.error(f"Error reading batch file {batch_file}: {str(e)}")
            continue
    
    if combined_rows:
        # Write combined results to final CSV
        combined_df = pd.DataFrame(combined_rows)
        combined_df.to_csv(final_output_csv, index=False)
        
        logger.info(f"Successfully combined {len(combined_rows)} total results into: {final_output_csv}")
        
        # Log summary statistics
        total_qualified = len([row for row in combined_rows if row.get('qualification_check_passed', False)])
        avg_score = sum(float(row.get('contentq_score', 0)) for row in combined_rows if row.get('contentq_score')) / len(combined_rows) if combined_rows else 0
        
        logger.info(f"Final Summary: {total_qualified}/{len(combined_rows)} leads qualified, Average ContentQ Score: {avg_score:.1f}")
    else:
        logger.warning("No batch results to combine")

# counter = 0
async def run_single_workflow(input_data: Dict[str, Any], test_name: str) -> tuple:
    """
    Run a single workflow instance with given input data.
    
    Args:
        input_data: Input data for the workflow
        test_name: Name for this workflow test
        
    Returns:
        Tuple of (final_run_status_obj, final_run_outputs)
    """
    import io
    import contextlib
    
    logger.info(f"Starting {test_name}...")
    
    # Capture all stdout to prevent WorkflowRunRead objects from being printed
    captured_output = io.StringIO()
    
    try:
        with contextlib.redirect_stdout(captured_output):
            final_run_status_obj, final_run_outputs = await run_workflow_test(
                test_name=test_name,
                workflow_graph_schema=workflow_graph_schema,
                initial_inputs=input_data,
                expected_final_status=WorkflowRunStatus.COMPLETED,
                setup_docs=None,
                cleanup_docs=None,
                stream_intermediate_results=False,  # Suppress verbose workflow output
                dump_artifacts=False,  # Don't create artifact files
                poll_interval_sec=5,
                timeout_sec=900  # 10 minutes for comprehensive research and analysis
            )
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise
    
    # Log completion status without printing the full object
    status_str = str(final_run_status_obj.status) if final_run_status_obj else "None"
    logger.info(f"{test_name} completed with status: {status_str}")
    
    return final_run_status_obj, final_run_outputs


def print_partial_statistics(overall_start_time: float, 
                            batch_timings: List[Dict],
                            total_leads_processed: int,
                            successful_batches: int,
                            failed_batches: int,
                            total_delay_time: float,
                            current_batch: int,
                            total_batches: int,
                            start_row: int,
                            batch_size: int) -> None:
    """
    Print partial statistics when job stops due to failure.
    
    Args:
        overall_start_time: Start time of the overall job
        batch_timings: List of batch timing data
        total_leads_processed: Total leads processed before failure
        successful_batches: Number of successful batches
        failed_batches: Number of failed batches
        total_delay_time: Total artificial delay time
        current_batch: Current batch number where failure occurred
        total_batches: Total planned batches
        start_row: Starting row of processing
        batch_size: Batch size
    """
    current_time = time.time()
    partial_execution_time = current_time - overall_start_time
    
    # Calculate pure workflow time from successful batches
    successful_batch_timings = [b for b in batch_timings if b['leads_processed'] > 0]
    pure_workflow_time = sum(b['duration'] for b in successful_batch_timings)
    
    print(f"\n{'='*60}")
    print(f"JOB STOPPED DUE TO BATCH FAILURE - PARTIAL STATISTICS")
    print(f"{'='*60}")
    
    print(f"📊 PROGRESS AT FAILURE:")
    print(f"  Batches completed: {successful_batches}/{total_batches}")
    print(f"  Batches failed: {failed_batches}")
    print(f"  Current batch: {current_batch}")
    print(f"  Leads processed: {total_leads_processed}")
    
    # Calculate processed rows
    processed_rows = successful_batches * batch_size
    if current_batch > 1:
        last_successful_row = start_row + processed_rows - 1
        print(f"  Rows processed: {start_row} to {last_successful_row} ({processed_rows} rows)")
    else:
        print(f"  Rows processed: None (failed on first batch)")
    
    print(f"\n⏰ TIMING AT FAILURE:")
    print(f"  Total execution time: {partial_execution_time:.1f} seconds ({partial_execution_time/60:.1f} minutes)")
    print(f"  Pure workflow time: {pure_workflow_time:.1f} seconds ({pure_workflow_time/60:.1f} minutes)")
    print(f"  Artificial delay time: {total_delay_time:.1f} seconds ({total_delay_time/60:.1f} minutes)")
    
    if total_leads_processed > 0:
        print(f"  Average time per lead: {pure_workflow_time/total_leads_processed:.1f} seconds")
        print(f"  Throughput: {total_leads_processed/(pure_workflow_time/3600):.1f} leads/hour")
    
    if successful_batch_timings:
        batch_durations = [b['duration'] for b in successful_batch_timings]
        print(f"  Average batch duration: {sum(batch_durations)/len(batch_durations):.1f} seconds")
        print(f"  Fastest batch: {min(batch_durations):.1f} seconds")
        print(f"  Slowest batch: {max(batch_durations):.1f} seconds")
    
    print(f"\n📈 SUCCESSFUL BATCHES BREAKDOWN:")
    if successful_batch_timings:
        for batch_timing in successful_batch_timings:
            batch_num = batch_timing['batch_num']
            duration = batch_timing['duration']
            leads = batch_timing['leads_processed']
            avg_time = batch_timing['avg_time_per_lead']
            print(f"  Batch {batch_num:2d}: {duration:5.1f}s total, {leads:2d} leads, {avg_time:4.1f}s/lead")
    else:
        print(f"  No batches completed successfully")
    
    print(f"{'='*60}")


async def run_single_batch_with_semaphore(
    semaphore: asyncio.Semaphore,
    input_csv: str,
    batch_output_file: str,
    batch_start: int,
    batch_end: int,
    batch_num: int,
    total_batches: int,
    delay: int = 0,
    is_sequential: bool = False
) -> Dict[str, Any]:
    """
    Run a single batch workflow with semaphore control for both parallel and sequential execution.
    
    Args:
        semaphore: Asyncio semaphore to control concurrency
        delay: Delay in seconds after batch completion (only for sequential mode)
        is_sequential: If True, adds detailed progress reporting and delays
    
    Returns:
        Dictionary containing batch results and timing information
    """
    async with semaphore:
        if is_sequential:
            print(f"{'='*60}")
            print(f"BATCH {batch_num}/{total_batches}: Processing rows {batch_start}-{batch_end-1}")
            print(f"{'='*60}")
        else:
            print(f"🔄 Starting Batch {batch_num}/{total_batches}: rows {batch_start}-{batch_end-1}")
        
        batch_status, batch_outputs, batch_duration, leads_processed = await run_batch_workflow(
            input_csv=input_csv,
            output_csv=batch_output_file,
            batch_start=batch_start,
            batch_end=batch_end,
            batch_number=batch_num,
            total_batches=total_batches
        )
        
        # Return comprehensive batch result
        result = {
            'batch_num': batch_num,
            'batch_start': batch_start,
            'batch_end': batch_end,
            'status': batch_status,
            'outputs': batch_outputs,
            'duration': batch_duration,
            'leads_processed': leads_processed,
            'avg_time_per_lead': batch_duration / leads_processed if leads_processed > 0 else 0,
            'output_file': batch_output_file,
            'success': batch_status and batch_status.status == WorkflowRunStatus.COMPLETED if batch_status else False,
            'actual_delay_time': 0.0  # Will be updated if delay is applied
        }
        
        # Print completion status
        if result['success']:
            print(f"✅ Batch {batch_num} completed in {batch_duration:.1f}s ({leads_processed} leads)")
        else:
            print(f"❌ Batch {batch_num} failed after {batch_duration:.1f}s")
        
        if is_sequential:
            print(f"Batch {batch_num} completed. Progress: {batch_num}/{total_batches} batches")
            
            # Add delay between batches (except after the last batch) for sequential mode
            if batch_num < total_batches and delay > 0:
                print(f"⏳ Waiting {delay} seconds before next batch...")
                delay_start_time = time.time()
                await asyncio.sleep(delay)
                delay_end_time = time.time()
                actual_delay_time = delay_end_time - delay_start_time
                result['actual_delay_time'] = actual_delay_time
            print()
        
        return result


async def run_batches_unified(
    input_csv: str,
    batch_folder_path: Path,
    output_csv: str,
    start_row: int,
    actual_end_row: int,
    batch_size: int,
    total_batches: int,
    batch_parallelism_limit: int,
    stop_on_failure: bool,
    batch_output_files: List[str],
    delay: int = 0,
    overall_start_time: float = None
) -> tuple:
    """
    Run batches with semaphore-controlled concurrency (unified for both parallel and sequential modes).
    
    Args:
        delay: Inter-batch delay in seconds (only applied when batch_parallelism_limit=1)
        overall_start_time: Start time for partial statistics (only used for sequential mode failures)
    
    Returns:
        Tuple of (successful_batches, failed_batches, batch_timings, total_leads_processed[, total_delay_time])
        Returns total_delay_time only when batch_parallelism_limit=1 (sequential mode)
    """
    # Create semaphore to limit concurrent batches
    semaphore = asyncio.Semaphore(batch_parallelism_limit)
    is_sequential = batch_parallelism_limit == 1
    
    # Create batch tasks
    batch_tasks = []
    for batch_num in range(1, total_batches + 1):
        batch_start = start_row + (batch_num - 1) * batch_size
        batch_end = min(batch_start + batch_size, actual_end_row)
        
        # Create batch-specific output file
        output_suffix = Path(output_csv).suffix
        batch_output_file = batch_folder_path / f"batch_{batch_num:03d}_rows_{batch_start}-{batch_end-1}{output_suffix}"
        batch_output_files.append(str(batch_output_file))
        
        # Create task for this batch
        task = run_single_batch_with_semaphore(
            semaphore=semaphore,
            input_csv=input_csv,
            batch_output_file=str(batch_output_file),
            batch_start=batch_start,
            batch_end=batch_end,
            batch_num=batch_num,
            total_batches=total_batches,
            delay=delay,
            is_sequential=is_sequential
        )
        batch_tasks.append(task)
    
    print(f"📊 Created {len(batch_tasks)} batch tasks for {'sequential' if is_sequential else 'parallel'} execution")
    print(f"⚡ Running with concurrency limit: {batch_parallelism_limit}")
    print()
    
    # Execute all batches concurrently
    try:
        if stop_on_failure:
            # Use gather() with return_exceptions=False to stop on first failure
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=False)
        else:
            # Use gather() with return_exceptions=True to collect all results
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
    except Exception as e:
        # Handle case where stop_on_failure=True and a batch failed
        print(f"❌ Batch execution stopped due to failure: {str(e)}")
        
        # For sequential mode, provide partial statistics
        if is_sequential and stop_on_failure and overall_start_time:
            print_partial_statistics(
                overall_start_time=overall_start_time,
                batch_timings=[],  # No completed batches to report
                total_leads_processed=0,
                successful_batches=0,
                failed_batches=1,
                total_delay_time=0.0,
                current_batch=1,  # Failed on first batch
                total_batches=total_batches,
                start_row=start_row,
                batch_size=batch_size
            )
        
        if stop_on_failure:
            raise RuntimeError(f"Batch processing stopped due to batch failure: {str(e)}")
        batch_results = []
    
    # Process results
    successful_batches = 0
    failed_batches = 0
    batch_timings = []
    total_leads_processed = 0
    total_delay_time = 0.0  # Track delay time for sequential mode
    
    for i, result in enumerate(batch_results):
        if isinstance(result, Exception):
            # Handle exception results (when return_exceptions=True)
            failed_batches += 1
            batch_num = i + 1
            print(f"❌ Batch {batch_num} failed with exception: {str(result)}")
            
            # For sequential mode with stop_on_failure, provide partial statistics
            if is_sequential and stop_on_failure and overall_start_time:
                print_partial_statistics(
                    overall_start_time=overall_start_time,
                    batch_timings=batch_timings,
                    total_leads_processed=total_leads_processed,
                    successful_batches=successful_batches,
                    failed_batches=failed_batches,
                    total_delay_time=total_delay_time,
                    current_batch=batch_num,
                    total_batches=total_batches,
                    start_row=start_row,
                    batch_size=batch_size
                )
                raise RuntimeError(f"Job stopped due to batch failure. Batch {batch_num} failed")
            
            # Add failed batch to timings with 0 stats
            batch_timings.append({
                'batch_num': batch_num,
                'duration': 0.0,
                'leads_processed': 0,
                'avg_time_per_lead': 0.0
            })
        elif isinstance(result, dict):
            # Handle successful batch results
            if result['success']:
                successful_batches += 1
                total_leads_processed += result['leads_processed']
            else:
                failed_batches += 1
                
                # For sequential mode with stop_on_failure, provide partial statistics
                if is_sequential and stop_on_failure and overall_start_time:
                    print_partial_statistics(
                        overall_start_time=overall_start_time,
                        batch_timings=batch_timings,
                        total_leads_processed=total_leads_processed,
                        successful_batches=successful_batches,
                        failed_batches=failed_batches,
                        total_delay_time=total_delay_time,
                        current_batch=result['batch_num'],
                        total_batches=total_batches,
                        start_row=start_row,
                        batch_size=batch_size
                    )
                    raise RuntimeError(f"Job stopped due to batch failure. Batch {result['batch_num']} failed")
            
            # Track delay time for sequential mode
            total_delay_time += result.get('actual_delay_time', 0.0)
            
            # Add to batch timings
            batch_timings.append({
                'batch_num': result['batch_num'],
                'duration': result['duration'],
                'leads_processed': result['leads_processed'],
                'avg_time_per_lead': result['avg_time_per_lead']
            })
        else:
            # Handle unexpected result type
            failed_batches += 1
            batch_num = i + 1
            print(f"❌ Batch {batch_num} returned unexpected result type: {type(result)}")
    
    # Sort batch timings by batch number for consistent reporting
    batch_timings.sort(key=lambda x: x['batch_num'])
    
    execution_mode = "SEQUENTIAL" if is_sequential else "PARALLEL"
    print(f"\n📈 {execution_mode} EXECUTION SUMMARY:")
    print(f"  Total batches: {total_batches}")
    print(f"  Successful: {successful_batches}")
    print(f"  Failed: {failed_batches}")
    print(f"  Total leads processed: {total_leads_processed}")
    if is_sequential and total_delay_time > 0:
        print(f"  Total delay time: {total_delay_time:.1f}s")
    print()
    
    # Return appropriate tuple based on mode (sequential mode includes delay time)
    if is_sequential:
        return successful_batches, failed_batches, batch_timings, total_leads_processed, total_delay_time
    else:
        return successful_batches, failed_batches, batch_timings, total_leads_processed


async def main_batch_lead_scoring(input_csv: Optional[str] = None,
                                  output_csv: Optional[str] = None,
                                  batch_folder: Optional[str] = None,
                                  start_row: int = 0,
                                  end_row: Optional[int] = None,
                                  batch_size: int = 20,
                                  delay: int = 45,
                                  stop_on_failure: bool = True,
                                  run_batches_in_parallel: bool = True,
                                  batch_parallelism_limit: int = 5):
    """
    Main function for batch processing lead scoring workflow.
    
    Args:
        input_csv: Path to input CSV file with lead data
        output_csv: Path to output CSV file for results  
        batch_folder: Folder to store individual batch result files
        start_row: Starting row index for processing (0-based, excluding header)
        end_row: Ending row index for processing (0-based, exclusive)
        batch_size: Number of leads to process in each batch
        delay: Delay in seconds between consecutive batch workflows (ignored for parallel processing)
        stop_on_failure: If True, stop processing and throw exception on batch failure
        run_batches_in_parallel: If True, run batches concurrently instead of sequentially
        batch_parallelism_limit: Maximum number of concurrent batches when parallel processing is enabled
    """
    print(f"--- Starting Batch Lead Scoring Workflow ---")
    print(f"Configuration:")
    print(f"  Input CSV: {input_csv if input_csv else 'Using default test data'}")
    print(f"  Output CSV: {output_csv if output_csv else 'No output file'}")
    print(f"  Batch folder: {batch_folder}")
    print(f"  Row range: {start_row} to {end_row if end_row else 'end'}")
    print(f"  Batch size: {batch_size}")
    print(f"  Parallel processing: {run_batches_in_parallel}")
    if run_batches_in_parallel:
        print(f"  Max concurrent batches: {batch_parallelism_limit}")
        if delay > 0:
            print(f"  Inter-batch delay: {delay} seconds (ignored for parallel processing)")
    else:
        print(f"  Inter-batch delay: {delay} seconds")
    print(f"  Stop on failure: {stop_on_failure}")
    print()
    
    # Start overall timing
    overall_start_time = time.time()
    
    # Handle case where no CSV is provided (use default test data)
    if not input_csv or not Path(input_csv).exists():
        if input_csv:
            print(f"CSV file not found: {input_csv}")
        print("Using default test inputs (single workflow run)")
        
        # Run single workflow with default test data
        test_name = "Lead Scoring and Personalized Talking Points Generation"
        workflow_start_time = time.time()
        final_run_status_obj, final_run_outputs = await run_single_workflow(
            input_data=TEST_INPUTS,
            test_name=test_name
        )
        workflow_end_time = time.time()
        
        # Save results if output file specified
        if output_csv and final_run_outputs:
            print(f"Saving results to: {output_csv}")
            save_results_to_csv(final_run_outputs, output_csv)
            print(f"Results saved successfully to: {output_csv}")
        
        # Calculate and display timing stats for single run
        overall_duration = time.time() - overall_start_time
        workflow_duration = workflow_end_time - workflow_start_time
        leads_processed = len(final_run_outputs.get('processed_leads', [])) if final_run_outputs else 0
        
        print(f"\n{'='*60}")
        print(f"TIMING STATISTICS - SINGLE RUN")
        print(f"{'='*60}")
        print(f"Total execution time: {overall_duration:.1f} seconds ({overall_duration/60:.1f} minutes)")
        print(f"Workflow execution time: {workflow_duration:.1f} seconds ({workflow_duration/60:.1f} minutes)")
        print(f"Leads processed: {leads_processed}")
        if leads_processed > 0:
            print(f"Average time per lead: {workflow_duration/leads_processed:.1f} seconds")
        print(f"{'='*60}")
        
        return final_run_status_obj, final_run_outputs
    
    # Calculate total rows to process and number of batches
    df = pd.read_csv(input_csv)
    total_rows = len(df)
    
    # Determine actual end row
    actual_end_row = min(end_row if end_row is not None else total_rows, total_rows)
    
    # Calculate batch ranges
    total_leads_to_process = actual_end_row - start_row
    total_batches = (total_leads_to_process + batch_size - 1) // batch_size  # Ceiling division
    
    print(f"Batch Processing Plan:")
    print(f"  Total rows in CSV: {total_rows}")
    print(f"  Processing rows {start_row} to {actual_end_row-1} ({total_leads_to_process} leads)")
    print(f"  Batch size: {batch_size}")
    print(f"  Total batches: {total_batches}")
    print()
    
    # Create batch results folder
    batch_folder_path = Path(batch_folder)
    batch_folder_path.mkdir(parents=True, exist_ok=True)
    print(f"Batch results will be stored in: {batch_folder_path.resolve()}")
    
    batch_output_files = []
    successful_batches = 0
    failed_batches = 0
    
    # Timing tracking for batches
    batch_processing_start_time = time.time()
    
    # Choose processing mode based on configuration - use unified batch processor
    if run_batches_in_parallel:
        print(f"🚀 Running {total_batches} batches in PARALLEL mode (max {batch_parallelism_limit} concurrent)")
        batch_result = await run_batches_unified(
            input_csv=input_csv,
            batch_folder_path=batch_folder_path,
            output_csv=output_csv,
            start_row=start_row,
            actual_end_row=actual_end_row,
            batch_size=batch_size,
            total_batches=total_batches,
            batch_parallelism_limit=batch_parallelism_limit,
            stop_on_failure=stop_on_failure,
            batch_output_files=batch_output_files,
            delay=0,  # No delays for parallel processing
            overall_start_time=overall_start_time
        )
        successful_batches, failed_batches, batch_timings, total_leads_processed = batch_result
        total_delay_time = 0.0  # No delays in parallel mode
    else:
        print(f"🐌 Running {total_batches} batches in SEQUENTIAL mode")
        batch_result = await run_batches_unified(
            input_csv=input_csv,
            batch_folder_path=batch_folder_path,
            output_csv=output_csv,
            start_row=start_row,
            actual_end_row=actual_end_row,
            batch_size=batch_size,
            total_batches=total_batches,
            batch_parallelism_limit=1,  # Sequential mode = semaphore limit 1
            stop_on_failure=stop_on_failure,
            batch_output_files=batch_output_files,
            delay=delay,
            overall_start_time=overall_start_time
        )
        successful_batches, failed_batches, batch_timings, total_leads_processed, total_delay_time = batch_result
    
    batch_processing_end_time = time.time()
    total_batch_processing_time = batch_processing_end_time - batch_processing_start_time
    
    # Calculate pure workflow time (excluding artificial delays for sequential mode)
    pure_workflow_time = total_batch_processing_time - total_delay_time
    
    # Combine all batch results into final output file
    print(f"{'='*60}")
    print(f"COMBINING BATCH RESULTS")
    print(f"{'='*60}")
    
    try:
        combine_batch_results(batch_output_files, output_csv)
        print(f"✓ All batch results combined into: {output_csv}")
        
        # Keep batch files for reference (don't clean up automatically)
        print(f"✓ Individual batch files preserved in: {batch_folder_path}")
        
    except Exception as e:
        logger.error(f"Error combining batch results: {str(e)}")
        print(f"✗ Error combining batch results: {str(e)}")
    
    # Calculate overall timing statistics
    overall_end_time = time.time()
    total_execution_time = overall_end_time - overall_start_time
    
    # Calculate statistics from successful batches only
    successful_batch_timings = [b for b in batch_timings if b['leads_processed'] > 0]
    
    # Final summary with comprehensive timing statistics
    print(f"{'='*60}")
    print(f"BATCH PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total batches: {total_batches}")
    print(f"Successful batches: {successful_batches}")
    print(f"Failed batches: {failed_batches}")
    print(f"Final merged results saved to: {output_csv}")
    print(f"Individual batch files available in: {batch_folder_path}")
    
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE TIMING STATISTICS")
    print(f"{'='*60}")
    
    # Overall timing
    print(f"📊 OVERALL PERFORMANCE:")
    print(f"  Total execution time: {total_execution_time:.1f} seconds ({total_execution_time/60:.1f} minutes)")
    print(f"  Pure workflow time: {pure_workflow_time:.1f} seconds ({pure_workflow_time/60:.1f} minutes)")
    print(f"  Artificial delay time: {total_delay_time:.1f} seconds ({total_delay_time/60:.1f} minutes)")
    print(f"  Setup/cleanup time: {total_execution_time - total_batch_processing_time:.1f} seconds")
    print(f"  Total leads processed: {total_leads_processed}")
    
    if total_leads_processed > 0:
        print(f"  Pure workflow time per lead: {pure_workflow_time/total_leads_processed:.1f} seconds")
        print(f"  Workflow throughput (excluding delays): {total_leads_processed/(pure_workflow_time/3600):.1f} leads/hour")
        print(f"  Overall throughput (including delays): {total_leads_processed/(total_execution_time/3600):.1f} leads/hour")
        
        # Time breakdown percentages
        print(f"\n⏰ TIME BREAKDOWN:")
        workflow_pct = (pure_workflow_time / total_execution_time) * 100
        delay_pct = (total_delay_time / total_execution_time) * 100
        setup_pct = ((total_execution_time - total_batch_processing_time) / total_execution_time) * 100
        
        print(f"  Pure workflow processing: {workflow_pct:.1f}% ({pure_workflow_time:.1f}s)")
        print(f"  Artificial delays: {delay_pct:.1f}% ({total_delay_time:.1f}s)")
        print(f"  Setup/cleanup overhead: {setup_pct:.1f}% ({total_execution_time - total_batch_processing_time:.1f}s)")
        
        if delay > 0:
            efficiency_ratio = pure_workflow_time / (pure_workflow_time + total_delay_time)
            print(f"  Processing efficiency: {efficiency_ratio*100:.1f}% (workflow time / total processing time)")
    
    # Batch-level statistics
    if successful_batch_timings:
        batch_durations = [b['duration'] for b in successful_batch_timings]
        per_lead_times = [b['avg_time_per_lead'] for b in successful_batch_timings if b['avg_time_per_lead'] > 0]
        
        print(f"\n⏱️  BATCH PERFORMANCE:")
        print(f"  Average batch duration: {sum(batch_durations)/len(batch_durations):.1f} seconds")
        print(f"  Fastest batch: {min(batch_durations):.1f} seconds")
        print(f"  Slowest batch: {max(batch_durations):.1f} seconds")
        print(f"  Batch duration std dev: {(sum([(x - sum(batch_durations)/len(batch_durations))**2 for x in batch_durations])/len(batch_durations))**0.5:.1f} seconds")
        
        if per_lead_times:
            print(f"\n🎯 PER-LEAD PERFORMANCE:")
            print(f"  Average time per lead: {sum(per_lead_times)/len(per_lead_times):.1f} seconds")
            print(f"  Fastest lead processing: {min(per_lead_times):.1f} seconds")
            print(f"  Slowest lead processing: {max(per_lead_times):.1f} seconds")
        
        print(f"\n📈 DETAILED BATCH BREAKDOWN:")
        for batch_timing in successful_batch_timings:
            batch_num = batch_timing['batch_num']
            duration = batch_timing['duration']
            leads = batch_timing['leads_processed']
            avg_time = batch_timing['avg_time_per_lead']
            print(f"  Batch {batch_num:2d}: {duration:5.1f}s total, {leads:2d} leads, {avg_time:4.1f}s/lead")
    
    # Performance projections
    if successful_batches > 0 and total_leads_processed > 0:
        avg_pure_batch_time = pure_workflow_time / successful_batches
        avg_leads_per_batch = total_leads_processed / successful_batches
        avg_delay_per_batch = total_delay_time / max(successful_batches - 1, 1)  # -1 because last batch has no delay
        
        print(f"\n🔮 PERFORMANCE PROJECTIONS:")
        print(f"  Pure workflow time estimates (excluding delays):")
        print(f"    100 leads: {(avg_pure_batch_time * 100 / avg_leads_per_batch)/60:.1f} minutes")
        print(f"    500 leads: {(avg_pure_batch_time * 500 / avg_leads_per_batch)/60:.1f} minutes")
        print(f"    1000 leads: {(avg_pure_batch_time * 1000 / avg_leads_per_batch)/60:.1f} minutes")
        
        if delay > 0:
            print(f"  Total time estimates (including {delay}s delays):")
            batches_for_100 = (100 + avg_leads_per_batch - 1) // avg_leads_per_batch  # Ceiling division
            batches_for_500 = (500 + avg_leads_per_batch - 1) // avg_leads_per_batch
            batches_for_1000 = (1000 + avg_leads_per_batch - 1) // avg_leads_per_batch
            
            total_time_100 = (avg_pure_batch_time * 100 / avg_leads_per_batch) + ((batches_for_100 - 1) * delay)
            total_time_500 = (avg_pure_batch_time * 500 / avg_leads_per_batch) + ((batches_for_500 - 1) * delay)
            total_time_1000 = (avg_pure_batch_time * 1000 / avg_leads_per_batch) + ((batches_for_1000 - 1) * delay)
            
            print(f"    100 leads: {total_time_100/60:.1f} minutes ({batches_for_100} batches)")
            print(f"    500 leads: {total_time_500/60:.1f} minutes ({batches_for_500} batches)")
            print(f"    1000 leads: {total_time_1000/60:.1f} minutes ({batches_for_1000} batches)")
    
    print(f"{'='*60}")
    
    return successful_batches, failed_batches




def parse_arguments():
    """Parse command line arguments for CSV input/output functionality."""
    parser = argparse.ArgumentParser(
        description="Lead Scoring and Personalized Talking Points Generation Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default hardcoded test data
  python wf_lead_scoring_personalized_talking_points.py
  
  # Process entire CSV file in batches (default: batch size 20, rows 0-250)
  python wf_lead_scoring_personalized_talking_points.py --input leads.csv --output results.csv
  
  # Process specific row range with custom batch size
  python wf_lead_scoring_personalized_talking_points.py --input leads.csv --output results.csv --start-row 10 --end-row 100 --batch-size 15
  
  # Process from row 5 to 50 with batch size 10 and custom batch folder
  python wf_lead_scoring_personalized_talking_points.py --input leads.csv --output results.csv --start-row 5 --end-row 50 --batch-size 10 --batch-folder my_batches/
  
  # Process with custom delay between batches (30 seconds instead of default 45)
  python wf_lead_scoring_personalized_talking_points.py --input leads.csv --output results.csv --delay 30
  
  # Process with no delay between batches (for faster processing)
  python wf_lead_scoring_personalized_talking_points.py --input leads.csv --output results.csv --delay 0
  
  # Continue processing even if some batches fail
  python wf_lead_scoring_personalized_talking_points.py --input leads.csv --output results.csv --continue-on-failure
  
  # Run batches in parallel with custom concurrency limit (8 concurrent batches)
  python wf_lead_scoring_personalized_talking_points.py --input leads.csv --output results.csv --batch-parallelism-limit 8
  
  # Run batches sequentially instead of in parallel
  python wf_lead_scoring_personalized_talking_points.py --input leads.csv --output results.csv --sequential
  
  # Combine existing batch files without running workflows
  python wf_lead_scoring_personalized_talking_points.py --output results.csv --combine-only

Batch Processing:
  The workflow processes leads in batches to manage resource usage and provide progress tracking.
  Batches can run either in parallel (default) or sequentially, with results stored in the batch folder.
  After all batches complete, results are combined into the final output CSV file.
  
  Default behavior: Process rows 0-200 in batches of 200 leads each in parallel (max 5 concurrent).
  Individual batch files are saved to batch_results/ folder and preserved for reference.
  
  Parallel Processing (Default):
  By default, batches run in parallel with a concurrency limit of 5 simultaneous batches.
  Use --batch-parallelism-limit to adjust concurrent batch count (e.g., --batch-parallelism-limit 8).
  Use --sequential to disable parallel processing and run batches one at a time.
  Inter-batch delays are ignored when running in parallel mode for maximum throughput.
  
  Sequential Processing:
  Use --sequential to run batches one after another instead of in parallel.
  A configurable delay is added between batches to prevent API rate limiting and reduce server load.
  Set --delay 0 to disable delays for faster sequential processing (use with caution).
  
  Failure Handling:
  By default, the job stops and throws an exception if any batch fails (--stop-on-failure).
  Use --continue-on-failure to process all batches even if some fail, then combine available results.
  When a job stops due to failure, partial statistics are displayed showing progress made.
  
  Combine-Only Mode:
  Use --combine-only to merge existing batch files without running any workflows.
  This is useful for combining results from previous runs or after manual intervention.
  Only requires --output argument; finds all batch_*.csv files in the batch folder.

Required CSV columns (supports multiple naming conventions):
  • LinkedIn URL: 'linkedinUrl', 'LinkedIn URL', 'LinkedIn'
  • Company: 'Company', 'Company Name', 'Organization' 
  • First Name: 'firstName', 'First Name', 'First'
  • Last Name: 'lastName', 'Last Name', 'Last'
  • Company Website: 'companyWebsite', 'Company website', 'Website', 'Company Website'
  • Email: 'emailId', 'Email ID', 'Email', 'Email Address'
  • Job Title: 'jobTitle', 'Job Title', 'Title', 'Position'

Example CSV formats supported:
  linkedinUrl,Company,First Name,Last Name,Company website,Email ID,Job Title
  LinkedIn URL,Company Name,firstName,lastName,Website,Email,Position
        """
    )

    # Get the directory where this script is located
    current_file_dir = Path(__file__).parent
    
    # Set default file paths relative to current script directory
    default_input_csv = str(current_file_dir / "leads.csv")
    default_output_csv = str(current_file_dir / "results.csv")
    default_batch_folder = str(current_file_dir / "batch_results")
    start_row = 0
    end_row = 200  # 250
    batch_size = 100
    default_delay_in_between_batches = 90  # 60
    default_stop_on_failure = True
    default_combine_batch_files_only_mode = False
    default_run_batches_in_parallel = True
    default_batch_parallelism_limit = 2

    kwargs = {
        'type': str,
        'help': 'Path to input CSV file containing lead data'
    }
    if default_input_csv is not None:
        kwargs['default'] = default_input_csv
        kwargs['help'] = f'Path to input CSV file containing lead data (default: {default_input_csv})'
    
    parser.add_argument(
        '--input', '--input-csv', 
        **kwargs
    )
    
    kwargs = {
        'type': str,
        'help': 'Path to output CSV file for processed results'
    }
    if default_output_csv is not None:
        kwargs['default'] = default_output_csv
        kwargs['help'] = f'Path to output CSV file for processed results (default: {default_output_csv})'
    
    parser.add_argument(
        '--output', '--output-csv',
        **kwargs
    )
    
    parser.add_argument(
        '--start-row',
        type=int,
        default=start_row,
        help='Starting row index for processing (0-based, excluding header). Default: 0'
    )
    
    kwargs = {
        'type': int,
        'help': 'Ending row index for processing (0-based, exclusive). If not specified, process to end of file'
    }
    if end_row is not None:
        kwargs['default'] = end_row
        kwargs['help'] = f'Ending row index for processing (0-based, exclusive). If not specified, process to end of file (default: {end_row})'
    
    parser.add_argument(
        '--end-row',
        **kwargs
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=batch_size,
        help=f'Number of leads to process in each batch. Default: {batch_size}'
    )
    
    parser.add_argument(
        '--batch-folder',
        type=str,
        default=default_batch_folder,
        help=f'Folder to store individual batch result files. Default: {default_batch_folder}'
    )
    
    parser.add_argument(
        '--delay',
        type=int,
        default=default_delay_in_between_batches,
        help=f'Delay in seconds between consecutive batch workflows. Default: {default_delay_in_between_batches} seconds'
    )
    
    parser.add_argument(
        '--stop-on-failure',
        action='store_true',
        default=default_stop_on_failure,
        help='Stop processing and throw exception if any batch fails. Default: True'
    )
    
    parser.add_argument(
        '--continue-on-failure',
        action='store_false',
        dest='stop_on_failure',
        help='Continue processing remaining batches even if some fail. Overrides --stop-on-failure'
    )
    
    parser.add_argument(
        '--combine-only',
        action='store_true',
        default=default_combine_batch_files_only_mode,
        help='Only combine existing batch files in batch folder without running workflows. Default: False'
    )
    
    parser.add_argument(
        '--run-batches-in-parallel',
        action='store_true',
        default=default_run_batches_in_parallel,
        help=f'Run batches in parallel instead of sequentially. Default: {default_run_batches_in_parallel}'
    )
    
    parser.add_argument(
        '--sequential',
        action='store_false',
        dest='run_batches_in_parallel',
        help='Run batches sequentially instead of in parallel. Overrides --run-batches-in-parallel'
    )
    
    parser.add_argument(
        '--batch-parallelism-limit',
        type=int,
        default=default_batch_parallelism_limit,
        help=f'Maximum number of batches to run concurrently when parallel processing is enabled. Default: {default_batch_parallelism_limit}'
    )
    
    args = parser.parse_args()
    
    # Convert input path to absolute path and validate
    input_path = Path(args.input).resolve()
    print(f"Input path: {input_path}")
    
    # Only validate file existence if it's not using the default path
    # (allow default path to not exist for backward compatibility)
    if args.input != default_input_csv and not input_path.exists():
        parser.error(f"Input CSV file does not exist: {args.input}")
    
    # Update args with resolved paths
    args.input = str(input_path)
    args.output = str(Path(args.output).resolve())
    
    if args.start_row < 0:
        parser.error("Start row must be >= 0")
        
    if args.end_row is not None and args.end_row <= args.start_row:
        parser.error("End row must be greater than start row")
        
    if args.batch_size <= 0:
        parser.error("Batch size must be greater than 0")
        
    if args.delay < 0:
        parser.error("Delay must be >= 0 seconds")
        
    if args.batch_parallelism_limit <= 0:
        parser.error("Batch parallelism limit must be greater than 0")
    
    # Warn if delay is specified with parallel processing (delays don't apply to parallel execution)
    if args.run_batches_in_parallel and args.delay > 0:
        print("⚠️  Warning: Inter-batch delay is ignored when running batches in parallel")
    
    return args

if __name__ == "__main__":
    print("="*80)
    print("Lead Scoring and Personalized Talking Points Generation Workflow")
    print("="*80)
    logging.basicConfig(level=logging.INFO)
    
    # Parse command line arguments
    args = parse_arguments()
    
    print(f"Configuration:")
    print(f"  Input CSV: {args.input if args.input else 'Using default test data'}")
    print(f"  Output CSV: {args.output if args.output else 'No output file'}")
    print(f"  Batch folder: {args.batch_folder}")
    print(f"  Row range: {args.start_row} to {args.end_row if args.end_row else 'end'}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Parallel processing: {args.run_batches_in_parallel}")
    if args.run_batches_in_parallel:
        print(f"  Max concurrent batches: {args.batch_parallelism_limit}")
        if args.delay > 0:
            print(f"  Inter-batch delay: {args.delay} seconds (ignored for parallel processing)")
    else:
        print(f"  Inter-batch delay: {args.delay} seconds")
    print(f"  Stop on failure: {args.stop_on_failure}")
    print(f"  Combine only: {args.combine_only}")
    print()
    
    # Handle combine-only mode
    if args.combine_only:
        print("🔄 COMBINE-ONLY MODE: Combining existing batch files...")
        combine_existing_batch_files(args.batch_folder, args.output)
        print("✅ Combine-only operation completed.")
        sys.exit(0)
    
    asyncio.run(main_batch_lead_scoring(
        input_csv=args.input,
        output_csv=args.output,
        batch_folder=args.batch_folder,
        start_row=args.start_row,
        end_row=args.end_row,
        batch_size=args.batch_size,
        delay=args.delay,
        stop_on_failure=args.stop_on_failure,
        run_batches_in_parallel=args.run_batches_in_parallel,
        batch_parallelism_limit=args.batch_parallelism_limit
    ))
