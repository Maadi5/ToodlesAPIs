import os 
import json
import pandas as pd 

state_code_map = json.load(open(os.path.join(os.getcwd(), 'state_code_map.json'), encoding='utf8'))

def get_order_details(df):
    if not os.path.exists(os.path.join(os.getcwd(), 'order_tracker.csv')):
        tracker_df = pd.DataFrame({'unique_id': [], 'name': [], 'phone_num': [], 'email_id': [], 'awb': [], 'sku': [],
                                    'pincode': [],'state' : [], 'city' : [], 'email_status': [], 'whatsapp_status': [], 'usermanual_whatsapp_status': [], 
                                   'usermanual_email_status': [],'awb_message_timestamp': [], 'usermanual_message_timestamp': []})
        new_ids = set(df['Order Id'])
    else:
        tracker_df = pd.read_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index_col = False)
        unique_ids = set(tracker_df['unique_id'])
        new_ids = set(df['Order Id']).difference(unique_ids)
    
    to_be_pushed = []
    trackerdf = []
    for idx, row in df.iterrows():
        dfdict = {}
        if row['Order Id'] in new_ids:
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
            to_be_pushed.append(dfdict)
            dfdict['email_status'] = ''
            dfdict['whatsapp_status'] = ''
            dfdict['usermanual_email_status'] = ''
            dfdict['usermanual_whatsapp_status'] = ''
            dfdict['awb_message_timestamp'] = ''
            dfdict['usermanual_message_timestamp'] = ''
            trackerdf.append(dfdict)
    del df
    to_be_pushed_df = pd.DataFrame(to_be_pushed)
    del to_be_pushed
    tracker_df_new = pd.DataFrame(trackerdf)
    del trackerdf
    updated_tracker_df = pd.concat([tracker_df, tracker_df_new])
    updated_tracker_df.to_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index = False)
    return to_be_pushed_df

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


        