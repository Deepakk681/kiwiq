
# Workflows

## Add node to workflow (best to iteratively add nodes to a workflow ensuring valid flow??)

add Linkedin scraping node which fetches a user profile given their username fetched from the input field and passes to initial prompt constructor to generate a personalized linkedin post referencing the linkedin profile of the user ; modify prompts and how prompt is consturcted and create appropriate edges input -> scraping node -> prompt constructor; toggle fan in in prompt constructor by setting enable_node_fan_in=True in node_config (not nested node_config)
Also store the fetched user profile to central state
@post_creation_workflow.py 
@linkedin_scraping_node_guide.md 
@job_config_schema.py 


## Plan
Create a detailed plan including a detailed mermaid diagram to build a workflow using the appropriate nodes available given the workflow PRD; translate requirements in our available nodes and config schema only and suggest caveats / watchouts as required; add placeholders (eg: for loading or storing specific data and config needed for it -- i.e. name/version etc), user inputs, user HITL etc as required for the right kinds of inputs to the graph.
Add each node config in detail as required

All nodes registered here are available:
@db_node_register.py 

Guide file for node specific guides:
@core_dynamic_nodes_guide.md 
@data_join_node_guide.md 
@llm_node_guide.md 
@hitl_node_guide.md 
@filter_node_guide.md 
@if_else_node_guide.md 
@transform_node_guide.md 
@load_customer_data_node_guide.md 
@store_customer_data_node_guide.md 
@prompt_constructor_node_guide.md 
@dynamic_router_node_guide.md 
@map_list_router_node_guide.md 

Guide for nodes interplay and building workflows
@nodes_interplay_guide.md 
@workflow_building_guide.md 


/# PRD
...


## Corrections

There are a lot of hallucinations, incorrect configs and improper graph structure in the workflow plan; correct it using the appropriate context provided and ensure full correct graph config is written with available options and each node config is correctly setup with available options , not non-existing ones and edges are properly configured.

Output full configs, don't miss anything or write placeholders (eg: existing code, or keep as is etc).


## Config
Write in code with placeholders? placeholders can be filled up with the various docs etc!



# Guides

## Nodes Guides

Write a usage guide in directory [guides] @guides to understand and use each of the nodes available below
include everything needed to configure and include a node in a workflow graph schema and make it easy to read and use as guide for people not familar with the codebase and just need to build workflows using the documentation and creating node configs to include in their own workflows.

This should also be readable by product teams or non-coders to understand and configure the node for their workflows.

All nodes registered here are available:
@db_node_register.py 

Code for Nodes available to us:
@flow_nodes.py 
@customer_data.py 
@map_list_router_node.py
@transform_node.py 

@dynamic_nodes
@router_node.py 
@llm_node
@prompt

Test file for nodes for reference usage:
@test_customer_data_nodes.py 
@test_transform_node.py 


For context, we will use Graph schema to construct the grpah schema to define the workflow graph @graph.py; eg: @test_AI_loop.py 

Eg guide for if else node @if_else_node_guide.md 


## Nodes interplay guides


WRite guide on how to make nodes work with each other i.e. node interplay as part of a owrkflow, taking care of dynamic schemas, tips and guide etc on integrating nodes with each other as part of an overall workflow


Include everything needed to configure and include nodes in a workflow graph schema and make it easy to read and use as guide for people not familar with the codebase and just need to build workflows using the documentation and creating node configs to include in their own workflows.

This should also be readable by product teams or non-coders to understand and configure the node for their workflows.

All nodes registered here are available:
@db_node_register.py 

Guide file for node specific guides:
@core_dynamic_nodes_guide.md 
@data_join_node_guide.md 
@llm_node_guide.md 
@hitl_node_guide.md 
@filter_node_guide.md 
@if_else_node_guide.md 
@transform_node_guide.md 
@load_customer_data_node_guide.md 
@store_customer_data_node_guide.md 
@prompt_constructor_node_guide.md 
@dynamic_router_node_guide.md 
@map_list_router_node_guide.md 


For context, we will use Graph schema to construct the grpah schema to define the workflow graph @graph.py; eg: @test_AI_loop.py 


## Workflow Guides


Similarly, ADd more details  and write the e2e guide on how to build workflows, graph schemas etc with diff configuration options and how to configure / use nodes in them;
provide ample egs of workflows using complex nodes, etc
write it in document @workflow_building_guide.md 
@nodes_interplay_guide.md 

@graph.py @test_AI_loop.py 

All nodes registered here are available:
@db_node_register.py 

Guide file for node specific guides:
@core_dynamic_nodes_guide.md 
@data_join_node_guide.md 
@llm_node_guide.md 
@hitl_node_guide.md 
@filter_node_guide.md 
@if_else_node_guide.md 
@transform_node_guide.md 
@load_customer_data_node_guide.md 
@store_customer_data_node_guide.md 
@prompt_constructor_node_guide.md 
@dynamic_router_node_guide.md 
@map_list_router_node_guide.md 
