# Company Analysis Workflow

## Overview
This workflow performs comprehensive company analysis by combining internal document intelligence with market research. It analyzes internal company documents to extract business intelligence, conducts Reddit and market research to understand customer needs and opportunities, and generates strategic content pillars that align business goals with market demand. The workflow adapts based on whether the company has sufficient existing content or needs foundational research.

## Frontend User Flow
*To be documented later*

## File Locations
- **Workflow File**: `/standalone_client/kiwi_client/workflows/active/content_diagnostics/wf_company_analysis_workflow.py`
- **LLM Inputs**: `/standalone_client/kiwi_client/workflows/active/content_diagnostics/llm_inputs/company_analysis.py`

## Key Components

### 1. Input Node
**Node ID**: `input_node`

**Purpose**: Entry point for the workflow that accepts company information and scraped data

**Input Requirements**:
- `company_name`: Name of the company to analyze (required)
- `scraped_data`: Web scraped data from the company's website (required)
- `has_insufficient_blog_and_page_count`: Boolean flag indicating content sufficiency (required)

### 2. Document Loading Phase

#### 2.1 Load Company Documents
**Node ID**: `load_company_documents`

**Purpose**: Loads all internal company documents from uploaded files

**Configuration**:
- Namespace Pattern: `blog_uploaded_files_{company_name}`
- Maximum Documents: 200
- Loads user-specific documents only
- Returns as `company_documents`

#### 2.2 Load Company Context
**Node ID**: `load_company_context`

**Purpose**: Loads company goals and context document

**Configuration**:
- Document Name: `blog_company_doc`
- Namespace Pattern: `blog_company_{company_name}`
- Returns as `company_context`

### 3. Conditional Routing
**Node ID**: `route_based_on_content`

**Purpose**: Routes workflow based on content sufficiency

**Routing Logic**:
- **Insufficient Content Path**: Goes to Perplexity research → Document analysis
- **Sufficient Content Path**: Goes directly to document analysis
- Based on `has_insufficient_blog_and_page_count` flag

### 4. Path A: Insufficient Content (Perplexity Research First)

#### 4.1 Perplexity Company Research
**Node ID**: `construct_perplexity_research_prompt` → `perplexity_company_research`

**Purpose**: Conducts foundational company research when insufficient content exists

**Process**:
- Generates comprehensive company research using Perplexity
- Gathers public information about the company
- Creates foundational understanding

**Model Configuration**:
- Provider: Perplexity
- Model: sonar
- Temperature: 0.3
- Max Tokens: 6000

### 5. Document Analysis Phase

#### 5.1 Document Batching
**Node ID**: `batch_documents`

**Purpose**: Batches documents for efficient processing

**Configuration**:
- Batch Size: 5 documents per batch
- Routes to document analysis nodes

#### 5.2 Document Analysis
**Node ID**: `construct_doc_analysis_prompt` → `analyze_document_batch`

**Purpose**: Analyzes batched documents to extract company intelligence

**Process**:
- Processes each batch of documents
- Extracts key business information
- Identifies products, services, and capabilities

**Model Configuration**:
- Provider: OpenAI
- Model: gpt-5
- Temperature: 0.5
- Max Tokens: 12000

### 6. Synthesis Phase

#### 6.1 Unique Report Generation
**Node ID**: `construct_unique_report_prompt` → `generate_unique_report`

**Purpose**: Synthesizes all analyses into comprehensive company report

**Process**:
- Combines insights from all document batches
- Includes Perplexity research (if available)
- Creates unified company intelligence report

**Model Configuration**:
- Provider: OpenAI
- Model: gpt-5
- Temperature: 0.5
- Max Tokens: 12000

### 7. Reddit Market Research Phase

#### 7.1 Reddit Query Generation
**Node ID**: `construct_reddit_query_prompt` → `generate_reddit_queries`

**Purpose**: Generates targeted Reddit search queries

**Process**:
- Creates queries based on company analysis
- Targets relevant subreddits and topics
- Focuses on market needs and pain points

**Model Configuration**:
- Provider: OpenAI
- Model: gpt-5
- Temperature: 0.5
- Max Tokens: 12000

#### 7.2 Reddit Search Execution
**Node ID**: `execute_reddit_searches`

**Purpose**: Executes Reddit searches using Perplexity

**Process**:
- Runs generated queries on Reddit
- Collects community discussions and insights
- Gathers market sentiment data

**Configuration**:
- Uses Perplexity for Reddit search
- Collects multiple search results per query

#### 7.3 Reddit Insights Synthesis
**Node ID**: `construct_reddit_research_prompt` → `synthesize_reddit_insights`

**Purpose**: Synthesizes Reddit research into market intelligence

**Process**:
- Analyzes Reddit discussions
- Extracts market needs and opportunities
- Identifies demand indicators

**Model Configuration**:
- Provider: OpenAI
- Model: gpt-5
- Temperature: 0.5
- Max Tokens: 12000

### 8. Final Analysis & Content Pillars

#### 8.1 Strategic Content Pillars Generation
**Node ID**: `construct_final_insights_prompt` → `generate_final_insights`

**Purpose**: Creates strategic content pillars aligned with business and market

**Process**:
- Merges company strengths with market needs
- Generates actionable content strategies
- Provides demand-driven recommendations

**Model Configuration**:
- Provider: OpenAI
- Model: gpt-5
- Temperature: 0.5
- Max Tokens: 12000

### 9. Data Storage
**Node ID**: `store_company_analysis`

**Purpose**: Stores comprehensive analysis results

**Storage Configuration**:
- Document Name: `blog_company_analysis`
- Namespace Pattern: `blog_company_analysis_{company_name}`
- Storage Type: Unversioned, upsert operation

### 10. Output Node
**Node ID**: `output_node`

**Purpose**: Returns workflow results

**Output**:
- Company name
- Comprehensive company analysis
- Market insights with demand indicators
- Strategic content pillars

## Workflow Features

### Adaptive Processing
- Conditional routing based on content availability
- Optimized paths for different scenarios
- Efficient resource utilization

### Multi-Source Intelligence
- Internal document analysis
- External market research via Reddit
- Public company information via Perplexity

### Batch Processing
- Efficient document batching
- Parallel processing capabilities
- Scalable to large document sets

### Market Alignment
- Reddit community insights
- Demand indicator identification
- Strategic content recommendations

## Data Flow

### Path 1: Insufficient Content
1. Input → Load documents → Route to Perplexity
2. Perplexity research → Document batching
3. Document analysis → Unique report
4. Reddit query generation → Reddit searches
5. Reddit synthesis → Final insights
6. Store results → Output

### Path 2: Sufficient Content
1. Input → Load documents → Route to analysis
2. Document batching → Document analysis
3. Unique report → Reddit query generation
4. Reddit searches → Reddit synthesis
5. Final insights → Store results → Output

## Key Insights Generated

### Company Analysis
- Products and services overview
- Core capabilities and strengths
- Target markets and positioning
- Competitive advantages

### Market Intelligence
- Customer pain points from Reddit
- Market demand indicators
- Competitor discussions
- Emerging trends and opportunities

### Strategic Content Pillars
- Content themes aligned with market needs
- Demand-driven topic recommendations
- Competitive positioning strategies
- Growth opportunity areas

## Performance Considerations
- Batch processing for efficiency
- Conditional routing to optimize processing
- Parallel document analysis
- Cached search results when available
- Token optimization in LLM calls