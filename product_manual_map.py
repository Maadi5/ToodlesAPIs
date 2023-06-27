import os
import pandas as pd
import json 

product_manual_csv = ps.read_csv(os.path.join(os.getcwd(), 'product_manual_links_updated.csv'))

def get_product_name_manual(sku):
    sku_row = product_manual_csv[product_manual_csv['SKU Code'] == sku]
    product_name = list(sku_row['Product Name'])[0]
    product_manual = list(sku_row['URL'])[0]
    return product_name, product_manual
