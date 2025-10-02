# Investor Lead Scoring Workflow

Automated investor qualification and scoring workflow based on the **Investor Lead Scoring Playbook** methodology. This workflow conducts deep research on venture capital investors and assigns comprehensive scores based on the **100-point framework**.

## Overview

This workflow processes investor leads through multiple intelligent steps:

1. **LinkedIn URL Discovery (Optional - Perplexity Sonar)**: If LinkedIn URL is missing, uses Perplexity to find the investor's current LinkedIn profile, detecting firm changes.

2. **LinkedIn Data Collection (Apify)**: Scrapes LinkedIn profile data AND 20 recent posts for insights into partner's interests, thesis, and recent activity.

3. **Deep Research (Perplexity Sonar Deep Research)**: Conducts autonomous, comprehensive research on the investor/fund using web search to gather facts about fund size, portfolio composition, partner background, recent activity, and more.

4. **Structured Extraction & Scoring (Claude Sonnet 4.5)**: Analyzes the research report, LinkedIn profile, and posts to calculate scores using the 100-point framework, verify employment, and generate actionable intelligence.

### Scoring Framework (Total: 100 points)

- **Fund Vitals (0-25 pts)**: Fund size + recent activity (2024-2025)
- **Lead Capability (0-25 pts)**: Lead behavior + typical check size
- **Thesis Alignment (0-30 pts)**: AI B2B + MarTech portfolio + explicit thesis + focus areas (DevTools/API, PLG)
- **Partner Value (0-15 pts)**: Title + background (ex-founder MarTech/B2B, ex-CMO, ex-VP Sales, active creator)
- **Strategic Factors (0-5 pts)**: Geography (US/India) + momentum (new fund, exits, follow-ons)

**Single Disqualification Criterion**: Fund AUM < $20M

### Priority Tiers (0-100 Scale)

- **🔥 A-Tier (85-100)**: Top Priority - Must pursue immediately
- **⭐ B-Tier (70-84)**: High Priority - Direct outreach
- **📋 C-Tier (50-69)**: Medium Priority - Consider timing
- **❄️ D-Tier (<50)**: Low Priority - Backup list

## Input CSV Format

The workflow accepts a CSV file with the following **new 14-column structure**:

| Required | Column | Aliases | Description |
|----------|--------|---------|-------------|
| ✅ | `First Name` | `first_name`, `First` | Partner's first name |
| ✅ | `Last Name` | `last_name`, `Last` | Partner's last name |
| | `Title` | `title`, `Current Title`, `Role` | Partner's title |
| | `Firm/Company` | `firm_company`, `Company`, `Fund`, `Firm` | Fund/firm name |
| | `Firm ID` | `firm_id`, `FirmID` | Firm identifier (optional) |
| | `Investor Type` | `investor_type`, `Type` | Type (e.g., "VC/Institutional") |
| | `Investor Role Detail` | `investor_role_detail`, `Role Detail` | Role detail (e.g., "VC (Partner/Principal)") |
| | `Relationship Status` | `relationship_status`, `Status` | Status (e.g., "WARM", "COLD") |
| | `LinkedIn URL` | `linkedin_url`, `LinkedIn` | LinkedIn profile URL (auto-found if missing) |
| | `Twitter URL` | `twitter_url`, `Twitter` | Twitter profile URL (optional) |
| | `Crunchbase URL` | `crunchbase_url`, `Crunchbase` | Crunchbase URL (optional) |
| | `Investment Criteria` | `investment_criteria`, `Criteria` | Known criteria (optional) |
| | `Notes` | `notes`, `Detailed Notes` | Reference notes (optional) |
| | `Source Sheets` | `source_sheets`, `Source` | Data source (optional) |

**Note**: If LinkedIn URL is empty, the workflow automatically uses Perplexity to find it, including detection of firm changes.

### Example CSV

