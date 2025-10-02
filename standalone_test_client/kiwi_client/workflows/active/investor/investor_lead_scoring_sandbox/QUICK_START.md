# Quick Start Guide - Investor Lead Scoring Workflow

## 🚀 Get Started in 5 Minutes

### 1. Setup Environment

```bash
# Navigate to the project root
cd standalone_test_client

# Install dependencies
poetry install

# Create .env file in standalone_test_client/kiwi_client/.env
cat > kiwi_client/.env << EOF
TEST_ENV=prod
TEST_USER_EMAIL=your@email.com
TEST_USER_PASSWORD=yourpassword
TEST_ORG_ID=your_org_id
TEST_USER_ID=your_user_id
EOF
```

### 2. Prepare Your Data

Create or use the provided `sample_investors.csv` with the **new 14-column structure**:
- **Required**: `First Name`, `Last Name`
- **Optional**: `Title`, `Firm/Company`, `Firm ID`, `Investor Type`, `Investor Role Detail`, `Relationship Status`, `LinkedIn URL`, `Twitter URL`, `Crunchbase URL`, `Investment Criteria`, `Notes`, `Source Sheets`

Example:
```csv
First Name,Last Name,Title,Firm/Company,Firm ID,Investor Type,Investor Role Detail,Relationship Status,LinkedIn URL,Twitter URL,Crunchbase URL,Investment Criteria,Notes,Source Sheets
Oliver,Hsu,Investment Partner,Andreessen Horowitz,FIRM_001,VC/Institutional,VC (Partner/Principal),WARM,https://www.linkedin.com/in/ohsu,https://twitter.com/oyhsu,,AI/B2B SaaS; Seed to Series A,Partner at US-based VC,Test Data
Abraham,Cohen,Partner,Accel,FIRM_002,VC/Institutional,VC (Partner/Principal),WARM,https://www.linkedin.com/in/abiejcohen/,,,,Strong AI investment thesis,Test Data
```

**Note**: LinkedIn URL is optional - if missing, the workflow will automatically find it using Perplexity!

### 3. Run the Workflow

```bash
# Navigate to the workflow testing directory
cd kiwi_client/workflows/active/investor/investor_lead_scoring_sandbox/wf_testing

# Run with sample data (processes 3 sample investors)
PYTHONPATH=$(pwd)/../../../../:$(pwd)/../../../../services poetry run python wf_runner.py \
  --input sample_investors.csv \
  --output results.csv \
  --end-row 3

# Or process your own CSV
PYTHONPATH=$(pwd)/../../../../:$(pwd)/../../../../services poetry run python wf_runner.py \
  --input your_investors.csv \
  --output your_results.csv
```

### 4. View Results

Open `results.csv` to see:
- **Total Score**: 0-100 points (new simplified framework!)
- **Score Tier**: A (85-100), B (70-84), C (50-69), D (<50)
- **Employment Verification**: Current firm, title, firm change detection
- **Detailed Scoring Breakdown**:
  - Fund Vitals (0-25): Fund size + activity
  - Lead Capability (0-25): Lead behavior + check size
  - Thesis Alignment (0-30): AI B2B + MarTech + DevTools/PLG
  - Partner Value (0-15): Title + background
  - Strategic Factors (0-5): Geography + momentum
- **9 Actionable Intelligence Sections**: Portfolio pattern, partner insights (from LinkedIn posts!), investment pace, value-add evidence, deal preferences, recent positioning, fund context, competitive intel, pitch prep
- **Deep Research Report**: Full research backing the scores
- **LinkedIn Data**: Profile + 20 recent posts analysis

## ⚡ Common Commands

### Process Specific Rows
```bash
# Process rows 0-10
PYTHONPATH=$(pwd)/../../../../:$(pwd)/../../../../services poetry run python wf_runner.py \
  --input investors.csv \
  --output results.csv \
  --start-row 0 \
  --end-row 10
```

### Faster Processing (More Parallel Batches)
```bash
# Use 5 concurrent batches instead of default 2
PYTHONPATH=$(pwd)/../../../../:$(pwd)/../../../../services poetry run python wf_runner.py \
  --input investors.csv \
  --output results.csv \
  --batch-parallelism-limit 5
```

### Sequential Processing (Safer for API Limits)
```bash
# Process one batch at a time with delays
PYTHONPATH=$(pwd)/../../../../:$(pwd)/../../../../services poetry run python wf_runner.py \
  --input investors.csv \
  --output results.csv \
  --sequential \
  --delay 90
```

### Combine Previous Results
```bash
# If workflow was interrupted, combine existing batch files
PYTHONPATH=$(pwd)/../../../../:$(pwd)/../../../../services poetry run python wf_runner.py \
  --output results.csv \
  --combine-only
```

