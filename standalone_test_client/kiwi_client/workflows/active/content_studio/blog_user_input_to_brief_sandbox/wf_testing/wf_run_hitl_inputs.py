hitl_inputs = [
        # Topic Selection HITL - with additional context files
        {
            "user_action": "provide_feedback",
            "selected_topic_id": None,
            "revision_feedback": "Promising directions. Emphasize remote-team collaboration impacts and an exec framework for what to automate vs. where human leadership is essential.",
            "load_additional_user_files": [
                {
                    "namespace": "topic_context_files",
                    "docname": "executive_ai_framework_guide",
                    "is_shared": False
                },
                {
                    "namespace": "topic_context_files",
                    "docname": "remote_leadership_best_practices",
                    "is_shared": False
                }
            ]
        },
        {
            "user_action": "complete",
            "selected_topic_id": "topic_01",
            "revision_feedback": None,
            "load_additional_user_files": []
        },
        # Brief Approval HITL - with additional context files
        {
            "user_brief_action": "provide_feedback",
            "revision_feedback": "Please tighten the hook and add one concrete scenario. Keep the framework but make success metrics more specific.",
            "load_additional_user_files": [
                {
                    "namespace": "brief_context_files",
                    "docname": "success_metrics_examples",
                    "is_shared": False
                },
                {
                    "namespace": "brief_context_files",
                    "docname": "concrete_scenario_templates",
                    "is_shared": False
                }
            ],
            "updated_content_brief": {
                "content_brief": {
                    "title": "AI and Human Balance in Project Management: An 80/20 Framework",
                    "target_audience": "Project managers at 50-500 employee tech companies",
                    "content_goal": "Clarify what to automate vs. what requires human leadership",
                    "key_takeaways": [
                        "Automate repetitive PM tasks",
                        "Preserve human judgment for priorities and stakeholder alignment"
                    ],
                    "content_structure": [
                        {"section": "Hook & Context", "word_count": 80, "description": "Execs struggle with where to apply AI; introduce 80/20."},
                        {"section": "80/20 Framework", "word_count": 200, "description": "Automate vs. Keep Human table with examples."},
                        {"section": "Remote Team Scenario", "word_count": 200, "description": "Concrete example with metrics."},
                        {"section": "Implementation Tips", "word_count": 180, "description": "Guardrails and checkpoints."},
                        {"section": "CTA", "word_count": 60, "description": "Invite engagement and next steps."}
                    ],
                    "seo_keywords": {"primary_keyword": "AI in project management", "secondary_keywords": ["human-in-the-loop", "remote teams"]},
                    "call_to_action": "Comment your top AI adoption challenge and get a readiness checklist.",
                    "estimated_word_count": 700,
                    "difficulty_level": "Intermediate",
                    "writing_instructions": ["Conversational yet authoritative", "Data-informed with practical examples"]
                }
            }
        },
        {
            "user_brief_action": "draft",
            "revision_feedback": None,
            "load_additional_user_files": [],
            "updated_content_brief": {
                "content_brief": {
                    "title": "AI and Human Balance in Project Management: An 80/20 Framework (Draft V2)",
                    "estimated_word_count": 750
                }
            }
        },
        {
            "user_brief_action": "provide_feedback",
            "revision_feedback": "Looks good—make the CTA more outcome-oriented and add a metric example (e.g., 20% faster status reporting).",
            "load_additional_user_files": [
                {
                    "namespace": "brief_context_files",
                    "docname": "cta_optimization_examples",
                    "is_shared": False
                }
            ],
            "updated_content_brief": {
                "content_brief": {
                    "title": "AI and Human Balance in Project Management: An 80/20 Framework",
                    "call_to_action": "Download the AI readiness checklist and benchmark your current process.",
                    "writing_instructions": ["Add metric example in Remote Team Scenario"]
                }
            }
        },
        {
            "user_brief_action": "complete",
            "revision_feedback": None,
            "load_additional_user_files": [],
            "updated_content_brief": {
                "content_brief": {
                    "title": "AI and Human Balance in Project Management: An 80/20 Framework (Final)",
                    "estimated_word_count": 800
                }
            }
        }
    ]