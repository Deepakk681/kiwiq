# Predefined HITL inputs for comprehensive testing
# Note: This workflow currently doesn't have HITL nodes, but these inputs would be suitable
# if HITL interactions were added for topic review and approval at key decision points
hitl_inputs = [
    # 1) Theme Approval - After theme suggestion generation
    {
        "user_action": "approve_theme",
        "theme_feedback": "Great theme selection! This aligns perfectly with our content strategy pillars. Please proceed with generating topics around enterprise automation insights.",
        "approved_theme_id": "theme_01",
        "modifications": []
    },
    # 2) Research Insights Review - After research completion
    {
        "user_action": "approve_research",
        "research_feedback": "Excellent research insights from Reddit and industry discussions. The pain points identified will help create very targeted content.",
        "additional_research_requests": [],
        "approved_insights": True
    },
    # 3) Topic Suggestions Review - First iteration: provide feedback
    {
        "user_action": "provide_feedback",
        "topic_feedback": "These topic suggestions are solid, but I'd like to see more emphasis on ROI metrics and specific implementation timelines. Also, can we add topics about change management during ERP rollouts?",
        "selected_topic_ids": [],
        "regenerate_topics": True
    },
    # 4) Topic Suggestions Review - Second iteration: approve topics
    {
        "user_action": "approve_topics", 
        "topic_feedback": "Perfect! These revised topics address our audience's key concerns and provide actionable insights. The mix of strategic and tactical content is excellent.",
        "selected_topic_ids": ["topic_01", "topic_02", "topic_03", "topic_04"],
        "regenerate_topics": False
    },
    # 5) Final Calendar Review - Approve the complete calendar before storage
    {
        "user_action": "approve_calendar",
        "calendar_feedback": "Excellent topic calendar! The scheduling and theme distribution across the weeks looks great. Ready to publish.",
        "schedule_modifications": [],
        "final_approval": True
    }
]