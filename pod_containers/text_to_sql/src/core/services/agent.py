from datetime import datetime
import json
import os
import re
from pathlib import Path
from langchain.agents.react.agent import create_react_agent
from langchain.agents import AgentExecutor,create_tool_calling_agent
from langchain_core.prompts import PromptTemplate
# from langchain.callback.bas import BaseCallbackHandler
from langchain.agents.react.output_parser import ReActOutputParser
from typing import ClassVar

from core.tools.prettyFormatTool import pretty_format_tool
from core.tools.resolveProductColumnTool import create_resolve_product_column_tool
from core.tools.sqlValidatorTool import validate_sql_tool
from core.connectors.mcp_client import sql_query_tool,create_mcp_sql_query_tool
# from langchain.agents.react.output_parser import ReActSingleInputOutputParser
from core.connectors.llm_connector import llm
from dotenv import load_dotenv
load_dotenv()

CURR_DIR = Path(__file__).resolve().parents[2]
SCHEMA_DIR = CURR_DIR/"core"/"storage"
CONFIDENCE_THRESHOLD = os.getenv("CONFIDENCE_THRESHOLD")


# ---- Prompt Template ----
template = f"""
You are an intelligent talk-to-your-data agent with access to semantic models and executable tools.

You must reason step by step internally, but DO NOT reveal internal reasoning.
You MUST use tools whenever required. Tool calls must be made using structured arguments only.

---

### CURRENT DATETIME
{{current_datetime}}

### SEMANTIC MODELS
{{semantic_model}}

### CONVERSATION HISTORY
{{history}}

### USER QUESTION
{{input}}

##Agent Scratchpad
{{agent_scratchpad}}
---

## TASK OBJECTIVES

1. Use the most recent conversation history to understand context.
2. If the question is unrelated to the datasets, answer using internal knowledge only.
3. Identify which table(s) the question relates to.
4. Compute a relevance score between 0–1 for each candidate table unless one table is clearly dominant.
5. Do NOT proceed until a relevant table is selected.

---

## COLUMN / ENTITY RESOLUTION (MANDATORY)

When a product, customer, item, or category value appears in the question:

• You MUST call the column resolution tool.
• Each value must be resolved independently.
• Multiple values require multiple tool calls.

### Tool usage rules:
- Pass arguments as structured JSON
- Never describe the tool call in text
- Do not batch multiple values in one call

### Required arguments:
- value: the raw entity string from the question
- value_type: "item" or "category"
- table: chosen table name

If resolution confidence is low or no match is found:
- Capture unresolved entities
- Preserve `top5_possible_matches` for follow-up

---

## SQL GENERATION RULES

Once all required entities are resolved:

1. Generate a SQL query string ONLY.
2. Do NOT execute SQL manually.
3. Automatically include JOINs for foreign keys.
4. Include only necessary tables.
5. Assume year-to-date if no time filter is provided.
6. Use backticks for column names with spaces (SQLite compliant).
7. Use double quotes for values with apostrophes or special characters.
8. If customer names do not match exactly, use ILIKE instead of '='.
9. When comparing time periods:
   - Include absolute difference if meaningful
   - Prefer percentage change: (new - old) / old * 100
   - Name column clearly (e.g., revenue_pct_change)

---

## SQL VALIDATION AND EXECUTION (STRICTLY ENFORCED)

If a SQL query is generated at any point:

1. You MUST call the SQL validation tool.
   - Pass the generated query, user question, and chosen table.

2. Only if validation returns `valid = true`:
   - Call the mcp_sql_query tool.

3. Immediately after execution:
   - Call the format_sql_results tool to convert results into a DataFrame-compatible structure.

4. If no results are returned:
   - You may refactor the query ONE time
   - Repeat validation → execution → formatting

---

## EMPTY OR UNRESOLVED RESULTS HANDLING

If:
- SQL execution returns no rows AND
- One or more entities remain unresolved

You MUST return a Final Answer explaining:
- Which entities failed resolution
- Why resolution failed
- A table of top 5 possible matches with confidence scores
- Ask the user to confirm or rephrase

No further SQL execution should occur in this case.

---

## FINAL OUTPUT REQUIREMENTS (STRICT)

Final Answer MUST be returned as STRICT JSON with the following schema:

  "reasoning": "<clear explanation of what was done>",
  "sql": "<final executed SQL query or empty string>",
  "answer": "<only if not dataset-related>",
  "analysis": "<business interpretation of results>",
  "sqlResult": <formatted query results>,
  "graph": <plotly graph generated from sqlResult>,
  "title": "<summary title>",
  "followUpQuestions": [
    "3-4 relevant questions answerable from the data"
  ],
  "sqlSummary": "<3-4 sentence explanation of the SQL logic>"

---

## GRAPH GENERATION

If sqlResult exists:
- Generate the most appropriate Plotly chart
- Add legends and labels
- Store graph spec in `graph`

---

## FOLLOW-UP QUESTIONS

Only generate follow-up questions if:
- They are directly answerable from the semantic model
- They relate to the result produced

---

## HARD CONSTRAINTS (NO EXCEPTIONS)

- NEVER hallucinate tool or dataset names
- NEVER execute SQL without tools
- NEVER return SQL without validation + execution + formatting
- NEVER produce Final Answer unless sqlResult exists when SQL is involved
- NEVER expose internal chain-of-thought
- All numeric values must be returned as strings

Failure to follow these rules is considered an incorrect response.
"""

