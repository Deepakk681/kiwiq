"""
Output validation functions for B2B Blog Content Scoring workflow.
"""

import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    
    logger.info("✓ B2B Blog Content Scoring workflow validation passed.")
    
    return True


def display_scoring_results(final_outputs: Dict[str, Any]) -> None:
    """
    Display the B2B Blog Content Scoring results in a formatted way.
    
    Args:
        final_outputs: The final outputs from the workflow execution.
    """
    if not final_outputs:
        logger.warning("No final outputs to display.")
        return
    
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
