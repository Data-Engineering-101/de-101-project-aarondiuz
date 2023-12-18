-- dim_categories
CREATE OR REPLACE TABLE dim_categories (
    id INT PRIMARY KEY,
    category_name VARCHAR(128)
);

-- dim_time
CREATE OR REPLACE TABLE dim_time (
    id INT PRIMARY KEY,
    year INT,
    month INT,
    day INT
);

-- dim_products
CREATE OR REPLACE TABLE dim_products (
    id VARCHAR(128) PRIMARY KEY,
    category_id INT FOREIGN KEY REFERENCES dim_categories (id) NOT ENFORCED,
    title VARCHAR(255),
    subtitle VARCHAR(255)
);

-- fact_sales
CREATE OR REPLACE TABLE fact_sales (
    ticket_id BIGINT PRIMARY KEY,
    product_id VARCHAR(128) FOREIGN KEY REFERENCES dim_products (id) NOT ENFORCED,
    sales DOUBLE,
    quantity INT,
    date_id INT FOREIGN KEY REFERENCES dim_time (id) NOT ENFORCED
);