```csv
First Name,Last Name,Title,Firm/Company,Firm ID,Investor Type,Investor Role Detail,Relationship Status,LinkedIn URL,Twitter URL,Crunchbase URL,Investment Criteria,Notes,Source Sheets
Oliver,Hsu,Investment Partner,Andreessen Horowitz,FIRM_001,VC/Institutional,VC (Partner/Principal),WARM,https://www.linkedin.com/in/ohsu,https://twitter.com/oyhsu,,AI/B2B SaaS; Seed to Series A,Partner at US-based VC,Test Data
Spandan,(Dan) Saha,Mentor,Nasdaq Entrepreneurial Center,FIRM_3193,VC/Institutional,VC (Other),COLD,,,,,Focus on later stages,Current Master List
Geoffrey,(Geoff) Rodgers,CEO/Principal,The Lazarus Group LLC,FIRM_3194,VC/Institutional,VC (Partner/Principal),WARM,,,,,Active VC professional; AI/ML focus,Current Master List
```

## Output CSV Format

The output CSV contains comprehensive scoring results with 80+ columns including:

### Input Data (Preserved)
- All 14 input columns prefixed with `input_`
- `linkedin_url_found_by_perplexity` - URL found if originally missing

### Employment Verification
- `current_fund_verified` - Current fund name (may differ from input)
- `current_title_verified` - Current title
- `still_at_input_firm` - Boolean
- `firm_change_detected` - Boolean
- `firm_change_details` - Details if partner moved firms
- `still_in_vc` - Still in venture capital?
- `employment_notes` - Additional notes

### Scoring Summary (100-Point Framework)
- `total_score` - Total score (0-100)
- `score_tier` - A (85-100), B (70-84), C (50-69), D (<50)
- `recommended_action` - Top Priority, High Priority, Medium, Low
- `is_disqualified` - Boolean (only if Fund AUM < $20M)
- `disqualification_reason` - Reason if DQ'd

### Fund Vitals (0-25 points)
- `fund_size_usd`, `fund_size_points`, `fund_size_reasoning`
- `fund_number`, `latest_fund_raise_date`
- `recent_activity_2024_2025`
- `deals_in_2025_count`, `deals_in_2024_count`
- `activity_points`, `activity_reasoning`
- `fund_vitals_total`

### Lead Capability (0-25 points)
- `lead_behavior` - Pattern (Regularly leads, Co-leads, etc.)
- `led_rounds_count`, `led_round_examples`
- `lead_behavior_points`, `lead_behavior_reasoning`
- `typical_check_size`, `check_size_points`, `check_size_reasoning`
- `lead_capability_total`

### Thesis Alignment (0-30 points)
- `ai_b2b_portfolio_count`, `ai_b2b_companies`, `ai_b2b_points`
- `martech_portfolio_count`, `martech_companies`, `martech_points`
- `has_explicit_ai_b2b_thesis`, `investment_thesis_summary`, `thesis_points`
- `devtools_api_portfolio_count`, `devtools_api_companies`, `has_devtools_api_focus`, `devtools_api_points`
- `plg_portfolio_count`, `plg_companies`, `has_plg_focus`, `plg_points`
- `thesis_alignment_total`

### Partner Value (0-15 points)
- `partner_title`, `decision_authority_level`, `title_points`, `title_reasoning`
- `operational_background_summary`
- `is_ex_founder_martech_b2b`, `founder_details`, `ex_founder_points`
- `is_ex_cmo_vp_marketing`, `cmo_marketing_details`, `ex_cmo_marketing_points`
- `is_ex_vp_sales_growth`, `vp_sales_growth_details`, `ex_vp_sales_points`
- `is_active_creator`, `active_creator_details`, `active_creator_points`
- `background_total_points`, `partner_value_total`

### Strategic Factors (0-5 points)
- `fund_hq_location`, `geography_category`, `geography_points`
- `has_new_fund_under_18mo`, `new_fund_details`
- `has_recent_exits`, `exits_count_3yr`, `exit_details`
- `has_portfolio_followons`, `followon_details`
- `momentum_points`, `momentum_reasoning`
- `strategic_factors_total`