## 📊 What You Get

### Input (Per Investor)
- Name, title, firm/company, firm ID
- Investor type and role detail
- Relationship status (WARM/COLD)
- LinkedIn URL (auto-found if missing!), Twitter URL, Crunchbase URL
- Investment criteria, notes, source sheets

### Output (Per Investor)
- **Total Score**: 0-100 points (100-point framework)
- **Tier**: A (85-100), B (70-84), C (50-69), D (<50)
- **Employment Verification**: Current firm/title (detects if partner switched firms!)
- **Fund Vitals (0-25)**: Fund size, recent activity in 2024-2025, fund number, latest raise date
- **Lead Capability (0-25) - CRITICAL**: Lead behavior pattern, led rounds count, typical check size
- **Thesis Alignment (0-30)**: AI B2B portfolio, MarTech portfolio, explicit thesis, DevTools/API focus, PLG focus
- **Partner Value (0-15)**: Title/authority, operational background (ex-founder MarTech/B2B, ex-CMO, ex-VP Sales, active creator)
- **Strategic Factors (0-5)**: Geography (US/India), momentum (new fund, exits, follow-ons)
- **Disqualification**: Only if Fund AUM < $20M
- **9 Actionable Intelligence Sections**:
  1. Portfolio Pattern
  2. Partner Insights (uses LinkedIn posts!)
  3. Investment Pace & Process
  4. Value-Add Evidence (specific examples)
  5. Deal Preferences
  6. Recent Positioning (exact quotes from posts)
  7. Fund Context
  8. Competitive Intel (portfolio gaps for AI B2B content/marketing)
  9. Pitch Prep (reference + angle + opening)
- **LinkedIn Posts Analysis**: Insights from 20 recent posts
- **Notable Portfolio Companies**: Top 8-10 companies
- **Deep Research Report**: Full research backing the scores

## ⏱️ Performance

- **Per Investor**: 2-3 minutes (includes URL finding, LinkedIn scraping, deep research, extraction)
- **10 Investors**: ~20-30 minutes with parallel processing
- **100 Investors**: ~3-5 hours with 2-3 concurrent batches

## 💰 Cost

- **~$0.60-1.20 per investor lead**
  - LinkedIn URL Finding (Perplexity): $0.02-0.05 (only if missing)
  - LinkedIn Scraping (Apify): $0.05-0.10
  - Deep Research (Perplexity): $0.40-0.80
  - Extraction (Claude Sonnet 4.5): $0.15-0.25

**Cost Savings**: Provide LinkedIn URLs in your CSV to skip URL finding step!

## ✨ New Features (100-Point Framework)

1. **Automatic LinkedIn URL Finding**: Missing URLs? No problem - Perplexity finds them automatically
2. **Firm Change Detection**: Identifies if partner moved from input firm to a new firm
3. **LinkedIn Posts Analysis**: Captures 20 recent posts for real-time insights
4. **Simplified 100-Point Scoring**: Easier to interpret than old 200-point system
5. **Employment Verification**: Validates current employment before scoring
6. **9 Actionable Intelligence Sections**: Structured pitch prep directly from playbook
7. **No Risk Penalties**: Only positive scoring (removed penalty system)
8. **Single DQ Criterion**: Only Fund AUM < $20M disqualifies

## 🔧 Troubleshooting

### "CSV file not found"
→ Check the file path is correct, use absolute paths

### "Could not map required fields"
→ Ensure your CSV has `First Name` and `Last Name` columns (only 2 required!)

### Workflow times out
→ Default timeout is 30 minutes per batch, which is usually enough. Increase in `wf_runner.py` if needed.

### Batch fails
→ Check `logs/kiwiq_backend.log` for detailed errors

### Need to resume
→ Use `--combine-only` to merge successful batch results

### LinkedIn URL not found
→ Workflow still proceeds with research using name + firm. Check `linkedin_url_found_by_perplexity` column in output.

## 📖 Full Documentation

See `investor_workflow_full_documentation.md` for:
- Complete CSV format specification
- All 80+ output columns explained
- Scoring methodology details (100-point framework)
- Advanced configuration options
- Architecture and design decisions
- Pydantic schema reference

## 🎯 Next Steps

1. **Test with 3-5 investors first** to validate output quality
2. **Review the scoring** against the 100-point playbook rubric
3. **Check employment verification** - are firm changes detected correctly?
4. **Review LinkedIn posts usage** - see how they inform partner insights
5. **Adjust prompts if needed** (see `wf_llm_inputs.py`)
6. **Scale up** to your full investor list
7. **Use actionable intelligence** to craft personalized outreach

---

**Version**: 2.0 (100-Point Framework)
**Need Help?** Check `investor_workflow_full_documentation.md` or review the workflow code with detailed comments.
