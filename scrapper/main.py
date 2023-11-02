import datetime

from nikescrapi import NikeScrAPI
from sales_generator import SalesGenerator

import argparse

parser = argparse.ArgumentParser(description='Nike Scraper and Generator launcher')
parser.add_argument('--max_pages', type=int, help='Pages to load from NikeScrAPI, for prod use 200', default=1)
parser.add_argument('--day_count', type=int, help='Days to generates sales records from today to the past, use 0 for 1 day (today + 0 days in the past)', default=0)
parser.add_argument('--min_sales', type=int, help='Minimum ammount of ticket per product per day (can be zero)', default=1)
parser.add_argument('--max_sales', type=int, help='Maximum ammount of ticket per product per day (must be non zero and equal or higher than min_sales)', default=1)
args = parser.parse_args()

print(f"""#########
Loading job with the following parameters:
max_pages={args.max_pages}
day_count={args.day_count}
min_sales={args.min_sales}
max_sales={args.max_sales}
#########""")

# NOTE: for production set max_pages = 200
nikeAPI = NikeScrAPI(max_pages=args.max_pages, path='data/products')
df = nikeAPI.getData()

# Sales generator
gen = SalesGenerator(nike_df=df, min_sales=args.min_sales, max_sales=args.max_sales)

end = datetime.datetime.now()
start = end - datetime.timedelta(days=args.day_count)
gen.generate_interval(start=start, end=end)
