from langchain.tools import Tool
import pandas as pd
import json
import io

def sync_pretty_format(sql_result):
    """
        Convert SQL results into DataFrame and pretty-format ALL values as strings.
        Formatting rules:
        ✔ Integers → comma formatted  ("1,250")
        ✔ Floats   → 2 decimals       ("3,450.75")
        ✔ Money-related columns add $ ("$4,560.20")
        ✔ All values output as strings
    """

    print("***** FORMATTING PRETTY RESULTS *****")
    # --- Convert input into DataFrame ---
    if isinstance(sql_result, str):
        try:
            sql_result = json.loads(sql_result)
        except:
            try: return pd.read_csv(io.StringIO(sql_result)).to_json(orient="records")
            except: return json.dumps([{"error": "Invalid SQL result format"}])

    if isinstance(sql_result,dict) and "sql_result" in sql_result:
        inner = sql_result["sql_result"]
        # FIX: parse inner JSON string
        if isinstance(inner, str):
            try:
                sql_result = json.loads(inner)
            except:
                sql_result = inner
        else:
            sql_result = inner
    
    if isinstance(sql_result, dict) and "columns" in sql_result and "rows" in sql_result:
        df = pd.DataFrame(sql_result["rows"], columns=sql_result["columns"])
    elif isinstance(sql_result, list):
        df = pd.DataFrame(sql_result)
    elif isinstance(sql_result, pd.DataFrame):
        df = sql_result.copy()
    else:
        df = pd.DataFrame([sql_result])

    for col in df.columns:
        col_lower = col.lower()
        # numeric formatting → convert → then stringify
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].apply(lambda x:
                "{:,}".format(int(x)) if pd.notnull(x) and float(x).is_integer()
                else "{:,.2f}".format(x) if pd.notnull(x)
                else x
            )
        if "pct" in col_lower or "percent" in col_lower:
            df[col] = df[col].apply(lambda x: f"{x}%" if pd.notnull(x) else x)
        
        # Detect money columns + prepend "$"
        if any(key in col_lower for key in ["amount", "price", "revenue", "sales", "dollars"]):
            df[col] = df[col].apply(lambda x: f"${x}" if pd.notnull(x) else x)

        return df.to_json(orient="records", force_ascii=False)
    
# ---- LANGCHAIN TOOL ----
pretty_format_tool = Tool(
    name="format_sql_results",
    description="Formats SQL results into pretty string JSON. ALL values returned as formatted strings.",
    func=sync_pretty_format
)