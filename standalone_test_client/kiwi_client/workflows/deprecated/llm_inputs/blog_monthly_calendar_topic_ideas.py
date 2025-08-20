from typing import List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import date


class ContentObjective(str, Enum):
    """Primary objectives for blog content."""
    BRAND_AWARENESS = "brand_awareness"
    THOUGHT_LEADERSHIP = "thought_leadership"
    ENGAGEMENT = "engagement"
    EDUCATION = "education"
    LEAD_GENERATION = "lead_generation"
    COMMUNITY_BUILDING = "community_building"


BLOG_MONTHLY_USER_PROMPT_TEMPLATE = """Generate a monthly blog topic calendar.

Rules:
- Do NOT fabricate facts or statistics. Base suggestions on the provided documents and company expertise.
- Use the exact play names and concepts from the provided `playbook` when aligning themes.
- Generate diverse, non-repetitive topic ideas aligned to the company's audience and strategy.
- Use `recent_posts_context` to infer style, tone, and historical themes.
- Prioritize themes and topics informed by the diagnostics report opportunities and gaps.

Scheduling requirements:
- Plan slots only for the given month: start_date: {month_start}
- Schedule exactly `total_slots_needed` slots for this calendar month.
- Select specific calendar dates within the month that fall on preferred posting days if provided in `schedule_config.posting_days` (fallback: Mon/Thu).
- Each slot's date must be unique and cannot be in the past relative to {current_datetime}.

Output requirements per slot:
- Generate exactly 4 topic ideas for each scheduled date.
- All 4 topics in a slot must be unified around one common theme from the playbook.
- The theme must align to a specific play from the playbook (`play_aligned`).
- Each topic must include a title and a short description.
- Provide a clear objective for the slot and a brief "why this matters" rationale.

Context:
- Company Profile: {company_doc}
- Content Playbook: {playbook}
- Diagnostics Report: {diagnostic_report}
- Recent Posts (optional): {recent_posts_context}
- Schedule Config (optional): {schedule_config}
- Month Start: {month_start}
- Total Slots Needed: {total_slots_needed}
- Current Datetime: {current_datetime}

Respond ONLY with the JSON object matching the specified schema.
"""

BLOG_MONTHLY_SYSTEM_PROMPT_TEMPLATE = """You are a senior content strategist creating a monthly blog content calendar.

You must:
- Align each slot to a play from the provided playbook
- Select a cohesive theme per slot and generate exactly 4 topic ideas per slot
- Ensure novelty across slots (do not repeat themes or dates)
- Schedule within the specified calendar month, on preferred posting days when provided
- Use diagnostics to prioritize opportunities and fill content gaps

Validation before responding:
1) Total slots equal `total_slots_needed`
2) All slot dates are within the target month and unique
3) Each slot has 4 topics under a single coherent theme
4) Every slot references a concrete `play_aligned` from the playbook

Respond strictly with the JSON output conforming to the schema: ```json\n{schema}\n```"""

BLOG_MONTHLY_ADDITIONAL_USER_PROMPT_TEMPLATE = """Generate one additional blog topic slot for the month.

Requirements:
- Exactly 4 topic ideas, unified by a single theme
- Theme must align with a play from the playbook
- Select a new date within the target month not used previously
- Prefer a different theme/play than prior slots unless strongly justified by diagnostics
- Keep consistency with style and strategy
"""


class BlogTopic(BaseModel):
    title: str = Field(..., description="Suggested blog post title")
    description: str = Field(..., description="Short description of the blog post idea")


class BlogMonthlySlot(BaseModel):
    suggested_topics: List[BlogTopic] = Field(..., description="Exactly 4 topic suggestions for the slot")
    scheduled_date: date = Field(..., description="Scheduled calendar date (YYYY-MM-DD)")
    theme: str = Field(..., description="Cohesive theme for this slot (from playbook themes)")
    play_aligned: str = Field(..., description="Name of the play from playbook this slot aligns to")
    objective: ContentObjective = Field(..., description="Primary objective for this slot")
    why_important: str = Field(..., description="Why this slot matters to the audience")


# We generate one slot per LLM call in the loop; the collector will accumulate slots
BLOG_MONTHLY_OUTPUT_SCHEMA = BlogMonthlySlot.model_json_schema() 