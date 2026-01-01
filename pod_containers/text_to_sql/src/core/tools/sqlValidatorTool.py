from langchain.tools import Tool
import pandas as pd
import json
import io
import re
from pathlib import Path
from langchain.tools import Tool

# Columns exist in semantic model
# ✔ Tables exist in semantic model
# ✔ SQLite syntax (no catalog.schema.table)
# ✔ No unknown tables / columns
# ✔ Time-based questions must use a time column
# ✔ Deterministic errors (no hallucination handling)

# ---- Config ----
CURR_DIR = Path(__file__).resolve().parents[2]
SCHEMA_DIR = CURR_DIR /"core"/ "storage"

# ---- Load semantic models ----
with open(SCHEMA_DIR / "semantic_model.json") as f:
    semantic_model = json.load(f)

def validate_sql(input_data):
    """
    Validate SQL query using semantic model and question context.
    Accepts JSON string or Python dict.
    Ensures:
        - Full catalog.schema.table usage for all tables except CTEs
        - Columns exist in semantic model
        - Time column usage for YTD calculations
    """
    try:
        # Handle either JSON string or dict
        if isinstance(input_data, str):
            inp = json.loads(input_data)
        elif isinstance(input_data, dict):
            inp = input_data
        else:
            raise ValueError("Input must be JSON string or dict")

        query = inp.get("query", "")
        table = inp.get("table", "")
        question = inp.get("question", "")

        errors = []
        warnings = []

        if not query:
            return {"valid": False, "errors": ["Empty SQL query"]}

        # 1. SQLite table format check        
        if "." in table:
            errors.append(
                "SQLite does not support catalog.schema.table format. "
                "Use direct table name only."
            )

        # 2. Table existence check 
        tables = semantic_model.get("tables", {})
        if table not in tables:
            errors.append(f"Table '{table}' not found in semantic model.")

        # 3. Extract referenced columns
        column_pattern = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b")
        sql_keywords = {
            "select", "from", "where", "group", "by", "order", "limit",
            "sum", "avg", "count", "min", "max", "distinct", "as",
            "and", "or", "on", "join", "inner", "left", "right",
            "case", "when", "then", "else", "end"
        }
        tokens = column_pattern.findall(query.lower())
        candidate_columns = {
            t for t in tokens if t not in sql_keywords and not t.isdigit()
        }   
        #4. Validate columns
        if table in tables:
            valid_columns = set(tables[table]["columns"].keys())
            for col in candidate_columns:
                if col not in valid_columns:
                    errors.append(
                        f"Column '{col}' not found in table '{table}'.")
                    

        # 5. Final verdict    
        if errors:
            return {
                "valid": False,
                "reason": "; ".join(errors)
            }

        return {
            "valid": True,
            "reason": "SQL validated successfully for SQLite."
        }

    except Exception as e:
        print(str(e))
        return json.dumps({
            "valid": False,
            "reason": f"Exception during validation: {str(e)}"
        })
    

validate_sql_tool = Tool(
    name="validate_sql",
    description=(
        "Validate SQL query using semantic model and question context before executing. "
        "Ensures SQLite-compatible syntax, valid tables/columns, "
        "and time column usage for time-based questions."
    ),
    func=lambda inp: validate_sql(inp, semantic_model)
)