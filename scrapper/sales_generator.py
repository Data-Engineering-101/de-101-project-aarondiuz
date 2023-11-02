from datetime import date, timedelta
import time
import pandas
import random
import os

class SalesGenerator():

    """
    min_qty: Minimum items per ticket (must not be zero)
    max_qty: Maximum items per ticket (must be non zero and equal or higher than min_sales)
    min_index: Minimum random for ticket_id
    max_index: Maximum random for ticket_id
    """
    __min_qty = 1
    __max_qty = 5
    __column_names = ['ticket_id', 'UID', 'currency', 'sales', 'quantity', 'date']
    __file_prefix = 'nike_sales_'

    __min_index=1
    __max_index=1000000

    def __init__(self,
                 nike_df: pandas.DataFrame,
                 min_sales: int,
                 max_sales: int,
                 path='data/sales',
                 chance=2):
        """
        nike_df: Dataframe from NikeScrAPI.getData()
        min_sales: minimum ammount of ticket per product per day (can be zero)
        max_sales: maximum ammount of ticket per product per day (must be non zero and equal or higher than min_sales)
        path: output folder (suggested default value),
        chance: chance of not selling an item per day (1/n) chance of occurring (if this occurs the min_sales and max_sales are not applied)
        """
        self.__df = nike_df
        self.__min = min_sales
        self.__max = max_sales
        self.__path = path
        self.__chance = chance  # chance of a record of NOT being generated 1/n for every day/product

    def __generate_day(self, day: date):
        df = pandas.DataFrame([], columns=self.__column_names)
        for _, row in self.__df.iterrows():
            chance = random.randint(1, self.__chance)
            if (chance == self.__chance):
                sales = random.randint(self.__min, self.__max)
                for _ in range(sales):
                    qty = random.randint(self.__min_qty, self.__max_qty)
                    df.loc[len(df)] = [
                        int('{date}{random}'.format(
                            date=day.strftime('%Y%m%d'),
                            random=str(random.randint(self.__min_index, self.__max_index)).zfill(7)
                        )),
                        row['UID'],
                        row['currency'],
                        row['currentPrice'] * qty,
                        qty,
                        day.strftime('%Y-%m-%d')
                    ]
        return df
 
    def __create_folders(self, date: date):
        path = '{path}/{date_folder}'.format(
            path=self.__path,
            date_folder=date.strftime('%Y/%m/%d')
            )
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def generate_interval(self, start: date, end: date):
        day_count = (end - start).days + 1
        for single_date in (start + timedelta(n) for n in range(day_count)):
          df = self.__generate_day(single_date)
          file_name="{}{}.csv".format(self.__file_prefix, single_date.strftime('%Y_%m_%d'))
          path = self.__create_folders(single_date)
          file_full_path = os.path.join(path,file_name)
          df.to_csv(file_full_path)