### Actionable Intelligence (9 Sections from Playbook)
- `portfolio_pattern` - Stage, traction, founder profiles
- `partner_insights` - Recent content, beliefs (uses LinkedIn posts!)
- `investment_pace_and_process` - Timeline, IC process
- `value_add_evidence` - Specific examples with numbers
- `deal_preferences` - Traction bar, team needs, passes/excites
- `recent_positioning` - Thesis updates with exact quotes from posts
- `fund_context` - Deployment stage, team changes
- `competitive_intel` - Portfolio gaps for AI B2B content/marketing tools
- `pitch_prep` - Reference + Angle + Opening hook

### Additional Context
- `notable_portfolio_companies` - Top 8-10 companies
- `research_confidence` - High/Medium/Low
- `missing_critical_info` - List of missing data points

## Usage

### Prerequisites

1. **Environment Setup**:
   ```bash
   cd standalone_test_client
   poetry install
   ```

2. **Environment Variables** (`.env` file in `standalone_test_client/kiwi_client/`):
   ```
   TEST_ENV=prod
   TEST_USER_EMAIL=your@email.com
   TEST_USER_PASSWORD=yourpassword
   TEST_ORG_ID=your_org_id
   TEST_USER_ID=your_user_id
   ```

3. **Prepare Input CSV**: Place your investor leads CSV in the `wf_testing/` directory

### Running the Workflow

Navigate to the testing directory:
```bash
cd standalone_test_client/kiwi_client/workflows/active/investor/investor_lead_scoring_sandbox/wf_testing
```

#### Basic Usage (Process All Rows)

```bash
# Default: Process first 100 rows in batches of 10, parallel mode (2 concurrent)
PYTHONPATH=$(pwd)/../../../../:$(pwd)/../../../../services poetry run python wf_runner.py \
  --input investors.csv \
  --output results.csv
```

#### Custom Row Range

```bash
# Process rows 0-50
PYTHONPATH=$(pwd)/../../../../:$(pwd)/../../../../services poetry run python wf_runner.py \
  --input investors.csv \
  --output results.csv \
  --start-row 0 \
  --end-row 50 \
  --batch-size 10
```

#### Parallel Processing (Recommended)

```bash
# Process with 5 concurrent batches (faster)
PYTHONPATH=$(pwd)/../../../../:$(pwd)/../../../../services poetry run python wf_runner.py \
  --input investors.csv \
  --output results.csv \
  --batch-parallelism-limit 5
```

#### Sequential Processing

```bash
# Process batches one at a time with 90-second delays
PYTHONPATH=$(pwd)/../../../../:$(pwd)/../../../../services poetry run python wf_runner.py \
  --input investors.csv \
  --output results.csv \
  --sequential \
  --delay 90
```

#### Combine Existing Batch Results

```bash
# Combine previously processed batch files without re-running workflows
PYTHONPATH=$(pwd)/../../../../:$(pwd)/../../../../services poetry run python wf_runner.py \
  --output results.csv \
  --combine-only
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Path to input CSV file | `sample_investors.csv` |
| `--output` | Path to output CSV file | `results.csv` |
| `--start-row` | Starting row index (0-based, excluding header) | `0` |
| `--end-row` | Ending row index (exclusive) | All rows |
| `--batch-size` | Number of investors per batch | `100` |
| `--batch-folder` | Folder for batch result files | `batch_results/` |
| `--batch-parallelism-limit` | Max concurrent batches (parallel mode) | `2` |
| `--delay` | Delay between batches in seconds (sequential mode) | `60` |
| `--sequential` | Run batches sequentially instead of parallel | `False` |
| `--stop-on-failure` | Stop if any batch fails | `True` |
| `--continue-on-failure` | Continue even if batches fail | `False` |
| `--combine-only` | Only combine existing batch files | `False` |

## Performance & Cost

### Timing Estimates
- **Per Investor**: 2-3 minutes (URL finding + LinkedIn scraping + deep research + extraction)
- **Batch of 10**: ~20-30 minutes (parallel processing)
- **100 Investors**: ~3-5 hours with 2-3 concurrent batches

### Cost Estimates
- **LinkedIn URL Finding (Perplexity Sonar)**: ~$0.02-0.05 per investor (only if URL missing)
- **LinkedIn Scraping (Apify)**: ~$0.05-0.10 per investor
- **Deep Research (Perplexity Sonar Deep Research)**: ~$0.40-0.80 per investor
- **Structured Extraction (Claude Sonnet 4.5)**: ~$0.15-0.25 per investor
- **Total**: ~$0.60-1.20 per investor lead

### Optimization Tips

1. **Parallel Processing**: Use `--batch-parallelism-limit 3-5` for faster throughput
2. **Batch Size**: Keep at 10-20 investors per batch for optimal performance
3. **Sequential Mode**: Use only if you need to control API rate limits
4. **Failure Handling**: Use `--stop-on-failure` (default) for production to catch issues early
5. **Pre-filled LinkedIn URLs**: Providing LinkedIn URLs in CSV skips URL finding step, saving cost

## Workflow Architecture

```
Input CSV
   ↓
