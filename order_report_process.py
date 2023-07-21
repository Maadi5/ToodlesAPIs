import os 
import json
import pandas as pd
from datetime import datetime
import traceback
from dateutil.parser import parse
import re

def convert_date_format(input_date):
    try:
        parsed_date = parse(input_date)
        formatted_date = parsed_date.strftime('%Y-%m-%d')
        return formatted_date
    except ValueError:
        return "Invalid date format. Please provide a valid date."


state_code_map = json.load(open(os.path.join(os.getcwd(), 'state_code_map_2.json'), encoding='utf8'))


def get_order_details(browntape_df, tracker_df):

    unique_ids = set(tracker_df['unique_id'])
    print('unique_ids: ', unique_ids)
    browntape_ids = [str(val) for val in list(browntape_df['Order Id'])]
    new_ids = [val for val in browntape_ids if val not in unique_ids]

    print('new ids: ', new_ids)
    
    to_be_pushed = []
    trackerdf = []
    incomplete_orders = []
    for idx, row in browntape_df.iterrows():
        dfdict = {}
        if str(row['Order Id']) in new_ids and row['Fulfillment Status'] in {'shipped', 'delivered', 'packed','packing', 'manifested'}:
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
            dfdict['status'] = str(row['Fulfillment Status'])
            dfdict['email_status'] = ''
            dfdict['whatsapp_status'] = ''
            dfdict['usermanual_email_status'] = ''
            dfdict['usermanual_whatsapp_status'] = ''
            dfdict['awb_message_timestamp'] = ''
            dfdict['usermanual_message_timestamp'] = ''
            trackerdf.append(dfdict)

        if row['Fulfillment Status'] not in {'shipped', 'delivered', 'packed','packing', 'manifested', 'cancelled', 'returned'}:
            incomplete_orders.append(row)

    incomplete_orders_csv = pd.DataFrame(incomplete_orders)
    to_be_pushed_df = pd.DataFrame(trackerdf)
    return to_be_pushed_df, incomplete_orders_csv

def create_zoho_invoice_csv(new_browntape_df):
    bt_zoho_field_map = {'Invoice Number': 'Invoice Number',
                    'Channel Ref':'PurchaseOrder',
                   'Customer Name':'Customer Name',
                    'Invoiced Date': 'Invoice Date',
                   'State':'Place of Supply',
                   'Item Titles': 'Item Name',
                   'Quantity': 'Quantity',
                   'SKU Codes': 'SKU',
                   'HSN Code': 'HSN/SAC',
                   'Item Total': 'Item Price',
                   'Item Total Discount Value':'Discount Amount',
                   'Net Shipping':'Shipping Charge',
                   }
    bt_zoho_static_vals = {'Invoice Status': 'Overdue',
                           'Currency Code': 'INR',
                           'GST Treatment': 'consumer',
                           #'Discount Type': 'item_level',
                           #'Is Discount Before Tax': 'FALSE',
                           'GST Identification Number (GSTIN)': '',
                           'Item Type': 'goods',
                           'Usage unit': 'count',
                           'Is Inclusive Tax': 'TRUE',
                           # 'Item Tax Type': 'Tax Group',
                           'Item Tax %': '18',
                           'Supply Type': 'Taxable',
                           'Account': 'Sales',
                           'Template Name': 'Spreadsheet Template',
                           }

    zoho_csv = []
    bt_cols = list(new_browntape_df.columns)
    for idx, row in new_browntape_df.iterrows():
        dfdict = {}
        for c in bt_cols:
            if c in bt_zoho_field_map and c != 'State' and 'Date' not in c:
                dfdict[bt_zoho_field_map[c]] = row[c]
            elif c == 'State':
                try:
                    dfdict[bt_zoho_field_map[c]] = state_code_map[row[c].lower()]
                except:
                    pass
            elif 'Date' in c and str(row[c]) != 'nan':
                try:
                    date_val = str(row[c]).split(' ')[0]
                    print('original date: ', date_val)
                    try:
                        newdate = str(convert_date_format(date_val))
                    except:
                        print(traceback.format_exc())
                    print('new date: ', newdate)
                    dfdict[bt_zoho_field_map[c]] = newdate
                except:
                    pass
            elif c == 'TAX type':
                dfdict['Item Tax'] = str(row[c]) + '18'
            elif c == 'Invoice Number':
                invoice_num = str(row[c]).replace('23-24_', 'FY24-')
                dfdict[c] = invoice_num
        for cols in bt_zoho_static_vals:
            dfdict[cols] = bt_zoho_static_vals[cols]
        zoho_csv.append(dfdict)

    return pd.DataFrame(zoho_csv)


if __name__ == '__main__':
    testdf = pd.read_csv(r'C:\Users\Adithya\Downloads\btreport_2107_accounting_test.csv', index_col = False)
    newdf = create_zoho_invoice_csv(new_browntape_df=testdf)
    newdf.to_csv(r'C:\Users\Adithya\Downloads\btreport_21_07_zoho.csv', index= False)


        