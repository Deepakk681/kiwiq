
# Default document patterns for ingestion
# These patterns target the most important document types for RAG
DEFAULT_INGESTION_DOCUMENT_PATTERNS = [
    
    # # Uploaded files (empty docname template, so match all)
    # ("uploaded_files_*", "*"),
    
    # LinkedIn executive strategy and analysis documents
    ("linkedin_executive_strategy_*", "*"),
    ("linkedin_content_diagnostic_*", "*"),
    ("linkedin_knowledge_base_*", "*"),
    ("linkedin_uploaded_files_*", "*"),
    ("linkedin_executive_profile_namespace_*", "*"),
    ("linkedin_executive_analysis_*", "*"),
    
    # LinkedIn scraping results (updated patterns)
    ("linkedin_scraping_results_*", "*"),
    
    # LinkedIn content creation documents
    ("linkedin_content_briefs_*", "*"),
    ("linkedin_post_drafts_*", "*"),
    ("linkedin_content_ideas_*", "*"),
    
    # Blog company and strategy documents
    ("blog_company_profile_*", "*"),
    ("blog_company_strategy_*", "*"),
    ("blog_content_data_*", "*"),
    
    
    # Blog analysis documents
    ("blog_analysis_*", "*"),
    
    # Blog content diagnostic documents
    ("blog_content_diagnostic_*", "*"),
    # ("blog_content_diagnostic_report_*", "blog_content_diagnostic_report_doc"),
    
    # Blog AI query tracking documents
    ("blog_ai_query_tracking_*", "*"),
    
    # Blog content creation and delivery documents
    ("blog_spark_delivery_*", "*"),
    ("blog_ideas_namespace_*", "*"),
    ("blog_brief_namespace_*", "*"),
    ("blog_posts_draft_namespace_*", "blog_post_draft_*"),
    
    # External research and document summary reports
    ("external_research_reports_*", "*"),
    
    # System strategy documents (important for RAG context)
    ("blog_playbook_sys", "*"),
    ("blog_uploaded_files_*", "*"),
]