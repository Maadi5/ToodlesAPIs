import os
import pandas as pd
import json
import os
import config
from google_sheets_apis import googlesheets_apis



#updated code to point to the miniture manuals- updated product_shorthand, manual link


gsheets_productinfo = googlesheets_apis(spreadsheet_id= config.product_details_spreadsheet_id)
product_manual_csv = gsheets_productinfo.load_sheet_as_csv(sheet_name=config.product_details_sheet_name)
# product_manual_csv = pd.read_csv(os.path.join(os.getcwd(), 'product_manual_links_updated3.csv'))
product_manual_csv.fillna('', inplace= True)

def get_product_name_manual(sku):
    gsheets_productinfo = googlesheets_apis(spreadsheet_id=config.product_details_spreadsheet_id)
    product_manual_csv = gsheets_productinfo.load_sheet_as_csv(sheet_name=config.product_details_sheet_name)
    # product_manual_csv = pd.read_csv(os.path.join(os.getcwd(), 'product_manual_links_updated3.csv'))
    product_manual_csv.fillna('', inplace=True)
    sku_row = product_manual_csv[product_manual_csv['SKU Code'] == sku]
    product_name = list(sku_row['Product shorthand'])[0]
    product_manual = list(sku_row['Usermanual URL'])[0]
    review_url = list(sku_row['Review URL'])[0]
    try:
        cashback = list(sku_row['Cashback'])[0]
        if str(cashback) == '':
            cashback = 0
    except:
        cashback = 0
    return product_name, product_manual, review_url, cashback


if __name__ == '__main__':
    import os
    import json

    A,B,a, b = get_product_name_manual('YK-KW-006')
    print(A)
    print(B)
    print(a)
    print(b)
