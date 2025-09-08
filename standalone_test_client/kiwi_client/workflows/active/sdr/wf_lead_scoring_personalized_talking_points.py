"""
Lead Scoring and Personalized Talking Points Generation Workflow

This workflow demonstrates:
1. Taking a list of lead items with LinkedIn URL, Company, First Name, Last Name, Company website, Email ID, Job Title
2. Step 1: Parallel company qualification assessment using Perplexity LLM with structured output
3. Filtering qualified leads based on qualification_check_passed = True
4. Steps 2-4: Sequential LLM processing for each qualified lead:
   - Step 2: ContentQ scoring + content gap analysis
   - Step 3: Strategic content opportunity identification  
   - Step 4: Personalized talking points + pitch generation
5. Using private mode passthrough data to preserve context across all steps
6. Collecting final results with comprehensive lead insights and talking points

Input: List of lead items with required fields
Output: Qualified leads with ContentQ scores, content opportunities, and personalized talking points
"""

import json
import asyncio
import csv
import argparse
import sys
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any, Literal
import logging

# --- Workflow Constants ---
LLM_PROVIDER_RESEARCH = "perplexity"  # Using Perplexity for research capabilities
LLM_MODEL_RESEARCH = "sonar-pro"  # Perplexity model with online search
LLM_TEMPERATURE_RESEARCH = 0.5
LLM_MAX_TOKENS_RESEARCH = 2000

LLM_PROVIDER_WRITER = "anthropic"
LLM_MODEL_WRITER = "claude-sonnet-4-20250514"
LLM_TEMPERATURE_WRITER = 0.5
LLM_MAX_TOKENS_WRITER = 4000

# --- System Prompts for Each Step ---

STEP1_SYSTEM_PROMPT = """You are a B2B lead qualification expert specializing in fast company assessment. Your goal is to quickly determine if a company is a good fit for B2B content marketing services.

You have access to real-time web search to gather current information about companies. Use this capability to research the company thoroughly but efficiently.

Focus on gathering the essential qualification data points and making a clear pass/fail decision based on the criteria provided."""

STEP2_SYSTEM_PROMPT = """You are applying ContentQ's proven lead scoring methodology. You are an expert at evaluating B2B companies for content marketing opportunities and calculating precise scores based on multiple business factors.

Use your knowledge of B2B SaaS, funding stages, content marketing, and competitive landscapes to provide accurate assessments."""

STEP3_SYSTEM_PROMPT = """You are a senior content strategist at ContentQ with deep expertise in B2B technical content marketing. Your specialty is identifying unique content opportunities that drive measurable business outcomes.

Focus on strategic, high-impact content opportunities that leverage the company's unique position and the individual's expertise to create competitive advantages."""

STEP4_SYSTEM_PROMPT = """You are a senior sales development expert at ContentQ, skilled at creating personalized, research-backed talking points that demonstrate deep understanding of prospects' businesses.

Your talking points should be specific, insightful, and create urgency while positioning ContentQ as the expert solution for their content marketing needs."""

# --- Private mode passthrough data keys for preserving context across steps ---
# Step 1 outputs that need to be preserved through all subsequent steps
step1_passthrough_keys = ["linkedinUrl", "Company", "firstName", "lastName", "companyWebsite", "emailId", "jobTitle", "qualification_result", "qualification_result_citations"]

# Step 2 outputs that need to be preserved through steps 3-4  
step2_passthrough_keys = ["linkedinUrl", "Company", "firstName", "lastName", "companyWebsite", "emailId", "jobTitle", "qualification_result", "qualification_result_citations", "contentq_and_content_analysis", "contentq_and_content_analysis_citations"]

# Step 3 outputs that need to be preserved through step 4
step3_passthrough_keys = ["linkedinUrl", "Company", "firstName", "lastName", "companyWebsite", "emailId", "jobTitle", "qualification_result", "qualification_result_citations", "contentq_and_content_analysis", "contentq_and_content_analysis_citations", "strategic_analysis", "strategic_analysis_citations"]

