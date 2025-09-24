"""
B2B Blog Content Scoring Workflow

This workflow enables comprehensive B2B blog content analysis using the unified B2B Blog Content Scoring Framework:
- Loading of existing blog draft documents from provided namespace/docname
- Unified scoring for both traditional SEO and Answer Engine Optimization (AEO)
- Content Architecture & Structure evaluation (40 points)
- Content Depth & Authority assessment (40 points)
- Discovery Optimization analysis (15 points)
- Internal Architecture review (5 points)
- Total Search Visibility Score = (SEO Score × 0.5) + (AEO Score × 0.5)
- Structured output with quick wins, strategic recommendations, and detailed section breakdowns

Test Configuration:
- Uses provided document namespace, docname, and is_shared flag to load existing blog content
- Creates realistic B2B blog content for comprehensive framework testing
- Tests all four scoring sections with detailed criterion evaluation
- Includes proper validation and detailed results display
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import workflow testing utilities
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

# Import LLM inputs
from kiwi_client.workflows.active.content_studio.blog_aeo_seo_scoring.wf_llm_inputs import (
    B2B_BLOG_SCORING_SYSTEM_PROMPT,
    B2B_BLOG_SCORING_USER_PROMPT_TEMPLATE,
    B2B_BLOG_SCORING_OUTPUT_SCHEMA,
)

# Configuration constants
TEMPERATURE = 0.3  # Lower temperature for more consistent scoring
MAX_TOKENS = 10000

# LLM Provider Configuration
DEFAULT_LLM_PROVIDER = "openai"
DEFAULT_LLM_MODEL = "gpt-5"

# Workflow JSON structure
workflow_graph_schema = {
    "nodes": {
        # 1. Input Node
        "input_node": {
            "node_id": "input_node",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "namespace": {
                        "type": "str",
                        "required": True,
                        "description": "Namespace of the document to analyze for SEO"
                    },
                    "docname": {
                        "type": "str",
                        "required": True,
                        "description": "Document name of the blog content to analyze"
                    },
                    "is_shared": {
                        "type": "bool",
                        "required": True,
                        "description": "Whether the document is shared or private"
                    }
                }
            }
        },
        
        # 2. Transform Document Config for Loading
        "transform_document_config": {
            "node_id": "transform_document_config",
            "node_name": "transform_data",
            "node_config": {
                "base_object": {
                    "output_field_name": "blog_content"
                },
                "mappings": [
                    {"source_path": "namespace", "destination_path": "filename_config.static_namespace"},
                    {"source_path": "docname", "destination_path": "filename_config.static_docname"},
                    {"source_path": "is_shared", "destination_path": "is_shared"}
                ]
            }
        },
        
        # 3. Load Document Content
        "load_document": {
            "node_id": "load_document",
            "node_name": "load_customer_data",
            "node_config": {
                "load_configs_input_path": "transformed_data"
            }
        },
        
        # 4. Construct B2B Blog Scoring Prompt
        "construct_seo_analysis_prompt": {
            "node_id": "construct_seo_analysis_prompt",
            "node_name": "prompt_constructor",
            "node_config": {
                "prompt_templates": {
                    "seo_analysis_user_prompt": {
                        "id": "seo_analysis_user_prompt",
                        "template": B2B_BLOG_SCORING_USER_PROMPT_TEMPLATE,
                        "variables": {
                            "blog_content": None
                        },
                        "construct_options": {
                            "blog_content": "blog_content"
                        }
                    }
                }
            }
        },
        
        # 5. B2B Blog Content Scoring LLM
        "seo_analysis_llm": {
            "node_id": "seo_analysis_llm",
            "node_name": "llm",
            "node_config": {
                "llm_config": {
                    "model_spec": {
                        "provider": DEFAULT_LLM_PROVIDER,
                        "model": DEFAULT_LLM_MODEL
                    },
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS,
                    "reasoning_effort_class": "medium",
                },
                "default_system_prompt": B2B_BLOG_SCORING_SYSTEM_PROMPT,
                "output_schema": {
                    "schema_definition": B2B_BLOG_SCORING_OUTPUT_SCHEMA,
                    "convert_loaded_schema_to_pydantic": False,
                }
            }
        },
        
        # 6. Output Node
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "node_config": {}
        }
    },
    
    "edges": [
        # Input -> State: Store initial values
        {
            "src_node_id": "input_node",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "namespace", "dst_field": "namespace"},
                {"src_field": "docname", "dst_field": "docname"},
                {"src_field": "is_shared", "dst_field": "is_shared"}
            ]
        },
        
        # Input -> Transform Document Config
        {
            "src_node_id": "input_node",
            "dst_node_id": "transform_document_config",
            "mappings": [
                {"src_field": "namespace", "dst_field": "namespace"},
                {"src_field": "docname", "dst_field": "docname"},
                {"src_field": "is_shared", "dst_field": "is_shared"}
            ]
        },
        
        # Transform -> Load Document
        {
            "src_node_id": "transform_document_config",
            "dst_node_id": "load_document",
            "mappings": [
                {"src_field": "transformed_data", "dst_field": "transformed_data"}
            ]
        },
        
        # Load Document -> State (store loaded content)
        {
            "src_node_id": "load_document",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "blog_content", "dst_field": "blog_content"}
            ]
        },
        
        # Load Document -> Construct SEO Analysis Prompt
        {
            "src_node_id": "load_document",
            "dst_node_id": "construct_seo_analysis_prompt",
            "mappings": [
                {"src_field": "blog_content", "dst_field": "blog_content"}
            ]
        },
        
        # Construct Prompt -> SEO Analysis LLM
        {
            "src_node_id": "construct_seo_analysis_prompt",
            "dst_node_id": "seo_analysis_llm",
            "mappings": [
                {"src_field": "seo_analysis_user_prompt", "dst_field": "user_prompt"}
            ]
        },
        
        # SEO Analysis LLM -> State (store analysis results)
        {
            "src_node_id": "seo_analysis_llm",
            "dst_node_id": "$graph_state",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "seo_analysis_results"}
            ]
        },
        
        # SEO Analysis LLM -> Output Node
        {
            "src_node_id": "seo_analysis_llm",
            "dst_node_id": "output_node",
            "mappings": [
                {"src_field": "structured_output", "dst_field": "seo_analysis_results"}
            ]
        },
        
        # State -> Output Node (pass through document info)
        # {
        #     "src_node_id": "$graph_state",
        #     "dst_node_id": "output_node",
        #     "mappings": [
        #         {"src_field": "namespace", "dst_field": "analyzed_document_namespace"},
        #         {"src_field": "docname", "dst_field": "analyzed_document_docname"},
        #         {"src_field": "is_shared", "dst_field": "analyzed_document_is_shared"}
        #     ]
        # }
    ],
    
    "input_node_id": "input_node",
    "output_node_id": "output_node",
    
    "metadata": {
        "$graph_state": {
            "reducer": {
                # "blog_content": "replace",
                # "seo_analysis_results": "replace"
            }
        }
    }
}

# Validation function for B2B Blog Content Scoring workflow output
async def validate_seo_analysis_output(outputs: Optional[Dict[str, Any]]) -> bool:
    """
    Validate the B2B Blog Content Scoring workflow outputs.
    
    Args:
        outputs: The dictionary of final outputs from the workflow run.
        
    Returns:
        True if the outputs are valid, False otherwise.
    """
    assert outputs is not None, "Validation Failed: Workflow returned no outputs."
    logger.info("Validating B2B Blog Content Scoring workflow outputs...")
    
    # Check if scoring results are present
    scoring_results = outputs.get('seo_analysis_results')
    assert scoring_results is not None, "Validation Failed: No scoring results found."
    
    # Validate SEO score
    seo_score = scoring_results.get('seo_score')
    assert seo_score is not None, "Validation Failed: No SEO score found."
    assert isinstance(seo_score, int), "Validation Failed: SEO score should be an integer."
    assert 0 <= seo_score <= 100, "Validation Failed: SEO score should be between 0-100."
    logger.info(f"✓ SEO Score: {seo_score}/100")
    
    # Validate AEO score
    aeo_score = scoring_results.get('aeo_score')
    assert aeo_score is not None, "Validation Failed: No AEO score found."
    assert isinstance(aeo_score, int), "Validation Failed: AEO score should be an integer."
    assert 0 <= aeo_score <= 100, "Validation Failed: AEO score should be between 0-100."
    logger.info(f"✓ AEO Score: {aeo_score}/100")
    
    # Validate Total Search Visibility score
    total_score = scoring_results.get('total_search_visibility_score')
    assert total_score is not None, "Validation Failed: No total search visibility score found."
    assert isinstance(total_score, (int, float)), "Validation Failed: Total score should be a number."
    assert 0 <= total_score <= 100, "Validation Failed: Total score should be between 0-100."
    logger.info(f"✓ Total Search Visibility Score: {total_score}/100")
    
    # Validate grade
    grade = scoring_results.get('grade')
    assert grade is not None, "Validation Failed: No grade found."
    assert grade in ["A+", "A", "B", "C", "D", "F"], "Validation Failed: Invalid grade."
    logger.info(f"✓ Grade: {grade}")
    
    # Validate section scores
    section_scores = scoring_results.get('section_scores')
    assert section_scores is not None, "Validation Failed: No section scores found."
    
    # Check all four main sections exist
    required_sections = [
        'content_architecture_structure', 
        'content_depth_authority', 
        'discovery_optimization', 
        'internal_architecture'
    ]
    for section in required_sections:
        assert section in section_scores, f"Validation Failed: Missing section {section}"
        section_data = section_scores[section]
        assert 'seo_points' in section_data, f"Validation Failed: Missing seo_points in {section}"
        assert 'aeo_points' in section_data, f"Validation Failed: Missing aeo_points in {section}"
    
    logger.info("✓ All section scores present")
    
    # Validate key findings
    key_findings = scoring_results.get('key_findings')
    assert key_findings is not None, "Validation Failed: No key findings found."
    assert 'strengths' in key_findings, "Validation Failed: Missing strengths in key findings."
    assert 'gaps' in key_findings, "Validation Failed: Missing gaps in key findings."
    assert isinstance(key_findings['strengths'], list), "Validation Failed: Strengths should be a list."
    assert isinstance(key_findings['gaps'], list), "Validation Failed: Gaps should be a list."
    logger.info(f"✓ Key Findings: {len(key_findings['strengths'])} strengths, {len(key_findings['gaps'])} gaps")
    
    # Validate quick wins
    quick_wins = scoring_results.get('quick_wins')
    assert quick_wins is not None, "Validation Failed: No quick wins found."
    assert isinstance(quick_wins, list), "Validation Failed: Quick wins should be a list."
    assert len(quick_wins) >= 3, "Validation Failed: Should have at least 3 quick wins."
    logger.info(f"✓ Quick Wins: {len(quick_wins)} provided")
    
    # Validate strategic recommendations
    strategic_recs = scoring_results.get('strategic_recommendations')
    assert strategic_recs is not None, "Validation Failed: No strategic recommendations found."
    assert isinstance(strategic_recs, list), "Validation Failed: Strategic recommendations should be a list."
    assert len(strategic_recs) >= 2, "Validation Failed: Should have at least 2 strategic recommendations."
    logger.info(f"✓ Strategic Recommendations: {len(strategic_recs)} provided")
    
    # Validate document information in output
    analyzed_namespace = outputs.get('analyzed_document_namespace')
    analyzed_docname = outputs.get('analyzed_document_docname')
    assert analyzed_namespace is not None, "Validation Failed: Analyzed document namespace not found in output."
    assert analyzed_docname is not None, "Validation Failed: Analyzed document docname not found in output."
    logger.info(f"✓ Analyzed Document: {analyzed_namespace}/{analyzed_docname}")
    
    logger.info("✓ B2B Blog Content Scoring workflow validation passed.")
    
    return True

# Test function
async def main_test_seo_analysis():
    """
    Test the B2B Blog Content Scoring Workflow.
    """
    test_name = "B2B Blog Content Scoring Workflow Test"
    print(f"\n--- Starting {test_name} ---")
    
    # Test scenarios
    test_scenario = {
        "name": "B2B Blog Content Analysis",
        "initial_inputs": {
            "namespace": "test_blog_posts_b2b_scoring",
            "docname": "sample_ai_healthcare_blog_post",
            "is_shared": False
        }
    }
    
    # Setup test document with realistic blog content
    setup_docs: List[SetupDocInfo] = [
        {
            'namespace': "test_blog_posts_b2b_scoring",
            'docname': "sample_ai_healthcare_blog_post",
            'initial_data': {
                "title": "The Future of AI in Healthcare: Transforming Patient Care in 2024",
                "content": """
