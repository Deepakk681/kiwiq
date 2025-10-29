    # Predefined HITL inputs for testing
hitl_inputs = [
        # First HITL: Request revision
        {
            "user_brief_action": "provide_feedback",
            "revision_feedback": "The brief needs more focus on specific cost categories and should include more concrete examples. Please add a section about hidden costs like opportunity cost of sales reps not selling.",
            "load_additional_user_files": [
                {
                    "namespace": "user_research_files",
                    "docname": "cfo_automation_roi_guide",
                    "is_shared": False
                }
            ],
            "updated_content_brief": {
                "title": "The Hidden Cost of Manual CRM Data Entry: A CFO's Perspective",
                "target_audience": "CFOs and Finance Leaders at Enterprise SaaS companies",
                "content_goal": "Demonstrate financial impact of manual data entry and ROI of automation",
                "key_takeaways": [
                    "Manual CRM data entry costs enterprises $1M+ annually in lost productivity",
                    "Poor data quality leads to 20% revenue leakage",
                    "Automation delivers 10x ROI within 6 months"
                ],
                "content_structure": [
                    {
                        "section": "Introduction",
                        "description": "Hook with shocking statistics about manual data entry costs",
                        "word_count": 200
                    },
                    {
                        "section": "The True Cost Breakdown",
                        "description": "Detailed analysis of direct and indirect costs",
                        "word_count": 600
                    },
                    {
                        "section": "Impact on Revenue Forecasting",
                        "description": "How bad data affects financial planning",
                        "word_count": 500
                    },
                    {
                        "section": "ROI of Automation",
                        "description": "Financial benefits and payback period",
                        "word_count": 400
                    },
                    {
                        "section": "Conclusion",
                        "description": "Call to action for CFOs",
                        "word_count": 300
                    }
                ],
                "seo_keywords": {
                    "primary_keyword": "CRM data entry costs",
                    "secondary_keywords": ["revenue operations ROI", "sales productivity"],
                    "long_tail_keywords": ["manual CRM data entry financial impact"]
                },
                "brand_guidelines": {
                    "tone": "Professional and data-driven",
                    "voice": "Authoritative yet approachable",
                    "style_notes": ["Use financial metrics", "Include case studies"]
                },
                "research_sources": [
                    {
                        "source": "Industry Reports",
                        "key_insights": ["Average cost per manual entry", "Time spent on data entry"]
                    }
                ],
                "call_to_action": "Calculate your CRM data entry costs with our ROI calculator",
                "estimated_word_count": 2000,
                "difficulty_level": "intermediate",
                "writing_instructions": [
                    "Include specific dollar amounts and percentages",
                    "Use CFO-friendly language and metrics",
                    "Add comparison table of manual vs automated costs"
                ]
            }
        },
        # # Second HITL: Save as draft
        {
            "user_brief_action": "draft",
            "load_additional_user_files": [],
            "updated_content_brief": {
                "title": "The Hidden Cost of Manual CRM Data Entry: A CFO's Perspective (Revised)",
                "target_audience": "CFOs and Finance Leaders at Enterprise SaaS companies",
                "content_goal": "Demonstrate comprehensive financial impact of manual data entry including hidden costs and ROI of automation",
                "key_takeaways": [
                    "Manual CRM data entry costs enterprises $1M+ annually in lost productivity",
                    "Hidden opportunity costs from sales reps not selling add another $500K annually",
                    "Poor data quality leads to 20% revenue leakage",
                    "Automation delivers 10x ROI within 6 months"
                ],
                "content_structure": [
                    {
                        "section": "Introduction",
                        "description": "Hook with shocking statistics about manual data entry costs",
                        "word_count": 200
                    },
                    {
                        "section": "Direct Cost Categories",
                        "description": "Salary costs, training costs, and system maintenance",
                        "word_count": 400
                    },
                    {
                        "section": "Hidden Opportunity Costs",
                        "description": "Time sales reps spend on data entry instead of selling",
                        "word_count": 500
                    },
                    {
                        "section": "Data Quality Impact",
                        "description": "How bad data affects financial planning and forecasting accuracy",
                        "word_count": 400
                    },
                    {
                        "section": "ROI of Automation with Examples",
                        "description": "Financial benefits, payback period, and real customer examples",
                        "word_count": 500
                    },
                    {
                        "section": "Conclusion",
                        "description": "Call to action for CFOs with specific next steps",
                        "word_count": 200
                    }
                ],
                "seo_keywords": {
                    "primary_keyword": "CRM data entry costs",
                    "secondary_keywords": ["revenue operations ROI", "sales productivity", "opportunity cost"],
                    "long_tail_keywords": ["manual CRM data entry financial impact", "hidden costs sales data entry"]
                },
                "brand_guidelines": {
                    "tone": "Professional and data-driven",
                    "voice": "Authoritative yet approachable",
                    "style_notes": ["Use financial metrics", "Include case studies", "Add concrete examples"]
                },
                "research_sources": [
                    {
                        "source": "Industry Reports",
                        "key_insights": ["Average cost per manual entry", "Time spent on data entry", "Opportunity cost calculations"]
                    },
                    {
                        "source": "Customer Case Studies",
                        "key_insights": ["Real ROI examples", "Implementation timelines"]
                    }
                ],
                "call_to_action": "Calculate your CRM data entry costs with our ROI calculator and see your potential savings",
                "estimated_word_count": 2200,
                "difficulty_level": "intermediate",
                "writing_instructions": [
                    "Include specific dollar amounts and percentages",
                    "Use CFO-friendly language and metrics",
                    "Add comparison table of manual vs automated costs",
                    "Include at least 2 customer examples with specific ROI numbers",
                    "Add section on opportunity cost calculations"
                ]
            }
        },
        # Third HITL: Request another revision after draft
        {
            "user_brief_action": "provide_feedback",
            "revision_feedback": "The brief looks good but needs a stronger executive summary section and should include more industry-specific examples. Also, please add a section about implementation considerations from a CFO perspective.",
            "load_additional_user_files": [
                {
                    "namespace": "hitl_context_files",
                    "docname": "cfo_implementation_guide",
                    "is_shared": False
                },
                {
                    "namespace": "hitl_context_files",
                    "docname": "industry_case_studies",
                    "is_shared": False
                }
            ],
            "updated_content_brief": {
                "title": "The Hidden Cost of Manual CRM Data Entry: A CFO's Perspective (Draft)",
                "target_audience": "CFOs and Finance Leaders at Enterprise SaaS companies",
                "content_goal": "Demonstrate comprehensive financial impact of manual data entry including hidden costs and ROI of automation",
                "key_takeaways": [
                    "Manual CRM data entry costs enterprises $1M+ annually in lost productivity",
                    "Hidden opportunity costs from sales reps not selling add another $500K annually",
                    "Poor data quality leads to 20% revenue leakage",
                    "Automation delivers 10x ROI within 6 months"
                ],
                "content_structure": [
                    {
                        "section": "Introduction",
                        "description": "Hook with shocking statistics about manual data entry costs",
                        "word_count": 200
                    },
                    {
                        "section": "Direct Cost Categories",
                        "description": "Salary costs, training costs, and system maintenance",
                        "word_count": 400
                    },
                    {
                        "section": "Hidden Opportunity Costs",
                        "description": "Time sales reps spend on data entry instead of selling",
                        "word_count": 500
                    },
                    {
                        "section": "Data Quality Impact",
                        "description": "How bad data affects financial planning and forecasting accuracy",
                        "word_count": 400
                    },
                    {
                        "section": "ROI of Automation with Examples",
                        "description": "Financial benefits, payback period, and real customer examples",
                        "word_count": 500
                    },
                    {
                        "section": "Conclusion",
                        "description": "Call to action for CFOs with specific next steps",
                        "word_count": 200
                    }
                ],
                "seo_keywords": {
                    "primary_keyword": "CRM data entry costs",
                    "secondary_keywords": ["revenue operations ROI", "sales productivity", "opportunity cost"],
                    "long_tail_keywords": ["manual CRM data entry financial impact", "hidden costs sales data entry"]
                },
                "brand_guidelines": {
                    "tone": "Professional and data-driven",
                    "voice": "Authoritative yet approachable",
                    "style_notes": ["Use financial metrics", "Include case studies", "Add concrete examples"]
                },
                "research_sources": [
                    {
                        "source": "Industry Reports",
                        "key_insights": ["Average cost per manual entry", "Time spent on data entry", "Opportunity cost calculations"]
                    },
                    {
                        "source": "Customer Case Studies",
                        "key_insights": ["Real ROI examples", "Implementation timelines"]
                    }
                ],
                "call_to_action": "Calculate your CRM data entry costs with our ROI calculator and see your potential savings",
                "estimated_word_count": 2200,
                "difficulty_level": "intermediate",
                "writing_instructions": [
                    "Include specific dollar amounts and percentages",
                    "Use CFO-friendly language and metrics",
                    "Add comparison table of manual vs automated costs",
                    "Include at least 2 customer examples with specific ROI numbers",
                    "Add section on opportunity cost calculations"
                ]
            }
        },
        # Fourth HITL: Final completion
        {
            "user_brief_action": "complete",
            "load_additional_user_files": [],
            "updated_content_brief": {
                "title": "The Hidden Cost of Manual CRM Data Entry: A CFO's Perspective (Final)",
                "target_audience": "CFOs and Finance Leaders at Enterprise SaaS companies",
                "content_goal": "Demonstrate comprehensive financial impact of manual data entry including hidden costs, industry examples, and ROI of automation with implementation considerations",
                "key_takeaways": [
                    "Manual CRM data entry costs enterprises $1M+ annually in lost productivity",
                    "Hidden opportunity costs from sales reps not selling add another $500K annually",
                    "Poor data quality leads to 20% revenue leakage",
                    "Automation delivers 10x ROI within 6 months with proper implementation"
                ],
                "content_structure": [
                    {
                        "section": "Executive Summary",
                        "description": "Key financial impact overview for busy CFOs",
                        "word_count": 250
                    },
                    {
                        "section": "Introduction",
                        "description": "Hook with shocking statistics about manual data entry costs",
                        "word_count": 200
                    },
                    {
                        "section": "Direct Cost Categories",
                        "description": "Salary costs, training costs, and system maintenance with SaaS examples",
                        "word_count": 400
                    },
                    {
                        "section": "Hidden Opportunity Costs",
                        "description": "Time sales reps spend on data entry instead of selling",
                        "word_count": 500
                    },
                    {
                        "section": "Industry-Specific Impact",
                        "description": "Examples from SaaS, FinTech, and Enterprise software companies",
                        "word_count": 400
                    },
                    {
                        "section": "Data Quality Impact",
                        "description": "How bad data affects financial planning and forecasting accuracy",
                        "word_count": 350
                    },
                    {
                        "section": "ROI of Automation with Examples",
                        "description": "Financial benefits, payback period, and real customer examples",
                        "word_count": 500
                    },
                    {
                        "section": "CFO Implementation Considerations",
                        "description": "Budget planning, change management, and success metrics",
                        "word_count": 400
                    },
                    {
                        "section": "Conclusion",
                        "description": "Call to action for CFOs with specific next steps",
                        "word_count": 200
                    }
                ],
                "seo_keywords": {
                    "primary_keyword": "CRM data entry costs",
                    "secondary_keywords": ["revenue operations ROI", "sales productivity", "opportunity cost", "CFO implementation"],
                    "long_tail_keywords": ["manual CRM data entry financial impact", "hidden costs sales data entry", "SaaS CRM automation ROI"]
                },
                "brand_guidelines": {
                    "tone": "Professional and data-driven",
                    "voice": "Authoritative yet approachable",
                    "style_notes": ["Use financial metrics", "Include case studies", "Add concrete examples", "Focus on CFO concerns"]
                },
                "research_sources": [
                    {
                        "source": "Industry Reports",
                        "key_insights": ["Average cost per manual entry", "Time spent on data entry", "Opportunity cost calculations"]
                    },
                    {
                        "source": "Customer Case Studies",
                        "key_insights": ["Real ROI examples", "Implementation timelines", "Industry-specific results"]
                    },
                    {
                        "source": "CFO Surveys",
                        "key_insights": ["Implementation concerns", "Budget allocation priorities"]
                    }
                ],
                "call_to_action": "Download our CFO's Guide to CRM Automation ROI and calculate your potential savings",
                "estimated_word_count": 3200,
                "difficulty_level": "intermediate",
                "writing_instructions": [
                    "Include specific dollar amounts and percentages",
                    "Use CFO-friendly language and metrics",
                    "Add comparison table of manual vs automated costs",
                    "Include at least 3 customer examples with specific ROI numbers",
                    "Add section on opportunity cost calculations",
                    "Include executive summary for time-pressed CFOs",
                    "Add implementation timeline and budget considerations",
                    "Use industry-specific examples (SaaS, FinTech, Enterprise)"
                ]
            }
        }
    ]