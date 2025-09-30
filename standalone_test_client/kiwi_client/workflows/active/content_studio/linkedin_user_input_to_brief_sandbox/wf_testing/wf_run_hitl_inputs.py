# Predefined HITL inputs
hitl_inputs = [
        # 1) Topic selection: provide feedback once (triggers one regeneration loop)
        {
            "user_action": "provide_feedback",
            "selected_topic_id": None,
            "regeneration_feedback": "These are promising. Please propose options that emphasize remote team connection impact and an executive decision framework for what to automate vs. where human leadership is essential."
        },
        # 2) Topic selection (after regeneration): accept a specific topic
        {
            "user_action": "complete",
            "selected_topic_id": "topic_01",
            "regeneration_feedback": None
        },
        # 3) Brief approval: provide feedback first (allows one revision loop)
        # {
        #     "user_brief_action": "provide_feedback",
        #     "revision_feedback": "Tighten the hook and add one concrete remote-team scenario. Keep the 80/20 framing, but make success metrics more specific.",
        #     "updated_content_brief": {
        #         "content_brief": {
        #             "title": "The 80/20 Rule of AI in Project Management",
        #             "content_type": "LinkedIn Post",
        #             "content_format": "Thought leadership with practical framework",
        #             "target_audience": "Operations Managers and Project Managers at 50-500 employee tech companies",
        #             "content_goal": "Educate executives on where to apply AI vs. retain human leadership in PM",
        #             "key_message": "Use AI for high-leverage, repetitive PM tasks and preserve human judgment for people, priorities, and context.",
        #             "content_structure": [
        #                 {
        #                     "section_title": "Hook & Context",
        #                     "key_points": [
        #                         "Executives wrestle with what to automate vs. what needs human leadership",
        #                         "A simple 80/20 model clarifies where AI delivers outsized leverage"
        #                     ],
        #                     "estimated_word_count": 60
        #                 },
        #                 {
        #                     "section_title": "80/20 Framework",
        #                     "key_points": [
        #                         "Automate: status reporting, basic risk flags, capacity snapshots, meeting notes",
        #                         "Keep Human: prioritization trade-offs, stakeholder alignment, coaching, escalation calls"
        #                     ],
        #                     "estimated_word_count": 140
        #                 },
        #                 {
        #                     "section_title": "Examples & Tools",
        #                     "key_points": [
        #                         "Real examples of AI assisting remote teams without reducing connection",
        #                         "Tool patterns that augment—not replace—relationships"
        #                     ],
        #                     "estimated_word_count": 120
        #                 },
        #                 {
        #                     "section_title": "Implementation Tips",
        #                     "key_points": [
        #                         "Start with low-risk automations and expand",
        #                         "Define decision guardrails and human-in-the-loop checkpoints"
        #                     ],
        #                     "estimated_word_count": 120
        #                 },
        #                 {
        #                     "section_title": "CTA",
        #                     "key_points": [
        #                         "Invite readers to share their biggest AI adoption challenge",
        #                         "Offer a checklist to assess AI readiness"
        #                     ],
        #                     "estimated_word_count": 60
        #                 }
        #             ],
        #             "seo_keywords": [
        #                 "AI in project management",
        #                 "human-in-the-loop",
        #                 "remote teams",
        #                 "automation best practices"
        #             ],
        #             "call_to_action": "Comment your top AI adoption challenge and get the AI readiness checklist.",
        #             "success_metrics": "Engagement rate, saves, qualified inbound conversations, and 2 exec follow-up calls",
        #             "estimated_total_word_count": 500,
        #             "difficulty_level": "Intermediate",
        #             "writing_guidelines": [
        #                 "Conversational yet authoritative tone",
        #                 "Data-informed with practical examples",
        #                 "Emphasize augmentation over replacement"
        #             ],
        #             "knowledge_base_sources": [
        #                 "Internal implementation notes",
        #                 "Public case studies on AI-assisted PM",
        #                 "Vendor documentation for summarization and risk flagging tools"
        #             ]
        #         }
        #     }
        # },
        # # 4) Brief approval: save as draft (avoid hitting iteration limits)
        # {
        #     "user_brief_action": "draft",
        #     "revision_feedback": None,
        #     "updated_content_brief": {
        #         "content_brief": {
        #             "title": "The 80/20 Rule of AI in Project Management",
        #             "content_type": "LinkedIn Post",
        #             "content_format": "Thought leadership with practical framework",
        #             "target_audience": "Operations Managers and Project Managers at 50-500 employee tech companies",
        #             "content_goal": "Educate executives on where to apply AI vs. retain human leadership in PM",
        #             "key_message": "Use AI for high-leverage, repetitive PM tasks and preserve human judgment for people, priorities, and context.",
        #             "content_structure": [
        #                 {
        #                     "section_title": "Hook & Context",
        #                     "key_points": [
        #                         "Executives wrestle with what to automate vs. what needs human leadership",
        #                         "A simple 80/20 model clarifies where AI delivers outsized leverage"
        #                     ],
        #                     "estimated_word_count": 60
        #                 },
        #                 {
        #                     "section_title": "80/20 Framework",
        #                     "key_points": [
        #                         "Automate: status reporting, basic risk flags, capacity snapshots, meeting notes",
        #                         "Keep Human: prioritization trade-offs, stakeholder alignment, coaching, escalation calls"
        #                     ],
        #                     "estimated_word_count": 140
        #                 },
        #                 {
        #                     "section_title": "Examples & Tools",
        #                     "key_points": [
        #                         "Real examples of AI assisting remote teams without reducing connection",
        #                         "Tool patterns that augment—not replace—relationships"
        #                     ],
        #                     "estimated_word_count": 120
        #                 },
        #                 {
        #                     "section_title": "Implementation Tips",
        #                     "key_points": [
        #                         "Start with low-risk automations and expand",
        #                         "Define decision guardrails and human-in-the-loop checkpoints"
        #                     ],
        #                     "estimated_word_count": 120
        #                 },
        #                 {
        #                     "section_title": "CTA",
        #                     "key_points": [
        #                         "Invite readers to share their biggest AI adoption challenge",
        #                         "Offer a checklist to assess AI readiness"
        #                     ],
        #                     "estimated_word_count": 60
        #                 }
        #             ],
        #             "seo_keywords": [
        #                 "AI in project management",
        #                 "human-in-the-loop",
        #                 "remote teams",
        #                 "automation best practices"
        #             ],
        #             "call_to_action": "Comment your top AI adoption challenge and get the AI readiness checklist.",
        #             "success_metrics": "Engagement rate, saves, and qualified inbound conversations",
        #             "estimated_total_word_count": 500,
        #             "difficulty_level": "Intermediate",
        #             "writing_guidelines": [
        #                 "Conversational yet authoritative tone",
        #                 "Data-informed with practical examples",
        #                 "Emphasize augmentation over replacement"
        #             ],
        #             "knowledge_base_sources": [
        #                 "Internal implementation notes",
        #                 "Public case studies on AI-assisted PM",
        #                 "Vendor documentation for summarization and risk flagging tools"
        #             ]
        #         }
        #     }
        # },
        # # 5) Brief approval: provide feedback again, then proceed to save in next step
        # {
        #     "user_brief_action": "provide_feedback",
        #     "revision_feedback": "Looks good. Please make the CTA more outcome-oriented and add one metric example (e.g., 20% faster status reporting).",
        #     "updated_content_brief": {
        #         "content_brief": {
        #             "title": "The 80/20 Rule of AI in Project Management",
        #             "content_type": "LinkedIn Post",
        #             "content_format": "Thought leadership with practical framework",
        #             "target_audience": "Operations Managers and Project Managers at 50-500 employee tech companies",
        #             "content_goal": "Educate executives on where to apply AI vs. retain human leadership in PM",
        #             "key_message": "Use AI for high-leverage, repetitive PM tasks and preserve human judgment for people, priorities, and context.",
        #             "content_structure": [
        #                 {
        #                     "section_title": "Hook & Context",
        #                     "key_points": [
        #                         "Executives wrestle with what to automate vs. what needs human leadership",
        #                         "A simple 80/20 model clarifies where AI delivers outsized leverage"
        #                     ],
        #                     "estimated_word_count": 60
        #                 },
        #                 {
        #                     "section_title": "80/20 Framework",
        #                     "key_points": [
        #                         "Automate: status reporting, basic risk flags, capacity snapshots, meeting notes",
        #                         "Keep Human: prioritization trade-offs, stakeholder alignment, coaching, escalation calls"
        #                     ],
        #                     "estimated_word_count": 140
        #                 },
        #                 {
        #                     "section_title": "Examples & Tools",
        #                     "key_points": [
        #                         "Real examples of AI assisting remote teams without reducing connection",
        #                         "Tool patterns that augment—not replace—relationships"
        #                     ],
        #                     "estimated_word_count": 120
        #                 },
        #                 {
        #                     "section_title": "Implementation Tips",
        #                     "key_points": [
        #                         "Start with low-risk automations and expand",
        #                         "Define decision guardrails and human-in-the-loop checkpoints"
        #                     ],
        #                     "estimated_word_count": 120
        #                 },
        #                 {
        #                     "section_title": "CTA",
        #                     "key_points": [
        #                         "Invite readers to share their biggest AI adoption challenge",
        #                         "Offer a checklist to assess AI readiness"
        #                     ],
        #                     "estimated_word_count": 60
        #                 }
        #             ],
        #             "seo_keywords": [
        #                 "AI in project management",
        #                 "human-in-the-loop",
        #                 "remote teams",
        #                 "automation best practices"
        #             ],
        #             "call_to_action": "Comment your top AI adoption challenge and get the AI readiness checklist.",
        #             "success_metrics": "Engagement rate, saves, qualified inbound conversations, and 2 exec follow-up calls",
        #             "estimated_total_word_count": 500,
        #             "difficulty_level": "Intermediate",
        #             "writing_guidelines": [
        #                 "Conversational yet authoritative tone",
        #                 "Data-informed with practical examples",
        #                 "Emphasize augmentation over replacement"
        #             ],
        #             "knowledge_base_sources": [
        #                 "Internal implementation notes",
        #                 "Public case studies on AI-assisted PM",
        #                 "Vendor documentation for summarization and risk flagging tools"
        #             ]
        #         }
        #     }
        # },
        # 6) Brief approval: complete (save final)
        {
            "user_brief_action": "cancel_workflow",
            "revision_feedback": None,
            "updated_content_brief": {
                "content_brief": {
                    "title": "The 80/20 Rule of AI in Project Management",
                    "content_type": "LinkedIn Post",
                    "content_format": "Thought leadership with practical framework",
                    "target_audience": "Operations Managers and Project Managers at 50-500 employee tech companies",
                    "content_goal": "Educate executives on where to apply AI vs. retain human leadership in PM",
                    "key_message": "Use AI for high-leverage, repetitive PM tasks and preserve human judgment for people, priorities, and context.",
                    "content_structure": [
                        {
                            "section_title": "Hook & Context",
                            "key_points": [
                                "Executives wrestle with what to automate vs. what needs human leadership",
                                "A simple 80/20 model clarifies where AI delivers outsized leverage"
                            ],
                            "estimated_word_count": 60
                        },
                        {
                            "section_title": "80/20 Framework",
                            "key_points": [
                                "Automate: status reporting, basic risk flags, capacity snapshots, meeting notes",
                                "Keep Human: prioritization trade-offs, stakeholder alignment, coaching, escalation calls"
                            ],
                            "estimated_word_count": 140
                        },
                        {
                            "section_title": "Examples & Tools",
                            "key_points": [
                                "Real examples of AI assisting remote teams without reducing connection",
                                "Tool patterns that augment—not replace—relationships"
                            ],
                            "estimated_word_count": 120
                        },
                        {
                            "section_title": "Implementation Tips",
                            "key_points": [
                                "Start with low-risk automations and expand",
                                "Define decision guardrails and human-in-the-loop checkpoints"
                            ],
                            "estimated_word_count": 120
                        },
                        {
                            "section_title": "CTA",
                            "key_points": [
                                "Invite readers to share their biggest AI adoption challenge",
                                "Offer a checklist to assess AI readiness"
                            ],
                            "estimated_word_count": 60
                        }
                    ],
                    "seo_keywords": [
                        "AI in project management",
                        "human-in-the-loop",
                        "remote teams",
                        "automation best practices"
                    ],
                    "call_to_action": "Comment your top AI adoption challenge and get the AI readiness checklist.",
                    "success_metrics": "Engagement rate, saves, and qualified inbound conversations",
                    "estimated_total_word_count": 500,
                    "difficulty_level": "Intermediate",
                    "writing_guidelines": [
                        "Conversational yet authoritative tone",
                        "Data-informed with practical examples",
                        "Emphasize augmentation over replacement"
                    ],
                    "knowledge_base_sources": [
                        "Internal implementation notes",
                        "Public case studies on AI-assisted PM",
                        "Vendor documentation for summarization and risk flagging tools"
                    ]
                }
            }
        }
    ]