import asyncio
import re
import json
import difflib
import time
from langchain.tools import Tool
from pathlib import Path

CURR_DIR = Path(__file__).resolve().parents[2]
SCHEMA_DIR = CURR_DIR/"core"/"storage"

#AI9401
#IX1692

with open(SCHEMA_DIR/"semantic_model.json") as f:
    semantic_model = json.load(f)

CACHE_TTL_SECONDS = 24*60*60 # 1 Day
_table_cache = {} # Table_name -> {"timestamp":<epoch>,"col_value_map":{col:{values}}}


async def create_resolve_product_column_tool(sql_query_tool):
    async def async_resolve(value:str,value_type:str):
        print(f"Calling Resolve Product for {value}")
        # determine columns + table
        if value_type == "item":
            columns_to_resolve = semantic_model["lookup_index"].get("item", [])
            table = "dim_items"
        elif value_type == "category":
            columns_to_resolve = semantic_model["lookup_index"].get("category", [])
            table = "dim_items" 
        else:
            return {"best_column":None,"best_value":None,"confidence":0.0}

        simple_cols = [c for c in columns_to_resolve]

        # Check cache
        now = time.time()
        if table in _table_cache:
            cache_entry = _table_cache[table]
            if now - cache_entry["timestamp"]<CACHE_TTL_SECONDS:
                col_value_map = cache_entry["col_value_map"]
                print(f"Using cached values for {table} ({len(col_value_map)} columns)")
            else:
                print(f"Cache expired for {table}, fetching fresh data")
                col_value_map = None
        else:
            col_value_map = None
        
        if col_value_map is None:
            select_list = ",\n".join([f"`{c}`" for c in simple_cols])
            query = f"""
            SELECT DISTINCT {select_list} from {table} where {" OR ".join([f"`{c}` IS NOT NULL" for c in simple_cols])}
            """
            try:
                raw = await sql_query_tool.func(query)
                parsed = json.loads(raw)
                rows = parsed.get("rows",[])
            except Exception as e:
                return {"error":f"SQL fetched failed : {e}"}
            
            col_value_map = {col: [] for col in simple_cols}
            for row in rows:
                for idx,col in enumerate(simple_cols):
                    if row[idx] not in (None,"",[],{}):
                        col_value_map[col].append(str(row[idx]))

            ## Store in Cache
            _table_cache[table] = {"timestamp":now,"col_value_map":col_value_map}

        
        # ---- Fuzzy match across columns -----
        results = []
        possible_matches = []
        for col,values in col_value_map.items():
            for val in values:
                sim = difflib.SequenceMatcher(None, val.lower(), value.lower()).ratio()
                if sim >= 0.65:
                    results.append({"col":col,"value":val,"confidence":sim})
                if sim < 0.65:
                    possible_matches.append({"col":col,"value":val,"confidence":sim})
        print("Top 5 matches with threshold as 0.5",sorted(results,key=lambda x : x['confidence'],reverse=True[:5]))

        if not results:
            return {"best_column": None,
                "best_value": None,
                "confidence": 0.0,
                "top5_possible_matches":sorted(possible_matches, key=lambda x: x["confidence"], reverse=True)[:5]}
        
        best = max(results, key=lambda r: r["confidence"])
        return {
            "best_column": best["col"],
            "best_value": best["value"],
            "confidence": round(best["confidence"], 3)
        }
    
    def sync_resolve(input_json:str):
        try:
            inp = json.loads(input_json)
            val = inp.get("value")
            val_type = inp.get("value_type")
            
            return json.dumps(asyncio.run(async_resolve(val, val_type)))
        except Exception as e:
            return json.dumps({"best_column": None, "best_value": None, "confidence": 0.0, "error": str(e)})

    return Tool(
        name="resolve_column_tool",
        func=sync_resolve,
        description="Matches a item/category value across ALL columns by scanning full table once, with 1-day cache."
    )