import pandas as pd
from wati_apis import WATI_APIS

test = WATI_APIS()

preorder_customers = pd.read_csv('./csv_files/preorders_list_broadcast_18082023_mainSheet1_cleaned.csv')

for idx, row in preorder_customers.iterrows():
    print(row)
    customer_name = row['customer_name']
    customer_phone_number = str(row['customer_phone_number']).replace(' ','')
    estimated_delivery_date = '18/08/2023'
    custom_params = [{'name': 'name', 'value': str(customer_name)}, {'name':'date', 'value': str(estimated_delivery_date)}]
    print(customer_phone_number)
    status = test.send_template_message(contact_name = customer_name, contact_number = customer_phone_number , template_name = 'order_reassurance_date', custom_params = custom_params)
