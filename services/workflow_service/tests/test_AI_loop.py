"""
AI Loop Workflow Test.

This module tests a workflow that implements an AI-Human feedback loop pattern,
where an AI generates content, a human reviews it, and based on approval status,
either completes the workflow or loops back to the AI for refinement.
"""
from datetime import datetime
import json
import logging
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Type, Union, Annotated
from pydantic import BaseModel, Field, model_validator

from workflow_service.config.constants import (
    GRAPH_STATE_SPECIAL_NODE_NAME,
    HITL_NODE_NAME_PREFIX, 
    HITL_USER_PROMPT_KEY, 
    HITL_USER_SCHEMA_KEY,
    INPUT_NODE_NAME,
    OUTPUT_NODE_NAME,
    ROUTER_CHOICE_KEY,
    TEMP_STATE_UPDATE_KEY,
    CONFIG_REDUCER_KEY
)
from workflow_service.graph.graph import (
    EdgeMapping, 
    EdgeSchema, 
    GraphSchema, 
    NodeConfig,
    ConstructDynamicSchema
)
from workflow_service.graph.builder import GraphBuilder
from workflow_service.registry.nodes.base import BaseNode, BaseSchema
from workflow_service.registry.nodes.core.dynamic_nodes import DynamicRouterNode, HITLNode, DynamicSchema, DynamicSchemaFieldConfig, InputNode, OutputNode, RouterSchema, BaseDynamicNode
from workflow_service.registry.registry import MockRegistry
from workflow_service.graph.runtime.adapter import LangGraphRuntimeAdapter
from workflow_service.registry.schemas.reducers import ReducerRegistry

from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages

# ===============================
# Schema Definitions
# ===============================

class MessagesSchema(BaseSchema):
    """Schema for storing conversation history."""
    # Note add_messages accessable as Callable via field_info.metadata
    messages: Annotated[List[AnyMessage], add_messages] = Field(default_factory=list, description="List of messages in the conversation")
    # messages: Annotated[List[AnyMessage], add_messages] = Field(..., description="List of messages in the conversation")


class MessagesWithUserPromptSchema(MessagesSchema):
    """Schema for AI node input."""
    user_prompt: str = Field(description="User prompt for AI generation")


class Approved(Enum):
    """Enum for approval status."""
    APPROVED = "yes"
    REJECTED = "no"


class UserInputSchema(BaseSchema):
    """Schema for user input."""
    approved: Approved = Field(description="Approval status (true/false as string)")
    review_comments: Optional[str] = Field(None, description="Review comments if not approved")
    
    @model_validator(mode='after')
    def validate_review_comments(self) -> 'UserInputSchema':
        """
        Validate that review_comments is present if not approved.
        
        This validator runs after the model is created and checks that when
        the content is not approved (approved='false'), review comments are provided.
        
        Returns:
            UserInputSchema: The validated instance
            
        Raises:
            ValueError: If approved is 'false' and review_comments is None or empty
        """
        if self.approved == Approved.REJECTED and not self.review_comments:
            raise ValueError("Review comments must be provided when content is not approved")
        return self


class FinalOutputSchema(BaseSchema):
    """Schema for final workflow output."""
    approved_content: str = Field(description="Final approved content")
    review_iterations: int = Field(description="Number of review iterations")
    messages: List[AnyMessage] = Field(default_factory=list, description="Complete conversation history")

# ===============================
# Node Implementations
# ===============================

