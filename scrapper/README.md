# Nike API Scrapper


## Prerequirements

- [Python 3.X][python_web]

### Scrapping

*The following commands are used to run the `scrapper/main.py` file this will create the `data/products` and `data/sales` folders with all the raw data required*

From project root:

```sh
cd scrapper
python3 -m venv scrapper_env
pip3 install -r requirements.txt
python3 main.py --max_pages 300
```

> Feel free to use another commands if you already know how to run a py file
> scrapper_env is a suggestion for your virtual environment, however this virtual environment is already excluded in the gitignore file

NOTE: *Architecture supports more than 1 day at once as well as some other configurations, however it was planned to run daily, but it can be tested with more than one day. Check other flags with `--h` option*

```sh
% python3 main.py --h
usage: main.py [-h] [--max_pages MAX_PAGES] [--day_count DAY_COUNT] [--min_sales MIN_SALES] [--max_sales MAX_SALES]

Nike Scraper and Generator launcher

options:
  -h, --help            show this help message and exit
  --max_pages MAX_PAGES
                        Pages to load from NikeScrAPI, for prod use 300
  --day_count DAY_COUNT
                        Days to generates sales records from today to the past, use 0 for 1 day
  --min_sales MIN_SALES
                        Minimum ammount of ticket per product per day (can be zero)
  --max_sales MAX_SALES
                        Maximum ammount of ticket per product per day (must be non zero and equal or higher than min_sales)

# Example:
% python3 main.py --max_pages 300 --day_count 90
```

#### Sales generator constraints

Private properties:
*These properties are static in the class*

```txt
min_qty: Minimum items per ticket (must not be zero)
max_qty: Maximum items per ticket (must be non zero and equal or higher than min_qty)
min_index: Minimum random for ticket_id (must not be zero)
max_index: Maximum random for ticket_id (must be non zero and equal or higher than min_index)
```

Constructor properties:

```txt
nike_df: Dataframe from NikeScrAPI.getData()
min_sales: minimum ammount of ticket per product per day (can be zero)
max_sales: maximum ammount of ticket per product per day (must be non zero and equal or higher than min_sales)
path: output folder (suggested default value),
chance: chance of not selling an item per day (1/n) chance of occurring (if this occurs the min_sales and max_sales are not applied) the bigger the less likely to occur
```

#### Output Files

The new snippet will create the folders with the following structure:

Note: *Assuming data is generated on 2023 Apr 11 for the last 2 days*

```txt
<project root>
  scrapper
    data
      products
        nike_11APR2023_2120.csv
      sales
        2023
          04
            nike_sales_10.csv
            nike_sales_11.csv
```

## Considerations

For testing and development is recommended to have scrapper data for last 2 or 3 days, but for production you should use 300 pages and 30 or more days

```sh
# Testing/Development
python3 main.py --max_pages 1 --day_count 3 --min_sales 0 --max_sales 2

# Production
python3 main.py --max_pages 300 --day_count 70 --min_sales 0 --max_sales 4
```

## Useful links

[Download Terraform][terraform_web]
[Download AWS CLI][aws_cli]
[Setup CLI Profile][aws_profile]
[Download Python][python_web]
[Download Docker][docker_web]
[Snowflake Main Page][snowflake_web]
[Login Snowflake][app_snowflake_web]
[Original Requirements][file_requirements]
[NikeScrAPI][nike_scr_api]

[terraform_web]: https://developer.hashicorp.com/terraform/downloads
[aws_cli]: https://aws.amazon.com/es/cli/
[aws_profile]: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html
[python_web]: https://www.python.org/downloads/
[docker_web]: https://docs.docker.com/get-docker/
[snowflake_web]: https://www.snowflake.com/en/
[app_snowflake_web]: https://app.snowflake.com
[nike_scr_api]: https://github.com/artexmg/NikeScrAPI

[file_requirements]: project_requirements.md
