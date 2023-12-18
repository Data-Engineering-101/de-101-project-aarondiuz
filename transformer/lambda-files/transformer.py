import os
import json
import boto3
import pandas as pd
from snowflake.connector import connect, SnowflakeConnection
import datetime

s3 = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')
S3_BUCKET = os.getenv('S3_BUCKET')

# Retrieve credentials from AWS Secrets Manager
def get_secrets():
    secret_name = "nike-project-secrets"
    get_secret_value_response = secrets_client.get_secret_value(
            SecretId=secret_name
        )
    secret = get_secret_value_response['SecretString']
    return secret

def read_table(conn: SnowflakeConnection, table_name: str):
    """
    Read table content from Snowflake
    """
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, conn)
    return df

def write_category_table(conn: SnowflakeConnection, new_items: list, table_name: str):
    """
    Dump dataframe content into Snowflake table
    """
    with conn.cursor() as cursor:
        query = f"INSERT INTO {table_name} (category_name) VALUES (%s)"

        cursor.executemany(query, new_items)

def write_products_table(conn: SnowflakeConnection, new_items, table_name: str):
    """
    Write products dataframe content into Snowflake table
    """
    with conn.cursor() as cursor:
        query = f"INSERT INTO {table_name} (id, category_id, title, subtitle) VALUES (%s, %s, %s, %s)"
        
        data = new_items[['productID', 'ID', 'title', 'subtitle']].drop_duplicates().values.tolist()
        cursor.executemany(query, data)

def write_time_table(conn: SnowflakeConnection, date, table_name: str):
    """
    Write datetime dataframe content into Snowflake table
    """
    with conn.cursor() as cursor:
        query = f"INSERT INTO {table_name} (year, month, day) VALUES (%s, %s, %s)"
        
        cursor.executemany(query, [[date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')]])

def write_sales_table(conn: SnowflakeConnection, new_items, table_name: str):
    """
    Write sales dataframe content into Snowflake table
    """
    with conn.cursor() as cursor:
        query = f"INSERT INTO {table_name} (ticket_id, product_id, sales, quantity, date_id) VALUES (%s, %s, %s, %s, %s)"
        
        data = new_items[['ticket_id', 'productID', 'sales', 'quantity', 'date_id']].drop_duplicates().values.tolist()
        cursor.executemany(query, data)

# Having a CSV file in a S3 bucket, read it and generate a dataframe
def read_csv_from_s3(bucket_name: str, file_name: str):
    obj = s3.get_object(Bucket=bucket_name, Key=file_name)
    df = pd.read_csv(obj['Body'])
    return df

def lambda_handler(event, context):
    print(event)
    products_target = event['products_target']
    sales_target = event['sales_target']

    df = read_csv_from_s3(S3_BUCKET, products_target)
    df_sales = read_csv_from_s3(S3_BUCKET, sales_target)

    # Extract distinct values from column 'category' from df dataframe
    df_new_categories = df['category'].unique()
    # Extract 'UID', 'productID', 'title', 'subtitle' and 'category' from df dataframe
    df_products = df[['UID', 'productID', 'title', 'subtitle', 'category']]

    # Obtain credentials from AWS Secrets Manager
    secret = get_secrets()
    # Transform secret string into dictionary
    secret_dict = json.loads(secret)
    
    with connect(
        account=os.environ.get("ACCOUNT"),
        user=secret_dict['sfUser'],
        password=secret_dict['sfPassword'],
        database=os.environ.get("DATABASE"),
        schema=os.environ.get("SCHEMA"),
        warehouse=os.environ.get("WAREHOUSE"),
        region=os.environ.get("REGION")
    ) as connection:
        
        df_old_categories = read_table(connection, "DIM_CATEGORIES")
        
        # From df_new_categories, remove the values present in df_old_categories
        new_categories = list(set(df_new_categories) - set(df_old_categories['CATEGORY_NAME']))
        
        if len(new_categories) > 0:
            print("New categories found: ", new_categories)
            write_category_table(connection, new_categories, "DIM_CATEGORIES")

        # Read updated categories table
        df_updated_categories = read_table(connection, "DIM_CATEGORIES")

        # Read existing products dimension table
        df_existing_products = read_table(connection, "DIM_PRODUCTS")

        # Join df_products with df_updated_categories on 'category' = 'category_name'
        df_products = df_products.merge(df_updated_categories, left_on=['category'], right_on=['CATEGORY_NAME'], how='left').dropna()

        # From df_products, remove the values present in df_existing_categories
        df_new_products = df_products[~df_products['productID'].isin(df_existing_products['ID'])]

        if len(df_new_products) > 0:
            print("New categories found: ", df_new_products['title'].drop_duplicates().values.tolist())
            write_products_table(connection, df_new_products, "DIM_PRODUCTS")

        # Write date into dim_time table
        # From df_sales, transform 'date' column to datetime
        df_sales['date'] = pd.to_datetime(df_sales['date'])
        date = df_sales['date'][0]
        write_time_table(connection, date, "DIM_TIME")

        # Read updated time dimension table
        df_dim_time = read_table(connection, "DIM_TIME")

        # From df_sales, drop 'currency' column
        df_sales = df_sales.drop(columns=['currency'])

        # From df_sales, transform 'date' column to three separate columns: year, month and day
        df_sales['year'] = df_sales['date'].dt.year
        df_sales['month'] = df_sales['date'].dt.month
        df_sales['day'] = df_sales['date'].dt.day

        # Join df_sales with df_dim_time on 'year', 'month' and 'day'
        df_sales = df_sales.merge(df_dim_time, left_on=['year', 'month', 'day'], right_on=['YEAR', 'MONTH', 'DAY'], how='left')

        # In df_sales, drop columns 'date', 'year', 'month' and 'day'
        df_sales = df_sales.drop(columns=['date', 'year', 'month', 'day','YEAR', 'MONTH', 'DAY'])
        # In df_sales, rename column 'ID' to 'date_id'
        df_sales = df_sales.rename(columns={'ID': 'date_id'})

        # Join df_sales with df_products on 'UID'
        df_sales = df_sales.merge(df_products, on=['UID'], how='left')
        df_sales = df_sales.drop(columns=['UID', 'title', 'subtitle', 'category', 'ID', 'CATEGORY_NAME'])

        # Write df_sales into fact_sales table
        write_sales_table(connection, df_sales, "FACT_SALES")
        print("Number of new sales added to DW: ", len(df_sales))
    
    return event