# The Future of AI in Healthcare: Transforming Patient Care in 2024

Artificial intelligence (AI) is revolutionizing healthcare at an unprecedented pace. As we progress through 2024, the integration of AI technologies in medical practice has moved from experimental to essential, fundamentally changing how we diagnose, treat, and care for patients.

## What is AI in Healthcare?

AI in healthcare refers to the use of machine learning algorithms and software to emulate human cognition in analyzing, interpreting, and understanding complex medical data. This technology encompasses everything from diagnostic imaging to drug discovery and personalized treatment plans.

## Key Applications of AI in Modern Healthcare

### 1. Diagnostic Imaging and Radiology

AI-powered imaging systems have achieved remarkable accuracy rates, often surpassing human radiologists in detecting certain conditions:

- **Medical Imaging Analysis**: AI can identify cancerous tumors, fractures, and other abnormalities with 95%+ accuracy
- **Early Disease Detection**: Machine learning algorithms can spot early signs of diseases like Alzheimer's and Parkinson's
- **Workflow Optimization**: Automated image analysis reduces diagnostic time by up to 50%

### 2. Personalized Treatment Plans

Modern AI systems analyze patient data to create customized treatment protocols:

- **Genetic Analysis**: AI processes genomic data to predict treatment responses
- **Drug Interaction Monitoring**: Algorithms identify potential medication conflicts
- **Treatment Outcome Prediction**: Machine learning models forecast patient recovery timelines