# --- Workflow Graph Definition ---
workflow_graph_schema = {
    "nodes": {
        # --- 1. Input Node ---
        "input_node": {
            "node_id": "input_node",
            "node_name": "input_node",
            "node_config": {},
            "dynamic_output_schema": {
                "fields": {
                    "leads_to_process": {
                        "type": "list",
                        "required": False,
                        "default": [
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
                        ],
                        "description": "List of leads with LinkedIn URL, Company, First Name, Last Name, Company website, Email ID, Job Title"
                    }
                }
            }
        },

        # --- 2. Map List Router Node - Routes each lead to Step 1 qualification ---
        "route_leads_to_qualification": {
            "node_id": "route_leads_to_qualification",
            "node_name": "map_list_router_node",
            "node_config": {
                "choices": ["step1_qualification_prompt"],
                "map_targets": [
                    {
                        "source_path": "leads_to_process",
                        "destinations": ["step1_qualification_prompt"],
                        "batch_size": 1
                    }
                ]
            }
        },

        # --- 3. Step 1: Prompt Constructor for Qualification Assessment ---
        "step1_qualification_prompt": {
            "node_id": "step1_qualification_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step1_passthrough_keys,
            "node_config": {
                "prompt_templates": {
                    "qualification_system_prompt": {
                        "id": "qualification_system_prompt",
                        "template": STEP1_SYSTEM_PROMPT,
                        "variables": {},
                        "construct_options": {}
                    },
                    "qualification_user_prompt": {
                        "id": "qualification_user_prompt", 
                        "template": """Goal: Fast company fit assessment + foundation data

Research Actions:
1. Company website scan: Industry, employee signals, content presence
2. Single Crunchbase lookup: Funding stage, size, recent news
3. Quick LinkedIn validation: Confirm individual role/title
4. Basic fit check: B2B, technical product, 10-500 employees

Simple Qualification Criteria:
PASS if:
✓ B2B company (not pure consumer)
✓ 10-500 employee range
✓ Individual has marketing/growth/revenue/founder role

FAIL = Stop research, mark as unqualified

INPUT DATA:
Company: {Company}
Individual: {firstName} {lastName}, {jobTitle}
LinkedIn: {linkedinUrl}
Website: {companyWebsite}
Email: {emailId}

Please research this company and individual thoroughly using web search, then provide your assessment.""",
                        "variables": {
                            "Company": None,
                            "firstName": None,
                            "lastName": None,
                            "jobTitle": None,
                            "linkedinUrl": None,
                            "companyWebsite": None,
                            "emailId": None
                        },
                        "construct_options": {
                            "Company": "Company",
                            "firstName": "firstName",
                            "lastName": "lastName", 
                            "jobTitle": "jobTitle",
                            "linkedinUrl": "linkedinUrl",
                            "companyWebsite": "companyWebsite",
                            "emailId": "emailId"
                        }
                    }
                }
            }
        },

        # --- 4. Step 1: Company Qualification Assessment ---
        "step1_qualification_assessment": {
            "node_id": "step1_qualification_assessment",
            "node_name": "llm",
            "private_input_mode": True,
            # "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step1_passthrough_keys,
            "private_output_to_central_state_node_output_key": "qualification_result",
            "write_to_private_output_passthrough_data_from_output_mappings": {
                "web_search_result": "qualification_result_citations"
            },
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER_RESEARCH, "model": LLM_MODEL_RESEARCH},
                    "temperature": LLM_TEMPERATURE_RESEARCH,
                    "max_tokens": LLM_MAX_TOKENS_RESEARCH
                },
                "output_schema": {
                    "dynamic_schema_spec": {
                        "schema_name": "QualificationResult",
                        "fields": {
                            "company_info": {
                                "type": "str", 
                                "required": True,
                                "description": "Comprehensive company research summary including industry, size, funding, business model"
                            },
                            "individual_info": {
                                "type": "str",
                                "required": True, 
                                "description": "Individual role validation and background information"
                            },
                            "industry": {
                                "type": "str",
                                "required": True,
                                "description": "Primary industry/category of the company"
                            },
                            "employee_count_estimate": {
                                "type": "str", 
                                "required": True,
                                "description": "Estimated employee count range"
                            },
                            "funding_stage": {
                                "type": "str",
                                "required": True,
                                "description": "Current funding stage (Pre-seed, Seed, Series A, etc.)"
                            },
                            "qualification_reasoning": {
                                "type": "str",
                                "required": True,
                                "description": "Detailed explanation of why the lead passed or failed qualification"
                            },
                            "qualification_check_passed": {
                                "type": "bool",
                                "required": True,
                                "description": "True if company passes qualification criteria, False otherwise"
                            },                            
                        }
                    }
                }
            }
        },

        # --- 5. Filter Node - Keep only qualified leads ---
        "filter_qualified_leads": {
            "node_id": "filter_qualified_leads", 
            "node_name": "filter_data",
            "enable_node_fan_in": True,
            "node_config": {
                "targets": [
                    {
                        "filter_target": "qualification_results",
                        "filter_mode": "allow",
                        "condition_groups": [
                            {
                                "conditions": [
                                    {
                                        "field": "qualification_results.qualification_result.qualification_check_passed",
                                        "operator": "equals",
                                        "value": True
                                    }
                                ],
                                "logical_operator": "and"
                            }
                        ],
                        "group_logical_operator": "and"
                    }
                ],
                "non_target_fields_mode": "allow"
            }
        },

        # --- 6. Map List Router Node - Route qualified leads to Step 2 ---
        "route_qualified_to_step2": {
            "node_id": "route_qualified_to_step2",
            "node_name": "map_list_router_node", 
            "node_config": {
                "choices": ["step2_contentq_prompt"],
                "map_targets": [
                    {
                        "source_path": "filtered_data.qualification_results",
                        "destinations": ["step2_contentq_prompt"],
                        "batch_size": 1
                    }
                ]
            }
        },

        # --- 7. Step 2: Prompt Constructor for ContentQ Scoring ---
        "step2_contentq_prompt": {
            "node_id": "step2_contentq_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,  # Don't write to central state, pass to next step
            "private_output_passthrough_data_to_central_state_keys": step2_passthrough_keys,
            "node_config": {
                "prompt_templates": {
                    "contentq_system_prompt": {
                        "id": "contentq_system_prompt",
                        "template": STEP2_SYSTEM_PROMPT,
                        "variables": {},
                        "construct_options": {}
                    },
                    "contentq_user_prompt": {
                        "id": "contentq_user_prompt",
                        "template": """You are applying ContentQ's proven lead scoring methodology. Provide a comprehensive analysis in structured markdown format.

## ContentQ Lead Scoring Analysis

### Company Overview
**Company:** {company_name}  
**Individual:** {first_name} {last_name}, {title}  
**Website:** {website_url}

### Scoring Methodology

**COMPANY SCORING:**
- Funding Stage: Seed/Series A (+25), Pre-seed (+15), Series B+ (-10)
- Employee Count: 10-50 (+20), 5-10 (+10), 50-100 (+5)  
- Industry: Dev tools/API/Prosumer (+20), B2B SaaS (+15), B2C (disqualify)
- Founded: 1-3 years (+15), 6mo-1yr (+10), 4+ years (+5)

**CONTENT GAP SCORING:**
- No blog/broken blog (+30), Last post >60 days (+25), 1-3 posts/month (+20), 4+ generic posts (+10), Strong content (-20)
- AI Invisibility: Not in ChatGPT responses (+20), Competitors mentioned instead (+15)

**INDIVIDUAL SCORING:**
- Founder/CEO (+30), VP Marketing (+25), Fractional CMO (+25), Marketing Manager (+15), Content Manager (+5)
- LinkedIn: Recent posts (+10), <500 followers (+5), New role (+10)

**URGENCY FACTORS:**
- Recent funding <6mo (+20), Product launch (+15), New marketing hire (+15)

**OVERRIDE RULES:**
- "No Blog Rule": B2B company + 10+ employees + no blog = automatic 80+ score
- "Category Creator": No direct competitors = +20

### Analysis Structure Required:

#### 1. Company Assessment
- **Funding Stage Analysis:** [Current stage with reasoning and sources]
- **Employee Count Analysis:** [Size assessment with sources]
- **Industry Classification:** [Category with justification]
- **Company Age Analysis:** [Founded date and implications]
- **Score Calculation:** [Points awarded with reasoning]

#### 2. Content Gap Analysis
- **Current Content Audit:** [Blog status, posting frequency, content quality with specific examples]
- **AI Visibility Check:** [Search results in ChatGPT/AI responses with citations]
- **Content Gap Identification:** [Specific opportunities with reasoning]
- **Score Calculation:** [Points awarded with justification]

#### 3. Individual Assessment
- **Role Analysis:** [Title evaluation and authority level]
- **LinkedIn Presence:** [Follower count, recent activity, engagement with sources]
- **Authority Potential:** [Ability to create thought leadership content]
- **Score Calculation:** [Points awarded with reasoning]

#### 4. Urgency Factors
- **Recent Developments:** [Funding, launches, hires with dates and sources]
- **Market Timing:** [Why now is important with context]
- **Score Calculation:** [Additional points with justification]

#### 5. Final ContentQ Score
**TOTAL SCORE: [X]/100 - [TIER CLASSIFICATION]**
- 🔥 ON FIRE (80-100): Immediate priority
- 🌟 HOT LEAD (60-79): High priority  
- ⚡ WARM LEAD (40-59): Medium priority
- ❄️ COLD LEAD (0-39): Low priority

#### 6. Competitive Intelligence
- **Primary Competitors:** [Top 1-2 competitors with analysis]
- **Their Content Approach:** [What they're doing well/poorly]
- **Competitive Advantage Opportunity:** [How to differentiate]

#### 7. Strategic Recommendation
- **Biggest Content Opportunity:** [Most impactful area to focus]
- **Reasoning:** [Why this will drive business results]
- **Supporting Evidence:** [Data points and citations]

**Research Context:**
{company_research}

**Research Citations and Sources:**
{research_citations}

Please provide detailed analysis with specific citations and reasoning for each section. Use actual data points and sources where available. Reference the citations provided above when making claims.""",
                        "variables": {
                            "company_name": None,
                            "first_name": None,
                            "last_name": None,
                            "title": None,
                            "website_url": None,
                            "company_research": None,
                            "research_citations": None
                        },
                        "construct_options": {
                            "company_name": "Company",
                            "first_name": "firstName",
                            "last_name": "lastName",
                            "title": "jobTitle",
                            "website_url": "companyWebsite", 
                            "company_research": "qualification_result",
                            "research_citations": "qualification_result_citations"
                        }
                    }
                }
            }
        },

        # --- 8. Step 2: ContentQ Scoring + Content Gap Analysis ---
        "step2_contentq_scoring": {
            "node_id": "step2_contentq_scoring",
            "node_name": "llm",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,  # Don't write to central state, pass to next step
            "private_output_passthrough_data_to_central_state_keys": step2_passthrough_keys,
            "write_to_private_output_passthrough_data_from_output_mappings": {
                "text_content": "contentq_and_content_analysis",
                "web_search_result": "contentq_and_content_analysis_citations"
            },
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER_RESEARCH, "model": LLM_MODEL_RESEARCH},
                    "temperature": LLM_TEMPERATURE_RESEARCH,
                    "max_tokens": LLM_MAX_TOKENS_RESEARCH
                }
            }
        },

        # --- 9. Step 3: Prompt Constructor for Strategic Content Opportunity ---
        "step3_strategic_prompt": {
            "node_id": "step3_strategic_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step3_passthrough_keys,
            "node_config": {
                "prompt_templates": {
                    "strategic_system_prompt": {
                        "id": "strategic_system_prompt",
                        "template": STEP3_SYSTEM_PROMPT,
                        "variables": {},
                        "construct_options": {}
                    },
                    "strategic_user_prompt": {
                        "id": "strategic_user_prompt",
                        "template": """You are a senior content strategist at ContentQ. Provide a comprehensive strategic analysis in structured markdown format.

## Strategic Content Opportunity Analysis

### Company Profile
**Company:** {company_name}  
**Individual:** {first_name} {last_name}, {title}  
**Website:** {website_url}

### Context Integration

**Previous Analysis Summary:**
- **Qualification Results:** {qualification_analysis}
- **Qualification Citations:** {qualification_citations}
- **ContentQ Scoring & Content Analysis:** {contentq_analysis}
- **ContentQ Analysis Citations:** {contentq_citations}

### Strategic Framework

ContentQ helps B2B technical companies generate pipeline through thought leadership content. We focus on content that creates measurable business outcomes: lead generation, competitive differentiation, market authority.

### Analysis Structure Required:

#### 1. Strategic Content Positioning
- **Unique Content Angle:** [What content territory could this company own? With reasoning and market evidence]
- **Authority Building Opportunity:** [How the individual can become an industry thought leader]
- **Competitive Differentiation:** [Content angles competitors aren't covering with citations]
- **Market Timing Analysis:** [Why now is the right time with supporting data]

#### 2. Business Context Analysis  
- **Funding Stage Impact:** [How their current funding creates content urgency with timeline reasoning]
- **Company Size Advantage:** [How their scale creates content opportunities with examples]
- **Industry Positioning:** [Category-specific content opportunities with market analysis]
- **Growth Stage Implications:** [Content needs based on business maturity with citations]

#### 3. Individual Authority Assessment
- **Current Authority Level:** [Assessment of individual's existing thought leadership with sources]
- **Authority Building Potential:** [Specific areas where they could establish expertise]
- **Content Creation Capacity:** [Realistic assessment of their ability to produce content]
- **Network Leverage:** [How to use their existing network for content amplification]

#### 4. Content Strategy Framework
- **Primary Content Pillar:** [Main topic area with business rationale and evidence]
- **Secondary Content Pillars:** [2-3 supporting topics with strategic reasoning]
- **Content Format Recommendations:** [Best formats for their audience with justification]
- **Distribution Strategy:** [Optimal channels based on their market with data]

#### 5. Business Impact Projection
- **90-Day Outcomes:** [Expected results from content investment with benchmarks]
- **Lead Generation Potential:** [Specific pipeline impact with industry comparisons]
- **Brand Authority Building:** [How content will establish market position]
- **Competitive Advantage Creation:** [Sustainable differentiation through content]

#### 6. Implementation Roadmap
- **Phase 1 (Month 1):** [Immediate content opportunities with rationale]
- **Phase 2 (Month 2-3):** [Scaling content production with supporting evidence]
- **Success Metrics:** [KPIs to track content effectiveness with benchmarks]
- **Resource Requirements:** [Team, tools, budget considerations with justification]

#### 7. Risk Assessment & Mitigation
- **Content Creation Challenges:** [Potential obstacles with solutions]
- **Market Timing Risks:** [What could change the opportunity with contingencies]
- **Competitive Response:** [How competitors might react with counter-strategies]

Please provide detailed strategic analysis with specific reasoning, citations, and actionable recommendations for each section. Focus on measurable business outcomes and competitive advantages.""",
                        "variables": {
                            "company_name": None,
                            "first_name": None,
                            "last_name": None,
                            "title": None,
                            "website_url": None,
                            "qualification_analysis": None,
                            "qualification_citations": None,
                            "contentq_analysis": None,
                            "contentq_citations": None
                        },
                        "construct_options": {
                            "company_name": "Company",
                            "first_name": "firstName",
                            "last_name": "lastName",
                            "title": "jobTitle",
                            "website_url": "companyWebsite",
                            "qualification_analysis": "qualification_result",
                            "qualification_citations": "qualification_result_citations",
                            "contentq_analysis": "contentq_and_content_analysis",
                            "contentq_citations": "contentq_and_content_analysis_citations"
                        }
                    }
                }
            }
        },

        # --- 10. Step 3: Strategic Content Opportunity Identification ---
        "step3_strategic_opportunity": {
            "node_id": "step3_strategic_opportunity",
            "node_name": "llm",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step3_passthrough_keys,
            "write_to_private_output_passthrough_data_from_output_mappings": {
                "text_content": "strategic_analysis",
                "web_search_result": "strategic_analysis_citations"
            },
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER_RESEARCH, "model": LLM_MODEL_RESEARCH},
                    "temperature": LLM_TEMPERATURE_RESEARCH,
                    "max_tokens": LLM_MAX_TOKENS_RESEARCH
                }
            }
        },

        # --- 11. Step 4: Prompt Constructor for Talking Points ---
        "step4_talking_points_prompt": {
            "node_id": "step4_talking_points_prompt",
            "node_name": "prompt_constructor",
            "private_input_mode": True,
            "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step3_passthrough_keys,
            "node_config": {
                "prompt_templates": {
                    "talking_points_system_prompt": {
                        "id": "talking_points_system_prompt",
                        "template": STEP4_SYSTEM_PROMPT,
                        "variables": {},
                        "construct_options": {}
                    },
                    "talking_points_user_prompt": {
                        "id": "talking_points_user_prompt",
                        "template": """Create personalized email talking points that prove ContentQ understands this prospect's business and content opportunity. Use all previous analysis context to create highly specific, data-driven insights.

## Personalized Talking Points Generation

### Company Profile
**Company:** {company_name}  
**Individual:** {first_name} {last_name}, {title}  
**Website:** {website_url}

### Complete Analysis Context

**Step 1 - Qualification Analysis:**
{qualification_analysis}

**Step 1 - Qualification Citations:**
{qualification_citations}

**Step 2 - ContentQ Scoring & Content Analysis:**
{contentq_analysis}

**Step 2 - ContentQ Citations:**
{contentq_citations}

**Step 3 - Strategic Content Opportunity Analysis:**
{strategic_analysis}

**Step 3 - Strategic Citations:**
{strategic_citations}

### Talking Points Requirements

**GOAL:** Generate 4 specific insights that demonstrate deep expertise and create urgency for ContentQ's services.

**TALKING POINT CRITERIA:**
- Specific to their company/industry (not generic)
- Based on real research findings from analysis above
- Shows we understand their business context intimately
- Creates urgency for content marketing investment
- Positions ContentQ as the expert solution
- Include reasoning and citations for each point

**CONTENTQ VALUE PROPS BY INDUSTRY:**
- SaaS/Tech: Technical thought leadership, developer authority, product differentiation
- Fintech: Regulatory expertise, trust building, compliance content  
- Healthcare: Clinical authority, patient education, HIPAA-compliant content
- Industrial: Technical expertise, safety/compliance, B2B education

### Output Requirements

Generate structured output with detailed reasoning and citations for each talking point. Extract the ContentQ score from the analysis above and include it in your response.

IMPORTANT: while citing sources in the citations field, make sure to cite the source of the data (URL, snippet, title, etc.).
""",
                        "variables": {
                            "company_name": None,
                            "first_name": None,
                            "last_name": None,
                            "title": None,
                            "website_url": None,
                            "qualification_analysis": None,
                            "qualification_citations": None,
                            "contentq_analysis": None,
                            "contentq_citations": None,
                            "strategic_analysis": None,
                            "strategic_citations": None
                        },
                        "construct_options": {
                            "company_name": "Company",
                            "first_name": "firstName",
                            "last_name": "lastName",
                            "title": "jobTitle",
                            "website_url": "companyWebsite",
                            "qualification_analysis": "qualification_result",
                            "qualification_citations": "qualification_result_citations",
                            "contentq_analysis": "contentq_and_content_analysis",
                            "contentq_citations": "contentq_and_content_analysis_citations",
                            "strategic_analysis": "strategic_analysis",
                            "strategic_citations": "strategic_analysis_citations"
                        }
                    }
                }
            }
        },

        # --- 12. Step 4: Personalized Talking Points + Pitch Generation ---
        "step4_talking_points": {
            "node_id": "step4_talking_points",
            "node_name": "llm",
            "private_input_mode": True,
            # "private_output_mode": True,
            "output_private_output_to_central_state": True,
            "private_output_passthrough_data_to_central_state_keys": step3_passthrough_keys,
            "private_output_to_central_state_node_output_key": "talking_points_result",
            # "write_to_private_output_passthrough_data_from_output_mappings": {
            #     "structured_output": "final_talking_points"
            # },
            "node_config": {
                "llm_config": {
                    "model_spec": {"provider": LLM_PROVIDER_WRITER, "model": LLM_MODEL_WRITER},
                    "temperature": LLM_TEMPERATURE_WRITER,
                    "max_tokens": LLM_MAX_TOKENS_WRITER
                },
                "output_schema": {
                    "dynamic_schema_spec": {
                        "schema_name": "TalkingPointsWithReasoningResult",
                        "fields": {
                            "contentq_score": {
                                "type": "float",
                                "required": True,
                                "description": "ContentQ score extracted from previous analysis (e.g., 85.0)"
                            },
                            "contentq_score_text": {
                                "type": "str",
                                "required": True,
                                "description": "ContentQ score extracted from previous analysis (e.g., '85/100 - 🔥 ON FIRE')"
                            },
                            "talking_point_1_reasoning_citations": {
                                "type": "str",
                                "required": True,
                                "description": "Detailed reasoning and citations for talking point 1"
                            },
                            "talking_point_1": {
                                "type": "str",
                                "required": True,
                                "description": "First talking point - business context observation"
                            },
                            "talking_point_2_reasoning_citations": {
                                "type": "str",
                                "required": True,
                                "description": "Detailed reasoning and citations for talking point 2"
                            },
                            "talking_point_2": {
                                "type": "str", 
                                "required": True,
                                "description": "Second talking point - content gap insight"
                            },
                            "talking_point_3_reasoning_citations": {
                                "type": "str",
                                "required": True,
                                "description": "Detailed reasoning and citations for talking point 3"
                            },
                            "talking_point_3": {
                                "type": "str",
                                "required": True,
                                "description": "Third talking point - authority opportunity"
                            },
                            "talking_point_4_reasoning_citations": {
                                "type": "str",
                                "required": True,
                                "description": "Detailed reasoning and citations for talking point 4"
                            },
                            "talking_point_4": {
                                "type": "str",
                                "required": True,
                                "description": "Fourth talking point - timing/urgency factor"
                            },
                            "contentq_pitch_reasoning_citations": {
                                "type": "str",
                                "required": True,
                                "description": "Strategic reasoning behind the pitch with supporting evidence"
                            },
                            "contentq_pitch": {
                                "type": "str",
                                "required": True,
                                "description": "2-3 sentence personalized value proposition"
                            },
                            "subject_line_reasoning": {
                                "type": "str",
                                "required": True,
                                "description": "Psychology and strategy behind the subject line choice"
                            },
                            "email_subject_line": {
                                "type": "str",
                                "required": True,
                                "description": "Specific, curiosity-driven email subject line"
                            },
                        }
                    }
                }
            }
        },

        # --- 13. Output Node with Fan-In ---
        "output_node": {
            "node_id": "output_node",
            "node_name": "output_node",
            "enable_node_fan_in": True,
            "node_config": {}
        }
    },

    # --- Edges Defining Data Flow ---
    "edges": [
        # Input to state and router
        {"src_node_id": "input_node", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "leads_to_process", "dst_field": "original_leads"}
        ]},
        
        # Input to Step 1 router
        {"src_node_id": "input_node", "dst_node_id": "route_leads_to_qualification", "mappings": [
            {"src_field": "leads_to_process", "dst_field": "leads_to_process"}
        ]},
        
        # Step 1 router to qualification prompt constructor (private mode)
        {"src_node_id": "route_leads_to_qualification", "dst_node_id": "step1_qualification_prompt", "mappings": []},
        
        # Step 1 prompt constructor to qualification LLM
        {"src_node_id": "step1_qualification_prompt", "dst_node_id": "step1_qualification_assessment", "mappings": [
            {"src_field": "qualification_system_prompt", "dst_field": "system_prompt"},
            {"src_field": "qualification_user_prompt", "dst_field": "user_prompt"}
        ]},

        {"src_node_id": "step1_qualification_assessment", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "structured_output", "dst_field": "qualification_results"},
        ]},

        {"src_node_id": "step1_qualification_assessment", "dst_node_id": "filter_qualified_leads", "mappings": []},
        
        # State to filter (collect all qualification results)
        {"src_node_id": "$graph_state", "dst_node_id": "filter_qualified_leads", "mappings": [
            {"src_field": "qualification_results", "dst_field": "qualification_results"}
        ]},
        
        # Filter to Step 2 router
        {"src_node_id": "filter_qualified_leads", "dst_node_id": "route_qualified_to_step2", "mappings": [
            {"src_field": "filtered_data", "dst_field": "filtered_data"}
        ]},
        
        # Step 2 router to ContentQ prompt constructor (private mode)
        {"src_node_id": "route_qualified_to_step2", "dst_node_id": "step2_contentq_prompt", "mappings": []},
        
        # Step 2 prompt constructor to ContentQ scoring LLM
        {"src_node_id": "step2_contentq_prompt", "dst_node_id": "step2_contentq_scoring", "mappings": [
            {"src_field": "contentq_system_prompt", "dst_field": "system_prompt"},
            {"src_field": "contentq_user_prompt", "dst_field": "user_prompt"}
        ]},
        
        # Step 2 to Step 3 prompt constructor (private mode with passthrough data)
        {"src_node_id": "step2_contentq_scoring", "dst_node_id": "step3_strategic_prompt", "mappings": []},
        
        # Step 3 prompt constructor to strategic opportunity LLM
        {"src_node_id": "step3_strategic_prompt", "dst_node_id": "step3_strategic_opportunity", "mappings": [
            {"src_field": "strategic_system_prompt", "dst_field": "system_prompt"},
            {"src_field": "strategic_user_prompt", "dst_field": "user_prompt"}
        ]},
        
        # Step 3 to Step 4 prompt constructor (private mode with passthrough data)
        {"src_node_id": "step3_strategic_opportunity", "dst_node_id": "step4_talking_points_prompt", "mappings": []},
        
        # Step 4 prompt constructor to talking points LLM
        {"src_node_id": "step4_talking_points_prompt", "dst_node_id": "step4_talking_points", "mappings": [
            {"src_field": "talking_points_system_prompt", "dst_field": "system_prompt"},
            {"src_field": "talking_points_user_prompt", "dst_field": "user_prompt"}
        ]},
        
        # Step 4 to output (with fan-in)
        {"src_node_id": "step4_talking_points", "dst_node_id": "output_node", "mappings": []},

        {"src_node_id": "step4_talking_points", "dst_node_id": "$graph_state", "mappings": [
            {"src_field": "structured_output", "dst_field": "final_results"},
        ]},
        
        # State to output for final collection
        {"src_node_id": "$graph_state", "dst_node_id": "output_node", "mappings": [
            {"src_field": "final_results", "dst_field": "processed_leads"},
            # {"src_field": "original_leads", "dst_field": "original_leads"}
        ]}
    ],

    # Define start and end
    "input_node_id": "input_node",
    "output_node_id": "output_node",

    # State reducers - collect all results
    "metadata": {
        "$graph_state": {
            "reducer": {
                "qualification_results": "collect_values",
                "final_results": "collect_values"
            }
        }
    }
}

