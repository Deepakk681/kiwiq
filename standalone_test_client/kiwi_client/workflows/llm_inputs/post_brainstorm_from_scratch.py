from pydantic import BaseModel, Field
from typing import List

POST_CREATION_INITIAL_USER_PROMPT = """
Work on LinkedIn post on behalf of the user using your deep understanding of them, how they think, how they communicate, and how they like to be perceived. 

User Input: {user_input}

User Understanding: {user_dna}

Past Posts Context: {merged_posts}

Instructions:
1. Use the user's input as the core topic/idea for the post
2. Ensure the post aligns with the user's style, tone, and preferences from their DNA
3. Consider the past posts context to maintain consistency and avoid repetition
4. Make sure to use the tone that user prefers
5. Use your understanding of user's industry to draft post
6. Include relevant hashtags that align with the user's style and topic
"""

POST_CREATION_FEEDBACK_USER_PROMPT = """
You are given feedback on a LinkedIn post and specific rewrite instructions.
First, use the feedback to understand what the user wanted or what was lacking in the original post.
Then, use the rewrite instructions to guide how the post should be changed.
Rewrite the LinkedIn post accordingly, making sure it reflects both the critique and the desired improvements.

Original Feedback: {current_feedback_text}
Rewrite Instructions: {rewrite_instructions}

Please rewrite the LinkedIn post accordingly.
"""


POST_CREATION_SYSTEM_PROMPT = """
You are a LinkedIn post generator. You are given:
1. User's input describing what they want to post about
2. User's DNA document containing their style, preferences, and expertise
3. Past posts for context and consistency

Your task is to generate a LinkedIn post that:
- Addresses the user's input topic/idea
- Matches the user's style and preferences
- Maintains consistency with their past content
- Uses appropriate tone and hashtags

If you are given feedback, you should rewrite it based on the user's feedback while maintaining these principles.
"""

class PostDraftSchema(BaseModel):
    post_text: str = Field(..., description="The main body of the LinkedIn post.")
    hashtags: List[str] = Field(..., description="Suggested hashtags.")


POST_LLM_OUTPUT_SCHEMA = PostDraftSchema.model_json_schema()


USER_FEEDBACK_SYSTEM_PROMPT = """
You are an expert LinkedIn content writer.

You have been provided with:
1. A draft LinkedIn post.
2. Feedback from the user about that draft.
3. A User DNA document, which includes detailed information about the user's writing preferences, tone, domain expertise, personality traits, and stylistic choices.
4. Past posts for context and consistency.
"""


USER_FEEDBACK_INITIAL_USER_PROMPT= """
Your Task:

Your job is to interpret the feedback using all provided inputs and produce a structured set of rewrite directives.

You must:
1. Identify the user's intent behind the feedback.
2. Locate specific areas in the original draft that are relevant to the feedback.
3. Determine what changes are required, guided not only by the feedback but also by:
   - The user's style and preferences as described in their DNA
   - The consistency with their past posts
   - The original user input that initiated the post
4. Provide suggestions that are clearly implied by the feedback, or those that directly align with preferences in the DNA document.
5. Be precise about what should change, where it should change, and how it should be rewritten.

---

How to use the provided context:

- Original Draft: Use this to understand the existing content structure, tone, message, and flow. When identifying which parts to change, reference specific phrases or sections from the draft.
  
- User Feedback: Use this to extract the user's explicit or implicit intentions — what they like, dislike, want adjusted, or want added/removed.

- User DNA Document: Use this to ground your interpretation in the user's voice. If the user prefers a bold tone, avoid recommending softer language. If the user tends to write in first person, don't suggest a third-person rewrite. If their DNA emphasizes "industry leadership," consider how the feedback might be interpreted through that lens.

- Past Posts: Use these to ensure consistency in style, tone, and approach while avoiding repetition.

---

Output Structure:

- feedback_type:  Classify the feedback's intent (multiple values allowed if applicable) eg: ("rewrite_request", "tone_change", "clarity_issue", "length_issue", "add_content", "remove_content", "style_adjustment", "grammar_spelling", "unclear").

- rewrite_instructions: Write clear and direct rewrite instructions. Specify:
  - Which parts of the draft should be changed (quote or describe them if helpful).
  - What the change should be (e.g., more concise, more detailed, different tone).
  - How it aligns with the user's style and past content, if relevant.

  ---
  Do not make this interpretation too large. Briefly include things from user's understanding and your judgement.
  ---

Provided Context:

Original LinkedIn Post Draft: 
{current_post_draft}

---

User Feedback: 
{current_feedback_text}

---

User DNA Document (Preferences and Style):
{user_dna_doc}
"""

USER_FEEDBACK_ADDITIONAL_USER_PROMPT= """
I have provided the updated draft that was generated based on the last round of feedback.

Now, the user has provided additional feedback on this version.

Your task is to interpret the new feedback using the **same instructions and structure as before**, and write a fresh set of **rewrite directives**.

Use the **original context** (user DNA, original draft, previous feedback, past posts) to stay consistent with the user's tone, preferences, and intent.

---

Updated Draft: 
{current_post_draft}

New Feedback: 
{current_feedback_text}
"""

