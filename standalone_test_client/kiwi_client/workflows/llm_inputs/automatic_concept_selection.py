from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union


class ConceptScore(BaseModel):
    """Score for a single concept with detailed evaluation criteria."""
    concept_id: str = Field(description="ID of the concept being scored")
    reasoning: str = Field(description="Brief explanation of the scoring rationale")
    relevance_score: int = Field(description="Score from 1-100 for relevance to user's expertise and audience")
    originality_score: int = Field(description="Score from 1-100 for uniqueness and originality") 
    impact_score: int = Field(description="Score from 1-100 for potential engagement impact")
    alignment_score: int = Field(description="Score from 1-100 for alignment with content strategy")
    total_score: int = Field(description="Sum of all scores, maximum 400")
    


class SelectionDecision(str, Enum):
    """Enum representing possible decisions after concept evaluation."""
    SELECT = "select"      # Select the highest scoring concept
    REGENERATE = "regenerate"  # All concepts below threshold, need new ones
    RESTART = "restart"    # Fundamental issues with the approach


class ConceptEvaluationSchema(BaseModel):
    """Schema for evaluating concepts with detailed scores and selection decision."""
    concept_scores: List[ConceptScore] = Field(description="Scores for each concept")
    selected_concept_id: Optional[str] = Field(None, description="ID of the highest scoring concept if any meets threshold")
    decision_reasoning: str = Field(description="Explanation for the selection decision")
    selection_decision: SelectionDecision = Field(description="Decision: select highest scored concept, regenerate if all below threshold (during regeneration, previous concepts are available in context and may be used to build upon or modify), or restart (discard all concepts generated so far and start afresh)")
    regeneration_feedback: Optional[str] = Field(None, description="Feedback for regeneration if applicable")

CONCEPT_EVALUATION_SCHEMA = ConceptEvaluationSchema.model_json_schema()

CONCEPT_EVALUATION_SYSTEM_PROMPT = """
You are an expert LinkedIn content strategist and evaluator.

You will be given:
1. A set of 3-5 content concepts (hook, message).
2. The user’s DNA document, describing their tone, audience, and content goals.
3. Three evaluation documents:
   - LinkedIn Post Evaluation Framework
   - LinkedIn Post Scoring Framework
   - LinkedIn Content Optimization Guide

Your task:
- Evaluate each concept individually using the scoring framework (clarity, resonance, uniqueness, alignment with user DNA, and optimization potential).
- Assign a score (0 to 100) for each concept across all criteria.
- Identify the **highest-scoring** concept.
- Output the results in the specified format.

```json\n{schema}\n```
"""

CONCEPT_EVALUATION_USER_PROMPT = """
Evaluate the following LinkedIn post concepts and make a selection decision based on the provided user context and methodology.

**Generated Concepts:**
{concepts}

**Content Strategy Methodology:**
- Post Evaluation Methodology: {post_evaluation_methodology}
- Post Scoring Methodology: {post_scoring_methodology}
- Content Optimization Methodology: {content_optimization_methodology}

**User Context:**
- User DNA: {user_dna}
- Initial Brief: {initial_brief}

**Evaluation Task:**
1. Score each concept on 4 criteria (1-100 scale):
   - Relevance to user's expertise and audience
   - Originality compared to recent posts
   - Potential engagement impact
   - Alignment with content strategy

2. Calculate a total score (max 40 points)

3. Make a decision:
   - If any concept scores 30+ points, select the highest-scoring concept
   - If all concepts score below 30 points, recommend regeneration with specific feedback
   - Only recommend restart if there are fundamental issues with the approach

Provide clear reasoning for your scores and selection decision.
"""
