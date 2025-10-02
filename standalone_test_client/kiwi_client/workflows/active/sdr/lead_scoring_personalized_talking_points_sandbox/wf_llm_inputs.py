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

STEP_1_QUALIFICATION_USER_PROMPT = """Goal: Fast company fit assessment + foundation data

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

Please research this company and individual thoroughly using web search, then provide your assessment."""

STEP_1_QUALIFICATION_OUTPUT_SCHEMA = {
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

STEP2_SYSTEM_PROMPT = """You are applying ContentQ's proven lead scoring methodology. You are an expert at evaluating B2B companies for content marketing opportunities and calculating precise scores based on multiple business factors.

Use your knowledge of B2B SaaS, funding stages, content marketing, and competitive landscapes to provide accurate assessments."""

STEP_2_CONTENTQ_USER_PROMPT = """You are applying ContentQ's proven lead scoring methodology. Provide a comprehensive analysis in structured markdown format.

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

Please provide detailed analysis with specific citations and reasoning for each section. Use actual data points and sources where available. Reference the citations provided above when making claims."""

STEP3_SYSTEM_PROMPT = """You are a senior content strategist at ContentQ with deep expertise in B2B technical content marketing. Your specialty is identifying unique content opportunities that drive measurable business outcomes.

Focus on strategic, high-impact content opportunities that leverage the company's unique position and the individual's expertise to create competitive advantages."""

STEP_3_STRATEGIC_USER_PROMPT = """You are a senior content strategist at ContentQ. Provide a comprehensive strategic analysis in structured markdown format.

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

Please provide detailed strategic analysis with specific reasoning, citations, and actionable recommendations for each section. Focus on measurable business outcomes and competitive advantages."""

STEP4_SYSTEM_PROMPT = """You are a senior sales development expert at ContentQ, skilled at creating personalized, research-backed talking points that demonstrate deep understanding of prospects' businesses.

Your talking points should be specific, insightful, and create urgency while positioning ContentQ as the expert solution for their content marketing needs."""

STEP_4_TALKING_POINTS_USER_PROMPT = """Create personalized email talking points that prove ContentQ understands this prospect's business and content opportunity. Use all previous analysis context to create highly specific, data-driven insights.

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
"""

STEP4_TALKING_POINTS_OUTPUT_SCHEMA = {
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
