import datetime

from nikescrapi import NikeScrAPI
from sales_generator import SalesGenerator


def lambda_handler(event, context):
    print(event)
    print(f"""#########
    Loading job with the following parameters:
    max_pages={event['max_pages']}
    day_count={event['day_count']}
    min_sales={event['min_sales']}
    max_sales={event['max_sales']}
    #########""")
    
    # NOTE: for production set max_pages = 200
    nikeAPI = NikeScrAPI(max_pages=event['max_pages'], path='/tmp/data/products')
    df = nikeAPI.getData()
    
    # Sales generator
    gen = SalesGenerator(nike_df=df, min_sales=event['min_sales'], max_sales=event['max_sales'])
    
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=event['day_count'])
    gen.generate_interval(start=start, end=end)
    
    return {
        'products_target': nikeAPI.target_object,
        'sales_target': gen.target_object
    }