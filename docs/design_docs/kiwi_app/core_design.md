########################################################################################################################################################

Pending Tasks:

- DB layer
- Auth, user/orgs, oauth; secure AUTH + CSRF!!! User roles --> assign same user roles in multiple orgs!
- workflow service / registry DB layer; potential migration conflicts?
- Worklfow Ops; how to pend / pause workflow and store in DB
- Admins, perms
- backend API; integrate auto API documentation
- notifications, websockets
- notifications of job completion, job triggered/started, job progress live events, tokens streaming, job failure, HITL notification / request!
- HITL jobs table
- user sends back HITL job done!
- Key nodes / workflows with application context / external service context!
    - Embeddings + RAG + Retrieval + hybrid retrieval + llamaindex
- prefect setup!
- linkedin integrations
- billing and payments??
- scraping integrations!!??
- Deployment! External services packages / deployment! hosted vs managed!
- security brainstorming: https://claude.ai/chat/b553f08f-fd40-490c-8504-5f98318ded7c

- Scheduling?
- Triggers?
    - web hooks

########################################################################################################################################################


# DB Layer

Key Entities:
1. User (unique_name / ID > 1 char, * not allowed in name/ID)
2. Organization (unique_name / ID > 1 char, * not allowed in name/ID)
3. user roles
    - org permissions
    - user account permissions (another user controlling someone else's account)
    - Roles:
        - admin: has all permissions
        - 
    - permissions: TODO:
        - full access
        - workflow builder
        - workflow executor + scheduler
        - workflow delete access
        - data access: read + delete
        - billing

Auth data
- API tokens and sessions!
- Oauth data, eg: linkedin

#############################################################################


NOTE: Node Instance, Workflow, prompt template, schema template -> they can be owned by orgs!

Workflow entities: ()
1. Node Template
    - (type: template) (no owner) launch_status/ENV: prod, etc (They never have owners, owned by KIWIQ!)
2. Workflow (They don't have templates since they are fully defined via configs!)
owner org + pointers to parent_templates -> parent workflow copied and each node config will point to a node template (via node name / version)

NOTE: the below can either be in Postgres or Mongo -- stored under customer / namespaces!
Registry manages the details!
3. Prompt Template
4. Schema Template -- Json schema or Construct dynamic schema config or stored in code and just registered!


Runs
- Run ID!
- Thread ID! -> reusable for other Runs, can be potentially same as Run ID!
- Run state / status (A unique Instance)
- Run stream
- results!
- node execution order; events / streams / tokens
- each node execution order, potentially inputs?? (maybe later) or atleast outputs!
- the execution state is persisted and appears even when page is refreshed with fresh incoming notifications!
NOTE: can have diff collections / databases exclusive to KIWIQ, or Langgraph runs states!


Application Workflows + States
- These are workflows owned by Admin / KiwiQ which are run for diff users; 
    - Same instances run for diff users in diff runs
    - can access kiwiq namespace for our docs / prompts etc!
- orchestration between core workflow journeys
- User State


User Notifications
- workflow results / run finished -> with link to results!
User Jobs (HITL)


Data
- Data scopes: shared with org, private to user, public data! 
    {org/shared; org/user_id; shared/ file paths!} May include KiwiQ default data for customers in path too here!
    BTW kiwiq data (like eg content ideas!) won't be public, but it will be owned by default KIWIQ org and shared across org and leverages by users belonging to this system org!
NOTE: can have diff collections / databases exclusive to KIWIQ, or Langgraph runs states!

- User State + journey orchestration; user flow!
- User Data
- workflow data; responses, etc

Entities


PLans + Subscriptions
    - Tiers + Rate Limits + usage limits
Billing + Payments
Usage


[IN FUTURE] Workflow Builder Workspaces





###### DEPRECATED 
####### Instances (Owned by users / orgs AND RUNNABLE!)
####### - Node Instance: (type: instance) config copy + owner org + parent_template: (basically all the config part of the workflow belonging to a specific Node!)
####### - Workflow (same as above!) They have a parent pointer + owner --> will be fully configured