class AIGeneratorNode(BaseNode[MessagesWithUserPromptSchema, MessagesSchema, None]):
    """
    AI Generator node that creates content based on previous feedback.
    
    This node simulates an AI generating content, potentially incorporating
    feedback from previous iterations.
    """
    node_name: ClassVar[str] = "ai_generator"
    node_version: ClassVar[str] = "1.0.0"
    
    input_schema_cls: ClassVar[Type[MessagesWithUserPromptSchema]] = MessagesWithUserPromptSchema
    output_schema_cls: ClassVar[Type[MessagesSchema]] = MessagesSchema
    config_schema_cls: ClassVar[Type[None]] = None

    config: None = None
    
    def process(self, input_data: MessagesWithUserPromptSchema, config: Dict[str, Any], *args: Any, **kwargs: Any) -> MessagesSchema:
        """
        Generate AI content, potentially based on previous feedback.
        
        Args:
            input_data: Contains user prompt and optional message history
            config: Not used
            
        Returns:
            MessagesSchema: Updated message history with new AI message
        """
        
        user_prompt = input_data.user_prompt
        messages = input_data.messages
        
        # Count existing AI messages to track iterations
        ai_messages = [msg for msg in messages if msg.role == "assistant"]
        iteration = len(ai_messages)
        
        # Generate response based on iteration and feedback
        if iteration == 0:
            # Initial response
            content = f"Initial AI-generated content for prompt: '{user_prompt}'"
        else:
            # Follow-up response based on feedback
            content = f"Improved AI content (iteration {iteration+1}) based on feedback: '{user_prompt}' AND message history: \n\n{messages}\n\n"
        
        # Create a new AI message with the generated content
        ai_message = AIMessage(
            content=content,
            role="assistant",  # Role required by LangGraph/LangChain
            metadata={
                "iteration": iteration + 1,
                "timestamp": datetime.now().isoformat(),
                "source": "ai_generator_node"
            }
        )

        human_message = HumanMessage(
            content=user_prompt,
            role="user",  # Role required by LangGraph/LangChain
            metadata={
                "iteration": iteration + 1,
                "timestamp": datetime.now().isoformat(),
                "source": "ai_generator_node"
            }
        )
        
        # # Create updated messages list with the new AI message
        # updated_messages = list(messages)  # Create a copy of the existing messages
        # updated_messages.append(ai_message)
        
        # # Log the generation process
        # print(f"AI Generator created content (iteration {iteration+1})")
        
        # # For debugging purposes
        # if kwargs.get("debug", False):
        #     print(f"Generated content: {content}")
        #     print(f"Total messages: {len(updated_messages)}")
        
        # Return updated message history with new AI message
        return MessagesSchema(messages=[human_message, ai_message])  # The reducer will handle combining with existing messages


class HumanReviewNode(HITLNode):
    """
    Human-in-the-loop node for content review.
    
    This node presents AI-generated content to a human reviewer and collects
    their feedback on whether to approve it or request changes.
    """
    node_name: ClassVar[str] = f"{HITL_NODE_NAME_PREFIX}review"
    node_version: ClassVar[str] = "1.0.0"
    
    output_schema_cls: ClassVar[Type[UserInputSchema]] = UserInputSchema
    # config_schema_cls: ClassVar[Type[None]] = None

    # # instance config
    # config: None = None
    
    # def process(self, input_data: Dict[str, Any], config: Dict[str, Any], *args: Any, **kwargs: Any) -> UserInputSchema:
    #     """
    #     Process AI content through human review.
        
    #     In a real implementation, this would present data to a human and wait for feedback.
        
    #     Args:
    #         input_data: Dynamic schema containing fields from central state
    #         config: Configuration for the review
            
    #     Returns:
    #         UserInputSchema: Human review feedback
    #     """
    #     # Get data from central state
    #     state = kwargs.get("state", {})
    #     user_prompt = state.get("user_prompt", "")
    #     messages = state.get("messages", [])
        
    #     # Get the latest AI message to show to the human
    #     ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
    #     latest_ai_content = ai_messages[-1].content if ai_messages else "No AI content available"
        
    #     # Prepare the prompt for the human reviewer
    #     user_prompt_data = {
    #         "user_prompt": user_prompt,
    #         "latest_ai_content": latest_ai_content,
    #         "messages": messages,
    #         "iteration": len(ai_messages)
    #     }
        
    #     # For testing, we'll simulate this with an interrupt handler
    #     interrupt_data = {
    #         HITL_USER_PROMPT_KEY: user_prompt_data,
    #         HITL_USER_SCHEMA_KEY: UserInputSchema.model_json_schema()
    #     }
        
    #     # This will be caught by the graph executor and handled by our interrupt handler
    #     return self.interrupt(interrupt_data)


# BaseSchema
class ApprovalRouterChoiceOutputSchema(BaseSchema):
    """Schema for approval router choice output."""
    choices: List[str] = Field(description="List of choices for routing decisions", min_length=1)

