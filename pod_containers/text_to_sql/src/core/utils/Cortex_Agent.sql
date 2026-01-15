CREATE OR REPLACE AGENT my_sql_orchestrator_agent
  COMMENT = 'Agent that uses Cortex Analyst (text->SQL) and orchestrates SQL execution'
  PROFILE = '{"display_name": "SQL Orchestrator", "avatar": "db-icon.png", "color": "teal"}'
  FROM SPECIFICATION
$$
models:
  orchestration: "claude-4-sonnet"           # <- example; change to allowed model in your account

orchestration:
  budget:
    seconds: 60
    tokens: 8000

instructions:
  response: "Be concise, return results or explain if query can't be executed."
  orchestration: "For structured DB analysis use Analyst1"
  system: "Agent orchestrator that converts NL to SQL, executes it, and returns results."
  sample_questions:
    - question: "Show me total revenue last quarter"
      answer: "I will generate SQL using Analyst1 and run it on the warehouse."

tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "Analyst1"
      description: "Analyst converts natural language to SQL against semantic view(s)"

tool_resources:
  Analyst1:
    semantic_view: "CORTEX_ANALYST_DEMO.REVENUE_TIMESERIES.RAW_DATA/revenue_timeseries.yaml"
    warehouse: "CORTEX_ANALYST_WH"
    query_timeout_seconds: 30
$$;