# --- Test Execution Logic ---
from kiwi_client.test_run_workflow_client import (
    run_workflow_test,
    SetupDocInfo,
    CleanupDocInfo
)
from kiwi_client.schemas.workflow_constants import WorkflowRunStatus

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
            
            # Qualification result fields
            qualification_result = lead.get('qualification_result', {})
            row['industry'] = qualification_result.get('industry', '')
            row['company_info'] = qualification_result.get('company_info', '')
            row['funding_stage'] = qualification_result.get('funding_stage', '')
            row['individual_info'] = qualification_result.get('individual_info', '')
            row['employee_count_estimate'] = qualification_result.get('employee_count_estimate', '')
            row['qualification_reasoning'] = qualification_result.get('qualification_reasoning', '')
            row['qualification_check_passed'] = qualification_result.get('qualification_check_passed', False)
            
            # ContentQ analysis (truncated for CSV readability)
            contentq_analysis = lead.get('contentq_and_content_analysis', '')
            row['contentq_analysis_summary'] = contentq_analysis[:500] + '...' if len(contentq_analysis) > 500 else contentq_analysis
            
            # Strategic analysis (truncated for CSV readability)  
            strategic_analysis = lead.get('strategic_analysis', '')
            row['strategic_analysis_summary'] = strategic_analysis[:500] + '...' if len(strategic_analysis) > 500 else strategic_analysis
            
            # Talking points result
            talking_points_result = lead.get('talking_points_result', {})
            row['contentq_score'] = talking_points_result.get('contentq_score', 0.0)
            row['contentq_score_text'] = talking_points_result.get('contentq_score_text', '')
            row['contentq_pitch'] = talking_points_result.get('contentq_pitch', '')
            row['email_subject_line'] = talking_points_result.get('email_subject_line', '')
            
            # Individual talking points
            row['talking_point_1'] = talking_points_result.get('talking_point_1', '')
            row['talking_point_2'] = talking_points_result.get('talking_point_2', '')
            row['talking_point_3'] = talking_points_result.get('talking_point_3', '')
            row['talking_point_4'] = talking_points_result.get('talking_point_4', '')
            
            # Reasoning for talking points (truncated)
            for i in range(1, 5):
                reasoning_key = f'talking_point_{i}_reasoning_citations'
                reasoning = talking_points_result.get(reasoning_key, '')
                row[f'talking_point_{i}_reasoning'] = reasoning[:300] + '...' if len(reasoning) > 300 else reasoning
            
            # ContentQ pitch reasoning
            pitch_reasoning = talking_points_result.get('contentq_pitch_reasoning_citations', '')
            row['contentq_pitch_reasoning'] = pitch_reasoning[:300] + '...' if len(pitch_reasoning) > 300 else pitch_reasoning
            
            # Subject line reasoning
            subject_reasoning = talking_points_result.get('subject_line_reasoning', '')
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