# Dynamic Schema: here, since node doesn't have any outgoing edges, the input dynamic edges will be added to this Output Schema!
# NOTE: Marking Schemas as DynamicSchemas may have unintended side-effects, so be very careful!
# DynamicSchema generation inherits from original dynamic schema so it has new dynamic fields as well as all fields defined in original base dynamic schema!
class ApprovalRouterChoiceOutputDynamicSchema(DynamicSchema):
    """Schema for approval router choice output."""
    choices: List[str] = Field(description="List of choices for routing decisions", min_length=1)

class ApprovalRouterConfigSchema(RouterSchema):
    """Schema for approval router choice output."""
    field_name: str = Field(description="Field name to check for approval")
    field_value: str = Field(description="Value to check for approval")
    route_if_true: str = Field(description="Route to take if field is true")
    route_if_false: str = Field(description="Route to take if field is false")


class ApprovalRouterNode(DynamicRouterNode):
    """
    Router node that decides workflow path based on human approval.
    
    This node routes to either the final processor node (if approved) or back to the
    AI generator (if not approved) based on human review feedback.
    """
    node_name: ClassVar[str] = "approval_router"
    node_version: ClassVar[str] = "1.0.0"

    config_schema_cls: ClassVar[Type[ApprovalRouterConfigSchema]] = ApprovalRouterConfigSchema
    output_schema_cls: ClassVar[Type[ApprovalRouterChoiceOutputSchema]] = ApprovalRouterChoiceOutputDynamicSchema  # ApprovalRouterChoiceOutputSchema  ApprovalRouterChoiceOutputDynamicSchema

    # instance config
    config: ApprovalRouterConfigSchema
    
    def process(self, input_data: BaseSchema, config: Dict[str, Any], *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Decide routing based on human approval status.
        
        Args:
            input_data: Dynamic schema with fields from central state
            config: Not used
            
        Returns:
            Dict: Contains the routing decision
        """
        # Get data from central state
        check_value = getattr(input_data, self.config.field_name)
        route_if_true = self.config.route_if_true
        route_if_false = self.config.route_if_false
        
        # Determine route based on approval
        # Handle both enum values and regular string/value comparisons
        if hasattr(check_value, "value") and isinstance(check_value, Enum):
            # If check_value is an Enum, compare its value
            is_match = check_value.value == self.config.field_value
        else:
            # Direct comparison for non-Enum types
            is_match = check_value == self.config.field_value
            
        route = route_if_true if is_match else route_if_false

        # Here, we handle the case for dynamic edge being passed to Output Schema if Output schema was set as Dynamic too!
        if issubclass(self.output_schema_cls, ApprovalRouterChoiceOutputDynamicSchema):
            # passthrough input to this node in case output schema is Dynamic!
            output_data = self.output_schema_cls(choices=[route], **{self.config.field_name: check_value})
        else:
            output_data = self.output_schema_cls(choices=[route])
        
        # Just return the routing decision
        return {TEMP_STATE_UPDATE_KEY: output_data, ROUTER_CHOICE_KEY: [route]}


class FinalProcessorNode(BaseDynamicNode):
    """
    Final processor node that prepares the output of the workflow.
    
    This node formats the final approved content and metadata for output.
    """
    node_name: ClassVar[str] = "final_processor"
    node_version: ClassVar[str] = "1.0.0"
    
    input_schema_cls = DynamicSchema
    output_schema_cls = FinalOutputSchema
    config_schema_cls = None

    # instance config
    config: None = None
    
    def process(self, input_data: DynamicSchema, config: Dict[str, Any], *args: Any, **kwargs: Any) -> FinalOutputSchema:
        """
        Process the final approved content for output.
        
        Args:
            input_data: Dynamic schema with fields from central state
            config: Not used
            
        Returns:
            FinalOutputSchema: Final formatted output
        """
        # Get data from central state
        messages = input_data.messages
        
        # Get the latest AI message as approved content
        ai_messages = [msg for msg in messages if msg.role == "assistant"]
        approved_content = ai_messages[-1].content if ai_messages else "No approved content"
        
        # Count AI messages to determine number of iterations
        review_iterations = len(ai_messages)
        
        return FinalOutputSchema(
            approved_content=approved_content,
            review_iterations=review_iterations,
            messages=messages
        )


# ===============================
# Graph Creation
# ===============================

def create_ai_loop_graph() -> GraphSchema:
    """
    Create a workflow graph with an AI-Human feedback loop.
    
    This function configures a graph with nodes for AI content generation,
    human review, and conditional routing based on approval status.
    
    Returns:
        GraphSchema: The configured graph schema with all nodes and edges
    """
    # Input node
    input_node = NodeConfig(
        node_id=INPUT_NODE_NAME,
        node_name=INPUT_NODE_NAME,
        node_config={},
        # dynamic_output_schema=ConstructDynamicSchema(fields={
        #     "user_prompt": DynamicSchemaFieldConfig(type="str", required=True, description="User prompt for AI generation")
        # })
    )
    
    # Output node
    # output_node = NodeConfig(
    #     node_id=OUTPUT_NODE_NAME,
    #     node_name=OUTPUT_NODE_NAME,
    #     node_config={},
    #     dynamic_input_schema=ConstructDynamicSchema(fields={
    #         "approved_content": DynamicSchemaFieldConfig(type="str", required=True, description="Final approved content"),
    #         "review_iterations": DynamicSchemaFieldConfig(type="int", required=True, description="Number of review iterations"),
    #         "messages": DynamicSchemaFieldConfig(type="list", required=True, description="Complete conversation history")
    #     })
    # )
    
    # AI Generator node
    ai_generator_node = NodeConfig(
        node_id="ai_generator",
        node_name="ai_generator",
        node_config=None
    )
    
    # Human Review node
    human_review_node = NodeConfig(
        node_id="human_review",
        node_name=f"{HITL_NODE_NAME_PREFIX}review",
        node_config=None
    )
    
    # Approval Router node
    approval_router_node = NodeConfig(
        node_id="approval_router",
        node_name="approval_router",
        node_config={
            "field_name": "approved",
            "field_value": "yes",
            "route_if_true": "final_processor",
            "route_if_false": "ai_generator",
            "choices": ["final_processor", "ai_generator"],
            "allow_multiple": False,
        }
    )
    
    # Final Processor node
    final_processor_node = NodeConfig(
        node_id="final_processor",
        node_name="final_processor",
        node_config=None
    )
    
    # Create edges
    edges = [
        # # Input to Central State (store user prompt)
        # EdgeSchema(
        #     src_node_id=INPUT_NODE_NAME,
        #     dst_node_id=GRAPH_STATE_SPECIAL_NODE_NAME,
        #     mappings=[
        #         EdgeMapping(src_field="user_prompt", dst_field="user_prompt")
        #     ]
        # ),
        
        # Input to AI Generator (initial run with user prompt)
        EdgeSchema(
            src_node_id=INPUT_NODE_NAME,
            dst_node_id="ai_generator",
            mappings=[
                EdgeMapping(src_field="user_prompt", dst_field="user_prompt")
            ]
        ),
        
        # Central State to AI Generator (for loops - pass messages and user_prompt)
        EdgeSchema(
            src_node_id=GRAPH_STATE_SPECIAL_NODE_NAME,
            dst_node_id="ai_generator",
            mappings=[
                EdgeMapping(src_field="messages_history", dst_field="messages"),
                # EdgeMapping(src_field="user_prompt", dst_field="user_prompt")
            ]
        ),
        
        # AI Generator to Central State (store generated messages)
        EdgeSchema(
            src_node_id="ai_generator",
            dst_node_id=GRAPH_STATE_SPECIAL_NODE_NAME,
            mappings=[
                EdgeMapping(src_field="messages", dst_field="messages_history")
            ]
        ),
        
        # AI Generator to Human Review
        EdgeSchema(
            src_node_id="ai_generator",
            dst_node_id="human_review",
            mappings=[
                EdgeMapping(src_field="messages", dst_field="last_messages"),
            ]  # No direct data passing needed, will get from central state
        ),
        
        # Central State to Human Review (get messages for review)
        EdgeSchema(
            src_node_id=GRAPH_STATE_SPECIAL_NODE_NAME,
            dst_node_id="human_review",
            mappings=[
                EdgeMapping(src_field="messages_history", dst_field="all_messages"),
                # EdgeMapping(src_field="user_prompt", dst_field="user_prompt")
            ]
        ),
        
        # Human Review to Central State (store review decision)
        EdgeSchema(
            src_node_id="human_review",
            dst_node_id=GRAPH_STATE_SPECIAL_NODE_NAME,
            mappings=[
                EdgeMapping(src_field="approved", dst_field="approved"),
                EdgeMapping(src_field="review_comments", dst_field="review_comments")
            ]
        ),
        
        # Human Review to Approval Router
        EdgeSchema(
            src_node_id="human_review",
            dst_node_id="approval_router",
            mappings=[
                EdgeMapping(src_field="approved", dst_field="approved")
            ]
        ),
        
        # # Central State to Approval Router (get approval status if needed)
        # EdgeSchema(
        #     src_node_id=GRAPH_STATE_SPECIAL_NODE_NAME,
        #     dst_node_id="approval_router",
        #     mappings=[
        #         EdgeMapping(src_field="approved", dst_field="approved")
        #     ]
        # ),
        
        # Approval Router to AI Generator (if not approved)
        EdgeSchema(
            src_node_id="approval_router",
            dst_node_id="ai_generator",
            mappings=[],  # No direct data passing needed
            # condition="choices[0] == 'ai_generator'"
        ),
        
        # Approval Router to Final Processor (if approved)
        EdgeSchema(
            src_node_id="approval_router",
            dst_node_id="final_processor",
            mappings=[],  # No direct data passing needed
            # condition="choices[0] == 'final_processor'"
        ),
        
        # Central State to Final Processor (get final state)
        EdgeSchema(
            src_node_id=GRAPH_STATE_SPECIAL_NODE_NAME,
            dst_node_id="final_processor",
            mappings=[
                EdgeMapping(src_field="messages_history", dst_field="messages")
            ]
        ),
        
        # Final Processor to Output
        # EdgeSchema(
        #     src_node_id="final_processor",
        #     dst_node_id=OUTPUT_NODE_NAME,
        #     mappings=[
        #         EdgeMapping(src_field="approved_content", dst_field="approved_content"),
        #         EdgeMapping(src_field="review_iterations", dst_field="review_iterations"),
        #         EdgeMapping(src_field="messages", dst_field="messages")
        #     ]
        # )
    ]
    
    # Create and return graph schema with metadata for reducers
    return GraphSchema(
        nodes={
            INPUT_NODE_NAME: input_node,
            # OUTPUT_NODE_NAME: output_node,  # output_node
            "ai_generator": ai_generator_node,
            "human_review": human_review_node,
            "approval_router": approval_router_node,
            "final_processor": final_processor_node
        },
        edges=edges,
        input_node_id=INPUT_NODE_NAME,
        output_node_id="final_processor",  # OUTPUT_NODE_NAME
        metadata={
            # GRAPH_STATE_SPECIAL_NODE_NAME: {
            #     CONFIG_REDUCER_KEY: {
            #         "messages": "add_messages"  # Use add_messages reducer for message history
            #     }
            # },
        },
    )


# ===============================
# Test Execution Functions
# ===============================

def setup_registry() -> MockRegistry:
    """
    Set up a MockRegistry with all test nodes registered.
    
    Returns:
        MockRegistry: The configured registry
    """
    registry = MockRegistry()
    
    # Register built-in nodes
    registry.register_node(HITLNode)
    registry.register_node(InputNode)
    registry.register_node(OutputNode)
    
    # Register custom nodes
    registry.register_node(HumanReviewNode)
    registry.register_node(AIGeneratorNode)
    registry.register_node(ApprovalRouterNode)
    registry.register_node(FinalProcessorNode)
    
    return registry


def run_ai_loop_test() -> Dict[str, Any]:
    """
    Build and run the AI-Human feedback loop graph.
    
    Returns:
        Dict[str, Any]: The output of the graph execution
    """
    # Setup registry and create graph schema
    registry = setup_registry()
    graph_schema = create_ai_loop_graph()
    
    # Create graph builder
    builder = GraphBuilder(registry)
    
    # Build graph entities
    graph_entities = builder.build_graph_entities(graph_schema)

    print(f"Graph input input schema: {json.dumps(graph_entities['node_instances'][INPUT_NODE_NAME].input_schema_cls.model_json_schema(), indent=4)}")
    print(f"Graph input output schema: {json.dumps(graph_entities['node_instances'][INPUT_NODE_NAME].output_schema_cls.model_json_schema(), indent=4)}")
    print(f"Graph central state: {graph_entities['central_state'].__annotations__}\n\n")
    print(f"Graph graph state: {graph_entities['graph_state'].__annotations__}\n\n")
    
    # Create runtime adapter
    adapter = LangGraphRuntimeAdapter()
    
    # Configure runtime
    runtime_config = graph_entities["runtime_config"]
    runtime_config["thread_id"] = 1
    runtime_config["use_checkpointing"] = True
    
    # Build graph
    graph = adapter.build_graph(graph_entities)
    
    # Define human review interrupt handler
    def human_review_handler(interrupt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle human review interrupts.
        
        This function simulates human feedback by alternating between approval
        and requesting changes for demonstration purposes.
        
        Args:
            interrupt_data: Dictionary containing the user prompt and schema
            
        Returns:
            Dict[str, Any]: Simulated human response
        """
        user_prompt_data = interrupt_data[HITL_USER_PROMPT_KEY]
        user_schema = interrupt_data[HITL_USER_SCHEMA_KEY]
        print(user_prompt_data)
        # Print debug information
        print("\n#### HUMAN REVIEW INTERRUPT ####")
        # print(f"User prompt: {user_prompt_data.get('user_prompt', '')}")
        # print(f"Latest AI content: {user_prompt_data.get('latest_ai_content', '')}")
        # print(f"Current iteration: {user_prompt_data.get('iteration', 0)}")
        if isinstance(user_prompt_data, dict):
            last_messages = user_prompt_data.get('last_messages', [])
        elif hasattr(user_prompt_data, "last_messages"):
            last_messages = user_prompt_data.model_dump().get('last_messages', [])
            # last_messages = user_prompt_data.last_messages
        else:
            last_messages = []
        
        if isinstance(user_prompt_data, dict):
            all_messages = user_prompt_data.get('all_messages', [])
        elif hasattr(user_prompt_data, "all_messages"):
            all_messages = user_prompt_data.model_dump().get('all_messages', [])
            # user_prompt_data.all_messages
        else:
            all_messages = []
        
        from langchain_core.load import dumpd, dumps, load, loads

        print(f"Last messages: {dumps(last_messages, pretty=True)}")
        print(f"All messages: {dumps(all_messages, pretty=True)}")

        print(f"User schema: {json.dumps(user_schema, indent=4)}")
        
        # For demo purposes, approve on the 3rd iteration, request changes otherwise
        # last_messages = user_prompt_data.get('last_messages', [])
        iteration = [l["metadata"]["iteration"] for l in last_messages][0]
        if iteration >= 3:
            approved = "yes"
            review_comments = "Content looks good now, approved!"
        else:
            approved = "no"
            review_comments = f"Please improve iteration {iteration}. Make it more concise."
        
        print(f"Human decision: {'Approved' if approved == 'true' else 'Needs revision'}")
        print(f"Comments: {review_comments}")
        print("############################\n")
        
        # Return simulated human feedback
        return {
            # "user_prompt": user_prompt_data.get("user_prompt", ""),
            "approved": approved,
            "review_comments": review_comments
        }
    
    # Execute graph
    # result = adapter.execute_graph(
    #     graph, 
    #     input_data={"user_prompt": "Generate creative content about AI workflows"}, 
    #     config=runtime_config, 
    #     output_node_id=graph_entities["output_node_id"],
    #     interrupt_handler=human_review_handler
    # )

    result = adapter.execute_graph(  # execute_graph  execute_graph_stream
        graph, 
        input_data={"user_prompt": "Generate creative content about AI workflows"}, 
        config=runtime_config, 
        output_node_id=graph_entities["output_node_id"],
        interrupt_handler=human_review_handler
    )
    
    return result


if __name__ == "__main__":
    # Run the AI loop test
    result = run_ai_loop_test()
    
    # Print results
    print("\n#### FINAL RESULT ####")
    print(f"Approved content: {result.approved_content}")
    print(f"Review iterations: {result.review_iterations}")
    print(f"Message history length: {len(result.messages)}")
    print("######################")