### 3. Clinical Decision Support Systems

AI assists healthcare professionals in making informed decisions:

- **Real-time Risk Assessment**: Continuous monitoring of patient vital signs
- **Evidence-based Recommendations**: AI reviews latest medical literature for treatment options
- **Preventive Care Alerts**: Early warning systems for potential health complications

## Benefits of AI in Healthcare

The integration of AI technologies brings numerous advantages to healthcare delivery:

**Improved Accuracy**: AI systems can process vast amounts of data without fatigue, leading to more accurate diagnoses and treatment recommendations.

**Enhanced Efficiency**: Automated processes reduce administrative burden and allow healthcare professionals to focus on patient care.

**Cost Reduction**: AI optimization can reduce healthcare costs by up to 30% through improved resource allocation and reduced errors.

**Accessibility**: AI-powered telemedicine and diagnostic tools make healthcare more accessible to underserved populations.

## Challenges and Considerations

Despite its promise, AI in healthcare faces several challenges:

### Data Privacy and Security
- Patient data protection remains paramount
- HIPAA compliance requirements for AI systems
- Cybersecurity concerns with connected medical devices

### Regulatory Compliance
- FDA approval processes for AI medical devices
- International regulatory harmonization efforts
- Liability and malpractice considerations

### Integration Complexity
- Legacy system compatibility issues
- Staff training and adaptation requirements
- Change management in healthcare organizations