async def main_test_lead_scoring(input_csv: Optional[str] = None, 
                                  output_csv: Optional[str] = None,
                                  start_row: int = 0,
                                  end_row: Optional[int] = None):
    """
    Main test function for the lead scoring workflow.
    
    Args:
        input_csv: Path to input CSV file with lead data
        output_csv: Path to output CSV file for results  
        start_row: Starting row index for processing (0-based, excluding header)
        end_row: Ending row index for processing (0-based, exclusive)
    """
    test_name = "Lead Scoring and Personalized Talking Points Generation"
    print(f"--- Starting {test_name} ---")
    
    # Determine input data source
    if input_csv and Path(input_csv).exists():
        print(f"Loading leads from CSV: {input_csv}")
        print(f"Processing rows {start_row} to {end_row if end_row else 'end'}")
        
        # Load CSV data with row range filtering
        leads_data = load_csv_data(input_csv, start_row, end_row)
        initial_inputs = {"leads_to_process": leads_data}
        
        print(f"Loaded {len(leads_data)} leads from CSV")
    else:
        if input_csv:
            print(f"CSV file not found: {input_csv}")
        print("Using default test inputs (hardcoded sample data)")
        initial_inputs = TEST_INPUTS
    
    print("\n--- Running Workflow Test ---")
    final_run_status_obj, final_run_outputs = await run_workflow_test(
        test_name=test_name,
        workflow_graph_schema=workflow_graph_schema,
        initial_inputs=initial_inputs,
        expected_final_status=WorkflowRunStatus.COMPLETED,
        setup_docs=None,
        cleanup_docs=None,
        # validate_output_func=validate_output,
        stream_intermediate_results=False,
        poll_interval_sec=5,
        timeout_sec=600  # 10 minutes for comprehensive research and analysis
    )
    
    print(f"\n--- Test completed with status: {final_run_status_obj} ---")
    
    # Save results to CSV if output file specified
    if output_csv and final_run_outputs:
        print(f"\nSaving results to CSV: {output_csv}")
        save_results_to_csv(final_run_outputs, output_csv)
        print(f"Results saved successfully to: {output_csv}")
    
    return final_run_status_obj, final_run_outputs


