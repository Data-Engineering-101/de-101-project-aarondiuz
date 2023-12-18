-- Query the top 5 sales by product
SELECT dp.title, SUM(fs.sales) as total_sales
FROM fact_sales fs
LEFT JOIN dim_products dp ON fs.product_id = dp.id
GROUP BY dp.title
ORDER BY total_sales DESC
LIMIT 5;

-- Query the top 5 sales by category agrupation
SELECT dc.category_name, SUM(fs.sales) as total_sales
FROM fact_sales fs
LEFT JOIN dim_products dp ON fs.product_id = dp.id
LEFT JOIN dim_categories dc ON dp.category_id = dc.id
GROUP BY dc.category_name
ORDER BY total_sales DESC
LIMIT 5;

-- Query the least 5 sales by category agrupation
SELECT dc.category_name, SUM(fs.sales) as total_sales
FROM fact_sales fs
LEFT JOIN dim_products dp ON fs.product_id = dp.id
LEFT JOIN dim_categories dc ON dp.category_id = dc.id
GROUP BY dc.category_name
ORDER BY total_sales ASC
LIMIT 5;

-- Query the top 5 sales by title and subtitle agrupation
SELECT dp.title, dp.subtitle, SUM(fs.sales) as total_sales
FROM fact_sales fs
LEFT JOIN dim_products dp ON fs.product_id = dp.id
GROUP BY dp.title, dp.subtitle
ORDER BY total_sales DESC
LIMIT 5;

-- Query the top 3 products that has greatest sales per category (using window function)
WITH CAT_RANK AS 
(SELECT dc.category_name, dp.title, SUM(fs.sales) as total_sales, RANK() OVER(PARTITION BY dc.category_name ORDER BY total_sales DESC) as ranking
FROM fact_sales fs
LEFT JOIN dim_products dp ON fs.product_id = dp.id
LEFT JOIN dim_categories dc ON dp.category_id = dc.id
GROUP BY dc.category_name, dp.title)

SELECT * exclude(ranking)
FROM CAT_RANK
WHERE ranking <= 3
ORDER BY category_name, ranking;