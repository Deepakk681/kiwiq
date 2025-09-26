
# Phase 1: Run a workflow, edit configs
1. Separate page: configure sandbox identifiers (this will be applied for all workflows to be run); configure X workflow identifiers (eg: which brief to load -- this is specific to a workflow) -- This will be common across all workflows!
2. List of all workflows (fetch by path); choose a workflow and go to that workflow testing page
   1. Workflow testing page: see past runs of workflow tests; create new run
3. Separate page: configure setup docs; check if these should be deleted or not + any additional docs to be deleted?
4. Workflow inputs
5. TODO: connect workflow 

6. ingest workflows in test namespace; mega workflows ingests all dependencies before executing and runs those test namespace workflows after ingestion
7. single editable file per workflow iwth all configs to be changed, prompts ,schemas, model etc ; verbose variable name; comments etc; ALSO schema fields graph mappings if any mappings / config dependent on LLM output schema! Edit file, it gets overwritten and you're good!

8. Workflow Running: HITL data; intermediate outputs, node wise outputs??, final outputs; HITL interaction and validation

Session, multipage; potential login?

# Phase 2: Experiment configs, multiple runs belonging to experiment, eval runs and show evals (evals of specific workflow runs, between indices or dates)
Show past test runs of a worklfow in test key!
