import luigi
import logging
import pandas as pd
import time
import sqlalchemy
from datetime import datetime
from pipeline.extract import Extract
from pipeline.utils.db_conn import db_connection
from pipeline.utils.read_sql import read_sql_file
from sqlalchemy.orm import sessionmaker
import os
from pangres import upsert


# Define DIR
DIR_ROOT_PROJECT = os.getenv("DIR_ROOT_PROJECT")
DIR_TEMP_LOG = os.getenv("DIR_TEMP_LOG")
DIR_TEMP_DATA = os.getenv("DIR_TEMP_DATA")
DIR_LOAD_QUERY = os.getenv("DIR_LOAD_QUERY")
DIR_LOG = os.getenv("DIR_LOG")

class Load(luigi.Task):
    
    def requires(self):
        return Extract()
    
    def run(self):
         
        # Configure logging
        logging.basicConfig(filename = f'{DIR_TEMP_LOG}/logs.log', 
                            level = logging.INFO, 
                            format = '%(asctime)s - %(levelname)s - %(message)s')
        
 
        # Read Data to be load
        try:
            # Read csv
            country = pd.read_csv(self.input()[0].path)
            address = pd.read_csv(self.input()[1].path)
            address_status = pd.read_csv(self.input()[2].path)
            author = pd.read_csv(self.input()[3].path)
            book_language = pd.read_csv(self.input()[4].path)
            publisher = pd.read_csv(self.input()[5].path)
            book = pd.read_csv(self.input()[6].path)
            book_author = pd.read_csv(self.input()[7].path)
            customer = pd.read_csv(self.input()[8].path)
            shipping_method = pd.read_csv(self.input()[9].path)
            cust_order = pd.read_csv(self.input()[10].path)
            customer_address = pd.read_csv(self.input()[11].path)
            order_status = pd.read_csv(self.input()[12].path)
            order_history = pd.read_csv(self.input()[13].path)
            order_line = pd.read_csv(self.input()[14].path)
            
            logging.info(f"Read Extracted Data - SUCCESS")
            
        except Exception:
            logging.error(f"Read Extracted Data  - FAILED")
            raise Exception("Failed to Read Extracted Data")
        
        
        #----------------------------------------------------------------------------------------------------------------------------------------
        # Establish connections to DWH
        try:
            _, dwh_engine = db_connection()
            logging.info(f"Connect to DWH - SUCCESS")
            
        except Exception:
            logging.info(f"Connect to DWH - FAILED")
            raise Exception("Failed to connect to Data Warehouse")
        
        
        #----------------------------------------------------------------------------------------------------------------------------------------
        # Record start time for loading tables
        start_time = time.time()  
        logging.info("==================================STARTING LOAD DATA=======================================")
        # Load to tables to pacbook schema
        try:
            
            try:
                country = country.set_index("country_id")
                address = address.set_index("address_id")
                address_status = address_status.set_index("status_id")
                author = author.set_index("author_id")
                book_language = book_language.set_index("language_id")
                publisher = publisher.set_index("publisher_id")
                book = book.set_index("book_id")
                book_author = book_author.set_index(["book_id", "author_id"])
                customer = customer.set_index("customer_id")
                shipping_method = shipping_method.set_index("method_id")
                cust_order = cust_order.set_index("order_id")
                customer_address = customer_address.set_index(["customer_id", "address_id"])
                order_status = order_status.set_index("status_id")
                order_history = order_history.set_index("history_id")
                order_line = order_line.set_index("line_id")

                tabls_to_load = {
                    "country": country,
                    "address": address,
                    "address_status": address_status,
                    "author": author,
                    "book_language": book_language,
                    "publisher": publisher,
                    "book": book,
                    "book_author": book_author,
                    "customer": customer,
                    "shipping_method": shipping_method,
                    "cust_order": cust_order,
                    "customer_address": customer_address,
                    "order_status": order_status,
                    "order_history": order_history,
                    "order_line": order_line
                }

                for table_name, dataframe in tabls_to_load.items():
                    upsert(
                        con=dwh_engine,
                        df=dataframe,
                        table_name=table_name,
                        schema='staging',
                        if_row_exists='update'
                    )
                    logging.info(f"LOAD 'staging.{table_name}' - SUCCESS")

                logging.info(f"LOAD All Tables To DWH-pacbook - SUCCESS")
                
            except Exception:
                logging.error(f"LOAD All Tables To DWH-pacbook - FAILED")
                raise Exception('Failed Load Tables To DWH-pacbook')        
        
            # Record end time for loading tables
            end_time = time.time()  
            execution_time = end_time - start_time  # Calculate execution time
            
            # Get summary
            summary_data = {
                'timestamp': [datetime.now()],
                'task': ['Load'],
                'status' : ['Success'],
                'execution_time': [execution_time]
            }

            # Get summary dataframes
            summary = pd.DataFrame(summary_data)
            
            # Write Summary to CSV
            summary.to_csv(f"{DIR_TEMP_DATA}/load-summary.csv", index = False)
            
                        
        #----------------------------------------------------------------------------------------------------------------------------------------
        except Exception:
            # Get summary
            summary_data = {
                'timestamp': [datetime.now()],
                'task': ['Load'],
                'status' : ['Failed'],
                'execution_time': [0]
            }

            # Get summary dataframes
            summary = pd.DataFrame(summary_data)
            
            # Write Summary to CSV
            summary.to_csv(f"{DIR_TEMP_DATA}/load-summary.csv", index = False)
            
            logging.error("LOAD All Tables To DWH - FAILED")
            raise Exception('Failed Load Tables To DWH')   
        
        logging.info("==================================ENDING LOAD DATA=======================================")
        
    #----------------------------------------------------------------------------------------------------------------------------------------
    def output(self):
        return [luigi.LocalTarget(f'{DIR_TEMP_LOG}/logs.log'),
                luigi.LocalTarget(f'{DIR_TEMP_DATA}/load-summary.csv')]