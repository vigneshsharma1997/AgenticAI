-- 1. Item & Category Master
CREATE TABLE IF NOT EXISTS dim_items (
    item_code TEXT PRIMARY KEY,
    item_name TEXT NOT NULL,
    category_code TEXT NOT NULL,
    category_name TEXT NOT NULL
);

-- 2. Sales Fact Table
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date DATE NOT NULL,
    sale_time TIME NOT NULL,
    item_code TEXT NOT NULL,
    quantity_sold_kg REAL NOT NULL,
    unit_selling_price REAL NOT NULL,
    sale_or_return TEXT CHECK (sale_or_return IN ('Sale', 'Return')),
    discount_applied TEXT CHECK (discount_applied IN ('Yes', 'No')),
    FOREIGN KEY (item_code) REFERENCES dim_items(item_code)
);

-- 3. Wholesale Price Fact Table
CREATE TABLE IF NOT EXISTS fact_wholesale_prices (
    price_date DATE NOT NULL,
    item_code TEXT NOT NULL,
    wholesale_price REAL NOT NULL,
    PRIMARY KEY (price_date, item_code),
    FOREIGN KEY (item_code) REFERENCES dim_items(item_code)
);

-- 4. Item Loss Rate Dimension
CREATE TABLE IF NOT EXISTS dim_item_loss_rates (
    item_code TEXT PRIMARY KEY,
    item_name TEXT NOT NULL,
    loss_rate_percent REAL NOT NULL,
    FOREIGN KEY (item_code) REFERENCES dim_items(item_code)
);


CREATE TABLE IF NOT EXISTS sf_sessions (
        session_id TEXT PRIMARY KEY,
        account TEXT NOT NULL,
        host TEXT NOT NULL,
        token TEXT NOT NULL,
        token_issued_at REAL NOT NULL,
        expires_at REAL NOT NULL
    );