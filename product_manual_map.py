import os
import pandas as pd
import json
import os

#updated code to point to the miniture manuals- updated product_shorthand, manual link
product_manual_csv = pd.read_csv(os.path.join(os.getcwd(), 'product_manual_links_updated2.csv'))
product_manual_csv.fillna('', inplace= True)

def get_product_name_manual(sku):
    sku_row = product_manual_csv[product_manual_csv['SKU Code'] == sku]
    product_name = list(sku_row['Product shorthand'])[0]
    product_manual = list(sku_row['URL'])[0]
    return product_name, product_manual


if __name__ == '__main__':
    import os
    import json

    get_product_name_manual('MN-ACS-001')

