# Company Onboarding Process

entity_username = example-user-2-1a4b25172
company_name = gumloop

## Step 1: Create an account using Retool

**URL:** https://kiwiqai.retool.com/editor/fca4075a-4d9a-11f0-9220-033fd74d0ff9/Organization%20Dashboard/create_new_user_v2

**Important:** Refresh token at top right corner before starting the creation of account

## Step 2: Add recharge to the account

**URL:** https://kiwiqai.retool.com/editor/fca4075a-4d9a-11f0-9220-033fd74d0ff9/Organization%20Dashboard/create_promo_code_team_client

**Options:**
- For team
- For demo
- For client

## Step 3: Creating the company and profile docs

### LinkedIn
- Docname: `linkedin_executive_profile_doc`
- Namespace: `linkedin_executive_profile_namespace_{item}`
- is_versioned = true

### Blog
- Docname: `blog_company_doc`
- Namespace: `blog_company_profile_{item}`
- is_versioned = true

## Step 4: Running diagnostics workflow

### LinkedIn
- Docname: `linkedin_content_diagnostic_report_doc`
- Namespace: `linkedin_content_diagnostic_{item}`
- is_versioned = false

### Blog
- Docname: `blog_content_diagnostic_report_doc`
- Namespace: `blog_content_diagnostic_report_{item}`
- is_versioned = false

## Step 5: Creating playbook documents

### LinkedIn
- Docname: `linkedin_content_playbook_doc`
- Namespace: `linkedin_executive_strategy_{item}`
- is_versioned = true

### Blog
- Docname: `blog_content_playbook_doc`
- Namespace: `blog_company_strategy_{item}`
- is_versioned = true