prompt = PromptTemplate(
    input_variables=[
        "input",
        "semantic_model",
        "history",
        "current_datetime",
        "agent_scratchpad"
    ],
    template=template
)


async def createTools():
    try:
        with open(SCHEMA_DIR/"semantic_model.json") as f:
            semantic_model = json.load(f)
        resolve_colmn_tool =  await create_resolve_product_column_tool(sql_query_tool)
        mcp_sql_tool = await create_mcp_sql_query_tool(sql_query_tool)
        print("==== IN Tools =====")
        tools = [
            resolve_colmn_tool,
            validate_sql_tool,
            mcp_sql_tool,
            pretty_format_tool
        ]
        return tools , semantic_model
    except Exception as e:
        print(f"Caught Exception in create Tools {str(e)}")


async def run_agent(question:str,history:list[dict]=[],max_tries: int=2):
    """
        Run the agent asynchronously and return the final answer with sql query.
        Includes self healing for ReAct formatting erros like missing Action after Thought.
    """
    try:
        tools,semantic_model = await createTools()
        tool_names = [t.name for t in tools]
        print("tool Names ",tool_names)
        

        print("history ",history)
        if not history:
           print("Inside")
           history_str = []
        else:
            history_str = "\n".join([f"User: {h['question']}\nAssistant: {h['answer']}" for h in history[:5]])
        print("History Str: ",history_str)

        # # Create async reat Agent 
        # react_agent = create_react_agent(
        #     llm= llm,
        #     tools = tools,
        #     prompt = prompt
        #     # output_parser=ReActSingleInputOutputParser()
        # )
        # agent_executor = AgentExecutor(
        #                     agent = react_agent,
        #                     tools = tools,
        #                     verbose= True,
        #                     handling_parsing_erros = True,
        #                     return_intermediate_steps=True,
        #                 )

        agent = create_tool_calling_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )
        


        attempt = 0
        while attempt<=max_tries:
            try:
                output = await agent_executor.ainvoke({
                    "input": question,
                    "history": history_str,
                    "semantic_model": semantic_model,
                    "current_datetime": datetime.now().isoformat()
                })
                return output
            except Exception as e:
                print("Error in the Tool!")
                err_str = str(e)
                if "Invalid Format: Missing 'Action:' after 'Thought:'" in err_str and attempt<max_tries:
                    print(f"ReAct format error detected. Attempted self-heal # {attempt+1}...")
                    # Simple self-heal: append instruction reminder to history
                    history_str += "\n Assistant: Please ensure every Thought is immediatly followed by an Action step."
                    attempt+=1
                    continue
                else:
                    print(f"Raised : {str(e)}")
                    raise e
    except Exception as e:
        print(f"Error in Run Agent: {str(e)}")
        return {"answer":"Error in Run Agent"}
