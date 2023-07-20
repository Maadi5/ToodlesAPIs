import os 
import json
import pandas as pd

state_code_map = json.load(open(os.path.join(os.getcwd(), 'state_code_map.json'), encoding='utf8'))

def get_order_details(browntape_df, tracker_df):

    unique_ids = set(tracker_df['unique_id'])
    new_ids = set(browntape_df['Order Id']).difference(unique_ids)
    
    to_be_pushed = []
    trackerdf = []
    incomplete_orders = []
    for idx, row in browntape_df.iterrows():
        dfdict = {}
        if row['Order Id'] in new_ids and row['Fulfillment Status'] in {'shipped', 'delivered'}:
            phone_num = ''.join(''.join(str(row['Phone']).split(' ')).split('+'))
            phone_num = '91' + phone_num if len(phone_num)!=12 else phone_num
            print('processed phone num: ', phone_num)
            dfdict['unique_id'] = row['Order Id']
            dfdict['name'] = str(row['Customer Name'])
            dfdict['email_id'] = str(row['Customer Email'])
            dfdict['phone_num'] = phone_num
            dfdict['awb'] = str(row['Courier Tracking Number'])
            dfdict['sku'] = str(row['SKU Codes'])
            dfdict['pincode'] = str(row['Pincode'])
            dfdict['state'] = str(row['State'])
            dfdict['city'] = str(row['City'])
            dfdict['email_status'] = ''
            dfdict['whatsapp_status'] = ''
            dfdict['usermanual_email_status'] = ''
            dfdict['usermanual_whatsapp_status'] = ''
            dfdict['awb_message_timestamp'] = ''
            dfdict['usermanual_message_timestamp'] = ''
            trackerdf.append(dfdict)

        if row['Fulfillment Status'] not in {'shipped', 'delivered', 'cancelled', 'returned'}:
            incomplete_orders.append(row)

    incomplete_orders_csv = pd.DataFrame(incomplete_orders)
    to_be_pushed_df = pd.DataFrame(trackerdf)
    return to_be_pushed_df, incomplete_orders_csv

# def create_zoho_invoice_csv(df):
#     bt_zoho_field_map = {'Order Id':'PurchaseOrder',
#                    'Customer Name':'Customer Name',
#                    'State':'Place of Supply',
#                    'Item Titles': 'Item Name',
#                    'Quantity': 'Quantity',
#                    'SKU Codes': 'SKU',
#                    'HSN Code': 'HSN/SAC',
#                    'Item Total': 'Item Price',
#                    'Item Total Discount Value':'Discount Amount',
#                    'Net Shipping':'Shipping Charge',
#                    }
#     bt_zoho_static_vals = {'Invoice Status': 'Overdue',
#                            'Currency Code': 'INR',
#                            'GST Treatment': 'consumer',
#                            'Discount Type': 'item_level',
#                            'Is Discount Before Tax': 'FALSE',
#                            'GST Identification Number (GSTIN)': '',
#                            'Item Type': 'goods',
#                            'Usage unit': 'count',
#                            'Is Inclusive Tax': 'TRUE',
#                            'Item Tax': 'GST18',
#                            'Item Tax Type': 'Tax Group',
#                            'Item Tax %': '18%',
#                            'Supply Type': 'Taxable',
#                            'Account': 'Sales',
#                            'Template Name': 'Spreadsheet Template',
#                            }


        