## The Road Ahead: AI Healthcare Trends for 2024 and Beyond

Looking forward, several trends will shape the future of AI in healthcare:

1. **Predictive Analytics**: Advanced algorithms will predict health outcomes before symptoms appear
2. **Voice-Activated AI**: Natural language processing will enable hands-free medical documentation
3. **Robotic Surgery**: AI-assisted surgical procedures will become more precise and minimally invasive
4. **Mental Health AI**: Therapeutic chatbots and mood analysis tools will support mental health care
5. **Drug Discovery Acceleration**: AI will reduce pharmaceutical development timelines from decades to years

## Conclusion

The future of AI in healthcare is not just promising – it's already here. As we continue through 2024, healthcare organizations that embrace AI technologies will be better positioned to deliver superior patient outcomes, reduce costs, and advance medical science.

For healthcare professionals, patients, and policymakers, understanding and adapting to these AI-driven changes is crucial for participating in the healthcare transformation that's reshaping our world.

---

*This article was written to provide insights into the current state and future potential of AI in healthcare. For specific medical advice, always consult with qualified healthcare professionals.*
                """,
                "meta_description": "Discover how AI is transforming healthcare in 2024. Learn about diagnostic imaging, personalized treatment, and the future of patient care with artificial intelligence.",
                "author": "Dr. Sarah Johnson",
                "publication_date": "2024-03-15",
                "tags": ["AI", "Healthcare", "Medical Technology", "Digital Health", "Innovation"],
                "word_count": 750
            },
            'is_shared': False,
            'is_versioned': False,
            'initial_version': "None",
            'is_system_entity': False
        }
    ]
    
    cleanup_docs: List[CleanupDocInfo] = [
        {
            'namespace': "test_blog_posts_b2b_scoring",
            'docname': "sample_ai_healthcare_blog_post",
            'is_shared': False,
            'is_versioned': False,
            'is_system_entity': False
        }
    ]
    
    print(f"\n--- Running Scenario: {test_scenario['name']} ---")
    
    try:
        final_status, final_outputs = await run_workflow_test(
            test_name=f"{test_name} - {test_scenario['name']}",
            workflow_graph_schema=workflow_graph_schema,
            initial_inputs=test_scenario['initial_inputs'],
            expected_final_status=WorkflowRunStatus.COMPLETED,
            hitl_inputs=[],  # No HITL inputs needed for this workflow
            setup_docs=setup_docs,
            cleanup_docs=cleanup_docs,
            cleanup_docs_created_by_setup=True,
            validate_output_func=validate_seo_analysis_output,
            stream_intermediate_results=True,
            poll_interval_sec=2,
            timeout_sec=300  # 5 minutes should be sufficient for B2B content scoring
        )
        
        # Display results
        if final_outputs:
            print(f"\nB2B Blog Content Scoring Results:")
            scoring_results = final_outputs.get('seo_analysis_results', {})
            
            # Main scores
            seo_score = scoring_results.get('seo_score', 'N/A')
            aeo_score = scoring_results.get('aeo_score', 'N/A')
            total_score = scoring_results.get('total_search_visibility_score', 'N/A')
            grade = scoring_results.get('grade', 'N/A')
            
            print(f"SEO Score: {seo_score}/100")
            print(f"AEO Score: {aeo_score}/100")
            print(f"Total Search Visibility Score: {total_score}/100")
            print(f"Grade: {grade}")
            
            # Section breakdown
            section_scores = scoring_results.get('section_scores', {})
            if section_scores:
                print(f"\nSection Breakdown:")
                arch_struct = section_scores.get('content_architecture_structure', {})
                print(f"  Content Architecture & Structure: SEO {arch_struct.get('seo_points', 0):.1f}/24, AEO {arch_struct.get('aeo_points', 0):.1f}/37")
                
                depth_auth = section_scores.get('content_depth_authority', {})
                print(f"  Content Depth & Authority: SEO {depth_auth.get('seo_points', 0):.1f}/28, AEO {depth_auth.get('aeo_points', 0):.1f}/35")
                
                discovery = section_scores.get('discovery_optimization', {})
                print(f"  Discovery Optimization: SEO {discovery.get('seo_points', 0):.1f}/12, AEO {discovery.get('aeo_points', 0):.1f}/10")
                
                internal = section_scores.get('internal_architecture', {})
                print(f"  Internal Architecture: SEO {internal.get('seo_points', 0):.1f}/3, AEO {internal.get('aeo_points', 0):.1f}/2")
            
            # Quick wins
            quick_wins = scoring_results.get('quick_wins', [])
            if quick_wins:
                print(f"\nTop Quick Wins ({len(quick_wins)}):")
                for i, win in enumerate(quick_wins[:5], 1):  # Show first 5 quick wins
                    effort = win.get('effort_level', 'Unknown')
                    impact = win.get('points_impact', 'N/A')
                    time_est = win.get('time_estimate', 'Unknown')
                    print(f"{i}. [{effort} effort, +{impact} pts, {time_est}] {win.get('improvement', 'N/A')}")
            
            # Key findings
            key_findings = scoring_results.get('key_findings', {})
            strengths = key_findings.get('strengths', [])
            gaps = key_findings.get('gaps', [])
            
            if strengths:
                print(f"\nTop Strengths: {'; '.join(strengths[:3])}")  # Show first 3
            if gaps:
                print(f"Key Gaps: {'; '.join(gaps[:3])}")  # Show first 3
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    
    print(f"\n--- {test_name} Completed Successfully ---")


# Entry point
if __name__ == "__main__":
    print("="*60)
    print("B2B Blog Content Scoring Workflow Test")
    print("="*60)
    
    try:
        asyncio.run(main_test_seo_analysis())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.exception("Test execution failed")
    
    print("\nTest execution finished.")
    print("Run from project root: PYTHONPATH=$(pwd):$(pwd)/services poetry run python standalone_test_client/kiwi_client/workflows/active/content_studio/blog_aeo_seo_scoring/wf_blog_aeo_seo_scoring_json.py")