Check LinkedIn URL
   ↓
   ├─ [URL Exists] ──────────────────┐
   │                                  ↓
   └─ [URL Missing] → Find URL ──→ Scrape LinkedIn (Profile + 20 Posts)
      (Perplexity)                   ↓
                            Deep Research (Perplexity)
                                     ↓
                        Structured Extraction & Scoring (Claude)
                                     ↓
                                Output CSV
```

### Key Design Decisions

1. **Intelligent URL Discovery**: Automatically finds missing LinkedIn URLs and detects firm changes
2. **LinkedIn Posts Analysis**: Scrapes 20 recent posts for real-time insights into partner's interests and thesis
3. **Two-Step Research Pipeline**: Separates fact-gathering (Perplexity research) from judgment (Claude scoring) for better accuracy
4. **Employment Verification First**: Validates current firm before scoring (partners may have switched firms)
5. **100-Point Framework**: Simplified from 200-point system, focused on most predictive factors
6. **Single DQ Criterion**: Only disqualifies if Fund AUM < $20M
7. **9 Actionable Intelligence Sections**: Directly from playbook for pitch preparation
8. **No Data Truncation**: All output fields preserved in full for CSV export
9. **Private Mode Passthrough**: Preserves all context including research report and LinkedIn data through the pipeline
10. **Large DB Pool**: Uses `large` tier for concurrent database operations

## New Features (100-Point Framework Update)

### ✨ What's New

1. **LinkedIn URL Finder**: Automatically discovers missing LinkedIn URLs using Perplexity, including firm change detection
2. **LinkedIn Posts Scraping**: Captures 20 recent posts for insights into partner's recent interests and positioning
3. **Simplified 100-Point Scoring**: Streamlined from 200-point system for easier interpretation
4. **Employment Verification**: Validates current firm/title before scoring (uses LinkedIn as primary source)
5. **Enhanced Actionable Intelligence**: 9 structured sections directly from playbook, incorporating LinkedIn posts
6. **14-Column Input Schema**: Clearer structure with Firm ID, Investor Type, Role Detail, etc.
7. **No Risk Penalties**: Removed penalty system; only positive scoring
8. **Portfolio Gap Analysis**: Specific focus on AI B2B content/marketing tool gaps

### 🔄 Migration from Old Schema

If you have existing CSVs with old column names, the flexible column aliases will still work:
- Old `Current Company` → maps to `firm_company`
- Old `Current Title` → maps to `title`
- Old `Classification` → maps to `relationship_status`

## Troubleshooting

### Common Issues

**1. "CSV file not found" error**
- Ensure the input CSV path is correct
- Use absolute paths or paths relative to the working directory

**2. "Could not map required fields" error**
- Check that your CSV has `First Name` and `Last Name` columns
- Review the column aliases in the error message

**3. Workflow timeout**
- Deep research can take 2-3 minutes per investor
- Increase timeout if needed: edit `timeout_sec` in `wf_runner.py` (default: 1800s = 30 min)

**4. Batch failures**
- Use `--stop-on-failure` to catch issues early
- Check logs in `logs/kiwiq_backend.log` for detailed error messages
- Use `--combine-only` to merge successful batch results after fixing issues

**5. API rate limits**
- Use sequential mode with delays: `--sequential --delay 90`
- Reduce parallel processing: `--batch-parallelism-limit 2`

**6. LinkedIn URL not found**
- Workflow will still proceed with research using name + firm
- Check `linkedin_url_found_by_perplexity` column in output
- Quality may be lower without LinkedIn profile data

### Debugging Tips

1. **Test with small batch first**: Use `--end-row 5` to process just 5 investors
2. **Check batch folder**: Individual batch results in `batch_results/` show progress
3. **Review deep research reports**: Check CSV output for research quality
4. **Validate scores**: Compare scoring against the 100-point playbook rubric
5. **Check employment verification**: Review `firm_change_detected` and `firm_change_details` for accuracy

## Files in this Directory

- `wf_investor_lead_scoring_json.py` - Main workflow definition (GraphSchema)
- `wf_llm_inputs.py` - LLM prompts, Pydantic schemas, and model configurations
- `wf_testing/wf_runner.py` - Batch execution runner with CSV handling
- `wf_testing/sample_investors.csv` - Sample input data with new schema
- `Investor Lead Scoring Playbook.md` - Official 100-point scoring methodology
- `QUICK_START.md` - Quick start guide
- `investor_workflow_full_documentation.md` - This file (complete documentation)

## Next Steps

1. **Test with Sample Data**: Run on 5-10 sample investors first
2. **Review Output Quality**: Check if scoring aligns with playbook expectations
3. **Verify Employment Data**: Check `firm_change_detected` accuracy
4. **Review LinkedIn Posts Usage**: See how posts inform `partner_insights` and `recent_positioning`
5. **Tune Prompts**: Adjust `wf_llm_inputs.py` if needed for your specific use case
6. **Scale Up**: Process larger batches with parallel execution
7. **Integrate**: Use scored results with actionable intelligence for prioritized outreach

## Support & Feedback

For issues or questions about this workflow:
- Review the playbook methodology: `Investor Lead Scoring Playbook.md`
- Check workflow logs: `logs/kiwiq_backend.log`
- Review code comments in workflow files for implementation details

---

## Output CSV Column Reference

### Column Order (Total: 102 columns)

#### Group 1: Input Data (14 columns)
1. `input_first_name`
2. `input_last_name`
3. `input_title`
4. `input_firm_company`
5. `input_firm_id`
6. `input_investor_type`
7. `input_investor_role_detail`
8. `input_relationship_status`
9. `input_linkedin_url`
10. `input_twitter_url`
11. `input_crunchbase_url`
12. `input_investment_criteria`
13. `input_notes`
14. `input_source_sheets`

#### Group 2: LinkedIn URL Finding (2 columns)
15. `linkedin_url_found_by_perplexity` - Auto-found LinkedIn URL (if missing from input)
16. `linkedin_url_search_successful` - Boolean: Was URL found successfully?

#### Group 3: Current Employment Verification (7 columns)
17. `current_fund_verified` - Partner's actual current fund
18. `current_title_verified` - Partner's actual current title
19. `still_at_input_firm` - Boolean: Still at input company?
20. `firm_change_detected` - Boolean: Moved to different fund?
21. `firm_change_details` - Details of firm change if applicable
22. `still_in_vc` - Boolean: Still in venture capital?
23. `employment_notes` - Additional employment notes

#### Group 4: Primary Scores & Tier (4 columns) ⭐
**OPTIMIZED FOR QUICK REVIEW**
24. `total_score` - **PRIMARY SCORE** (0-100)
25. `score_tier` - **A (85-100), B (70-84), C (50-69), D (<50)**
26. `is_disqualified` - **DQ FLAG** (True/False)
27. `disqualification_reason` - DQ reason (only "Fund AUM < $20M")

#### Group 5: Fund Vitals (0-25 points) - 6 columns
28. `fund_vitals_score` - **Total Fund Vitals Score (0-25)**
29. `fund_size` - Fund AUM in millions
30. `fund_number` - Which fund (Fund I, II, III, etc.)
31. `latest_fund_raise_date` - Most recent fund raise date
32. `recent_activity_2024_2025` - Boolean: Active in 2024-2025?
33. `fund_vitals_reasoning` - Explanation of fund vitals score

#### Group 6: Lead Capability (0-25 points) - CRITICAL 🔥 - 7 columns
34. `lead_capability_score` - **Total Lead Capability Score (0-25)**
35. `lead_behavior_pattern` - Lead/Co-lead/Follow pattern
36. `led_rounds_count` - Number of led rounds in portfolio
37. `led_rounds_examples` - Example led rounds with details
38. `typical_check_size` - Typical investment check size
39. `can_cover_target_range` - Boolean: Can cover $400K-600K?
40. `lead_capability_reasoning` - Explanation of lead capability score

#### Group 7: Thesis Alignment (0-30 points) - 11 columns
41. `thesis_alignment_score` - **Total Thesis Alignment Score (0-30)**
42. `ai_b2b_portfolio_count` - Count of AI B2B portfolio companies
43. `ai_b2b_portfolio_companies` - List of AI B2B companies
44. `martech_portfolio_count` - Count of MarTech portfolio companies
45. `martech_portfolio_companies` - List of MarTech companies
46. `has_explicit_ai_b2b_martech_thesis` - Boolean: Explicit thesis?
47. `investment_thesis_summary` - Summary of investment thesis
48. `devtools_plg_portfolio_count` - Count of DevTools/API/PLG companies
49. `devtools_plg_portfolio_companies` - List of DevTools/PLG companies
50. `has_devtools_api_plg_focus` - Boolean: DevTools/API focus?
51. `thesis_alignment_reasoning` - Explanation of thesis alignment score

#### Group 8: Partner Value (0-15 points) - 10 columns
52. `partner_value_score` - **Total Partner Value Score (0-15)**
53. `partner_title` - Extracted partner title
54. `title_authority_level` - Partner/Principal/VP/Other
55. `is_ex_founder_martech_b2b` - Boolean: Ex-founder in MarTech/B2B?
56. `is_ex_cmo` - Boolean: Ex-CMO background?
57. `is_ex_vp_sales` - Boolean: Ex-VP Sales background?
58. `is_active_creator` - Boolean: Active content creator?
59. `operational_background_details` - Details of operational background
60. `thought_leadership_evidence` - Evidence of thought leadership
61. `partner_value_reasoning` - Explanation of partner value score

#### Group 9: Strategic Factors (0-5 points) - 7 columns
62. `strategic_factors_score` - **Total Strategic Factors Score (0-5)**
63. `fund_geography` - Fund location (US/India/Other)
64. `is_us_or_india_based` - Boolean: US or India based?
65. `has_new_fund_momentum` - Boolean: New fund raised recently?
66. `has_recent_exits` - Boolean: Recent exits in portfolio?
67. `has_follow_on_activity` - Boolean: Active follow-on investments?
68. `strategic_factors_reasoning` - Explanation of strategic factors score

#### Group 10: Actionable Intelligence Section 1 - Portfolio Pattern (3 columns)
69. `portfolio_pattern_summary` - Key portfolio patterns
70. `portfolio_pattern_ai_b2b_examples` - AI B2B portfolio examples
71. `portfolio_pattern_martech_examples` - MarTech portfolio examples

#### Group 11: Actionable Intelligence Section 2 - Partner Insights (4 columns)
72. `partner_insights_linkedin_post_themes` - Themes from LinkedIn posts
73. `partner_insights_investment_philosophy` - Investment philosophy from posts
74. `partner_insights_content_marketing_views` - Views on content/marketing
75. `partner_insights_recent_engagement` - Recent engagement topics

#### Group 12: Actionable Intelligence Section 3 - Investment Pace & Process (3 columns)
76. `investment_pace_frequency` - Investment frequency (2024-2025)
77. `investment_pace_stage_timing` - When they invest by stage
78. `investment_pace_decision_speed` - Decision-making speed indicators

#### Group 13: Actionable Intelligence Section 4 - Value-Add Evidence (3 columns)
79. `value_add_specific_examples` - Specific value-add examples
80. `value_add_areas_of_expertise` - Areas of expertise
81. `value_add_portfolio_support_style` - Support style for portfolio

#### Group 14: Actionable Intelligence Section 5 - Deal Preferences (3 columns)
82. `deal_preferences_team_size` - Preferred team size
83. `deal_preferences_revenue_stage` - Revenue stage preferences
84. `deal_preferences_business_model` - Business model preferences

#### Group 15: Actionable Intelligence Section 6 - Recent Positioning (3 columns)
85. `recent_positioning_exact_quotes` - Exact quotes from recent posts
86. `recent_positioning_timing` - When positioned (dates)
87. `recent_positioning_context` - Context of positioning

#### Group 16: Actionable Intelligence Section 7 - Fund Context (3 columns)
88. `fund_context_deployment_stage` - Current deployment stage
89. `fund_context_portfolio_construction` - Portfolio construction approach
90. `fund_context_competitive_positioning` - Competitive positioning

#### Group 17: Actionable Intelligence Section 8 - Competitive Intel (3 columns)
91. `competitive_intel_portfolio_gaps` - Portfolio gaps for AI B2B content/marketing
92. `competitive_intel_white_space` - White space opportunities
93. `competitive_intel_adjacent_investments` - Adjacent relevant investments

#### Group 18: Actionable Intelligence Section 9 - Pitch Prep (3 columns)
94. `pitch_prep_reference_point` - Specific reference point for pitch
95. `pitch_prep_angle` - Recommended pitch angle
96. `pitch_prep_opening` - Suggested opening line

#### Group 19: LinkedIn Profile Data (3 columns)
97. `linkedin_profile_data` - Full LinkedIn profile JSON
98. `linkedin_posts_data` - 20 recent LinkedIn posts JSON
99. `linkedin_posts_summary` - Summary of LinkedIn posts insights

#### Group 20: Research Report & Portfolio (3 columns)
100. `research_report` - Deep research text (full report)
101. `notable_portfolio_companies` - Top 8-10 portfolio companies
102. `research_notes` - Additional research notes

### Quick Review Workflow

When reviewing the output CSV:

1. **Sort by `total_score` (descending)** - See top prospects first (0-100 scale)
2. **Filter by `score_tier`** - Focus on A (85-100) and B (70-84) tiers
3. **Check `is_disqualified = False`** - Remove DQ'd investors
4. **Check `firm_change_detected`** - Identify partners who switched firms
5. **Review `lead_capability_score`** - Verify lead capability (critical!)
6. **Read actionable intelligence sections** - Use for personalized outreach
7. **Check `linkedin_url_found_by_perplexity`** - See if URL was auto-found

### Key Column Positions for Excel/Sheets

- **Column A (total_score)**: Primary score for sorting (0-100)
- **Column B (score_tier)**: A/B/C/D tier
- **Column C (is_disqualified)**: Quick filter column
- **Column D (disqualification_reason)**: Why DQ'd (only Fund AUM < $20M)
- **Column Q (current_fund_verified)**: What fund they're actually at NOW
- **Column S (firm_change_detected)**: Did they move firms?
- **Column T (firm_change_details)**: Where did they move to?
- **Column O (linkedin_url_found_by_perplexity)**: Auto-found LinkedIn URL

---

**Version**: 2.0 (100-Point Framework)
**Last Updated**: October 2025
**Based on**: Investor Lead Scoring Playbook (100-point rubric with 9 actionable intelligence sections)