def parse_arguments():
    """Parse command line arguments for CSV input/output functionality."""
    parser = argparse.ArgumentParser(
        description="Lead Scoring and Personalized Talking Points Generation Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default hardcoded test data
  python wf_lead_scoring_personalized_talking_points.py
  
  # Process entire CSV file
  python wf_lead_scoring_personalized_talking_points.py --input leads.csv --output results.csv
  
  # Process specific row range (rows 10-19, 0-based indexing)
  python wf_lead_scoring_personalized_talking_points.py --input leads.csv --output results.csv --start-row 10 --end-row 20
  
  # Process from row 5 to end of file
  python wf_lead_scoring_personalized_talking_points.py --input leads.csv --output results.csv --start-row 5

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
    start_row = 0
    end_row = 10

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
    print(f"  Row range: {args.start_row} to {args.end_row if args.end_row else 'end'}")
    print()
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        print("Async event loop already running. Scheduling task...")
        loop.create_task(main_test_lead_scoring(
            input_csv=args.input,
            output_csv=args.output,
            start_row=args.start_row,
            end_row=args.end_row
        ))
    else:
        print("Starting new async event loop...")
        asyncio.run(main_test_lead_scoring(
            input_csv=args.input,
            output_csv=args.output,
            start_row=args.start_row,
            end_row=args.end_row
        ))
