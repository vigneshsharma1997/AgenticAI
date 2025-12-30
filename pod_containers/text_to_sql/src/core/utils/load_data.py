import sqlite3
import pandas as pd
from pathlib import Path

## Config
DB_PATH = "retail.db"
CSV_DIR = Path("/Users/vigneshsharma/Desktop/Langgraph/pod_containers/text_to_sql/src/core/storage")

## SQL_SCHEMA
CREATE_TABLE_SQL = [
    """
    CREATE TABLE IF NOT EXISTS dim_items (
        item_code TEXT PRIMARY KEY,
        item_name TEXT NOT NULL,
        category_code TEXT NOT NULL,
        category_name TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_wholesale_prices (
        price_date DATE NOT NULL,
        item_code TEXT NOT NULL,
        wholesale_price REAL NOT NULL,
        PRIMARY KEY (price_date, item_code),
        FOREIGN KEY (item_code) REFERENCES dim_items(item_code)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_wholesale_prices (
        price_date DATE NOT NULL,
        item_code TEXT NOT NULL,
        wholesale_price REAL NOT NULL,
        PRIMARY KEY (price_date, item_code),
        FOREIGN KEY (item_code) REFERENCES dim_items(item_code)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_item_loss_rates (
        item_code TEXT PRIMARY KEY,
        item_name TEXT NOT NULL,
        loss_rate_percent REAL NOT NULL,
        FOREIGN KEY (item_code) REFERENCES dim_items(item_code)
    );
    """
]

def init_db(db_path:str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")
    for stmt in CREATE_TABLE_SQL:
        cursor.execute(stmt)
    
    conn.commit()
    return conn

## Data Loading
def load_dim_items(conn):
    df = pd.read_csv(CSV_DIR/"annex1.csv")
    df.columns = ['item_code','item_name','category_code','category_name']
    df.to_sql('dim_items',conn,if_exists='append',index=False)

def load_fact_tables(conn):
    df = pd.read_csv(CSV_DIR/'annex2.csv')
    df.columns = ['sales_date','sales_time','item_code','quantity_sold_kg','unit_selling_price','sale_or_return','discount_applied']
    df.to_sql('fact_sales',conn,if_exists='append',index=False)

def load_fact_wholesale_prices(conn):
    df = pd.read_csv(CSV_DIR/'annex3.csv')
    df.columns = ["price_date", "item_code", "wholesale_price"]
    df.to_sql('fact_wholesale_prices',conn,if_exists='append',index=False)

def load_dim_item_loss_rates(conn):
    df = pd.read_csv(CSV_DIR / "annex4.csv")
    df.columns = ["item_code", "item_name", "loss_rate_percent"]
    df.to_sql("dim_item_loss_rates", conn, if_exists="append", index=False)


## Main Execution

if __name__=='__main__':
    print("Initialized Retail Sqllite Database")
    conn = init_db(DB_PATH)
    print("Loading Dim Tables")
    load_dim_items(conn)
    load_dim_item_loss_rates(conn)
    print("Loading fact Tables")
    load_fact_tables(conn)
    load_fact_wholesale_prices(conn)
    conn.close()
    print("Database created and data loaded successfully.")

