"""
Filter targets configuration for LinkedIn profile and post data filtering.

This defines which fields to keep from the raw LinkedIn scraping results.
Uses a whitelist approach (non_target_fields_mode: "deny") to keep only specified fields.

The filter_data node processes nested data structures and supports dot notation
for accessing nested fields. Each target specifies:
- filter_target: The field path to evaluate (using dot notation for nested access)
- filter_mode: "allow" to keep the field, "deny" to remove it
- condition_groups: Conditions that must be met to keep the field
- group_logical_operator: How to combine condition groups ("and" or "or")

For arrays (like educations, positions, posts), the filter applies to each array element.
When filtering nested fields within arrays, all parent levels are automatically included
if any nested field passes the filter.

Example: If "educations.schoolName" passes, the entire "educations" array and each
education object's structure is preserved, but only fields explicitly allowed are kept.
"""

# Profile fields to keep
PROFILE_FILTER_TARGETS = [
    # Basic profile info
    {"filter_target": "data_to_filter.scraped_profile_job.username", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.username", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.firstName", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.firstName", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.lastName", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.lastName", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.summary", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.summary", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.headline", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.headline", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    
    # Geo fields
    {"filter_target": "data_to_filter.scraped_profile_job.geo", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.geo", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.geo.country", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.geo.country", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.geo.city", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.geo.city", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.geo.full", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.geo.full", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    
    # Education array and nested fields
    {"filter_target": "data_to_filter.scraped_profile_job.educations", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.start", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.start", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.start.year", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.start.year", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.start.month", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.start.month", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.start.day", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.start.day", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.end", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.end", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.end.year", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.end.year", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.end.month", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.end.month", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.end.day", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.end.day", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.fieldOfStudy", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.fieldOfStudy", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.degree", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.degree", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.grade", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.grade", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.schoolName", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.schoolName", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.educations.description", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.educations.description", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    
    # Position array and nested fields
    {"filter_target": "data_to_filter.scraped_profile_job.position", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.position", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.position.companyName", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.position.companyName", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.position.companyIndustry", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.position.companyIndustry", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.position.location", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.position.location", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_profile_job.position.description", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_profile_job.position.description", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
]

# Post fields to keep
POST_FILTER_TARGETS = [
    # Basic post fields
    {"filter_target": "data_to_filter.scraped_posts_job.text", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_posts_job.text", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_posts_job.reposted", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_posts_job.reposted", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_posts_job.postedDate", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_posts_job.postedDate", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_posts_job.postedDateTimestamp", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_posts_job.postedDateTimestamp", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    
    # Engagement metrics
    {"filter_target": "data_to_filter.scraped_posts_job.totalReactionCount", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_posts_job.totalReactionCount", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_posts_job.commentsCount", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_posts_job.commentsCount", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_posts_job.repostsCount", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_posts_job.repostsCount", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_posts_job.contentType", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_posts_job.contentType", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    
    # Reshared post data (NEW - includes nested text field)
    {"filter_target": "data_to_filter.scraped_posts_job.resharedPost", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_posts_job.resharedPost", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
    {"filter_target": "data_to_filter.scraped_posts_job.resharedPost.text", "filter_mode": "allow", 
     "condition_groups": [{"conditions": [{"field": "data_to_filter.scraped_posts_job.resharedPost.text", "operator": "is_not_empty"}], "logical_operator": "and"}], 
     "group_logical_operator": "and"},
]

# Combined list of all filter targets
ALL_FILTER_TARGETS = PROFILE_FILTER_TARGETS + POST_FILTER_TARGETS

