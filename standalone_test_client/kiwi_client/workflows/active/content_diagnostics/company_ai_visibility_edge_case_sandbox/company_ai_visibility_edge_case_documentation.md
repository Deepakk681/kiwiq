# Company AI Visibility Edge Case Workflow

## Overview
This workflow analyzes a company's AI visibility across search engines by performing competitive analysis, generating targeted search queries, executing searches across multiple platforms (Google, Bing, Perplexity), and generating comprehensive reports on the company's blog coverage and competitive positioning in AI-related searches.

## Frontend User Flow
*To be documented later*

## File Locations
- **Workflow File**: `/standalone_client/kiwi_client/workflows/active/content_diagnostics/wf_company_ai_visibility_edge_case.py`
- **LLM Inputs**: `/standalone_client/kiwi_client/workflows/active/content_diagnostics/llm_inputs/company_ai_visibility_edge_case.py`

## Key Components

### 1. Input Node
**Node ID**: `input_node`

**Purpose**: Entry point for the workflow that accepts company information and configuration

**Input Requirements**:
- `company_name`: Name of the company to analyze (required)
- `enable_cache`: Whether to use cached search results (default: true)
- `cache_lookback_days`: Number of days to look back for cached results (default: 7)

### 2. Load Context Documents
**Node ID**: `load_context_docs`

**Purpose**: Loads company documentation and context needed for analysis

**Process**:
- Loads blog company document using namespace pattern
- Document Name: `blog_company_doc`
- Namespace Pattern: `blog_company_{company_name}`

### 3. Competitive Analysis
**Node ID**: `construct_competitive_analysis_prompt` → `competitive_analysis_llm`

**Purpose**: Analyzes the competitive landscape and identifies key competitors

**Process**:
- Constructs prompt with company data
- Uses Perplexity AI for initial competitive analysis
- Identifies main competitors and market positioning

**Model Configuration**:
- Provider: Perplexity
- Model: sonar-pro
- Temperature: 0.8
- Max Tokens: 2000

### 4. Query Generation Phase

#### 4.1 Blog Coverage Queries
**Node ID**: `construct_blog_queries_prompt` → `generate_blog_queries`

**Purpose**: Generates search queries to assess blog content coverage

**Process**:
- Creates targeted queries for blog content analysis
- Focuses on company's content visibility
- Includes current date context

**Model Configuration**:
- Provider: Anthropic
- Model: claude-sonnet-4-20250514
- Temperature: 0.3
- Max Tokens: 2000

#### 4.2 Company & Competitor Queries
**Node ID**: `construct_company_comp_queries_prompt` → `generate_company_comp_queries`

**Purpose**: Generates comparative search queries for company vs competitors

**Process**:
- Creates queries comparing company with identified competitors
- Focuses on AI-related topics and visibility
- Includes market positioning queries

**Model Configuration**:
- Provider: Anthropic
- Model: claude-sonnet-4-20250514
- Temperature: 0.3
- Max Tokens: 2000

### 5. Multi-Engine Search Execution

#### 5.1 Blog Coverage Searches
**Node IDs**:
- `execute_blog_google_searches`
- `execute_blog_bing_searches`
- `execute_blog_perplexity_searches`

**Purpose**: Executes blog coverage queries across multiple search engines

**Process**:
- Runs queries on Google, Bing, and Perplexity
- Collects search results with caching support
- Stores raw search data

#### 5.2 Company & Competitor Searches
**Node IDs**:
- `execute_company_google_searches`
- `execute_company_bing_searches`
- `execute_company_perplexity_searches`

**Purpose**: Executes company/competitor queries across search engines

**Process**:
- Runs comparative queries on all three platforms
- Captures competitive positioning data
- Enables cross-platform comparison

### 6. Data Storage
**Node IDs**: `store_raw_blog_coverage_data`, `store_raw_company_comp_data`

**Purpose**: Stores raw search results for analysis and future reference

**Storage Configuration**:
- Blog Coverage Data: `blog_ai_visibility_raw_data_blog_coverage`
- Company Comparison Data: `blog_ai_visibility_raw_data_company_comp`
- Storage Type: Unversioned, upsert operation

### 7. Report Generation

#### 7.1 Blog Coverage Report
**Node ID**: `construct_blog_coverage_report_prompt` → `generate_blog_coverage_report`

**Purpose**: Generates comprehensive blog coverage analysis report

**Process**:
- Analyzes search results from all engines
- Evaluates content visibility and reach
- Provides recommendations for improvement

**Model Configuration**:
- Provider: Anthropic
- Model: claude-sonnet-4-20250514
- Temperature: 0.5
- Max Tokens: 10000

#### 7.2 Company Comparison Report
**Node ID**: `construct_company_comp_report_prompt` → `generate_company_comp_report`

**Purpose**: Generates competitive comparison report

**Process**:
- Compares company visibility against competitors
- Identifies strengths and weaknesses
- Provides strategic recommendations

**Model Configuration**:
- Provider: Anthropic
- Model: claude-sonnet-4-20250514
- Temperature: 0.5
- Max Tokens: 5000

### 8. Final Report Storage
**Node IDs**: `store_blog_coverage_report`, `store_company_comp_report`

**Purpose**: Stores generated reports in customer data

**Storage Details**:
- Blog Coverage Report: `blog_ai_visibility_test`
- Company Comparison Report: `blog_company_ai_visibility_test`
- Format: JSON structured data

### 9. Output Node
**Node ID**: `output_node`

**Purpose**: Consolidates all results and completes workflow

**Output**:
- Company name
- Blog coverage report
- Company comparison report
- Processing status

## Workflow Features

### Caching Support
- Configurable cache usage for search results
- Reduces API calls and improves performance
- Customizable lookback period

### Multi-Engine Analysis
- Parallel search execution across Google, Bing, and Perplexity
- Cross-platform comparison capabilities
- Comprehensive visibility assessment

### Competitive Intelligence
- Automated competitor identification
- Side-by-side visibility comparison
- Market positioning analysis

### Report Generation
- Two distinct report types (coverage and comparison)
- AI-powered insights and recommendations
- Structured output for easy consumption

## Data Flow
1. Input company name and configuration
2. Load company context documents
3. Perform competitive analysis
4. Generate targeted search queries
5. Execute searches across multiple engines
6. Store raw search data
7. Generate analytical reports
8. Store reports and output results

## Error Handling
- Graceful handling of search API failures
- Fallback to cached data when available
- Comprehensive error logging

## Performance Considerations
- Parallel search execution for efficiency
- Batch processing of queries
- Optimized token usage in LLM calls
- Cache utilization to reduce redundant searches