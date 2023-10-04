import os 
import json
import pandas as pd
from datetime import datetime
import traceback
from dateutil.parser import parse
from utils import input_df_preprocessing,set_shipping_mode
import re

import logging
# Configure the logger
logging.basicConfig(
    filename='postapi_logs.log',  # Specify the log file name
    level=logging.DEBUG,        # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def convert_date_format(input_date):
    try:
        parsed_date = parse(input_date)
        formatted_date = parsed_date.strftime('%Y-%m-%d')
        return formatted_date
    except ValueError:
        return "Invalid date format. Please provide a valid date."


state_code_map = json.load(open(os.path.join(os.getcwd(), 'state_code_map_2.json'), encoding='utf8'))

print(state_code_map)

def get_order_details(browntape_df, tracker_df):

    unique_ids = set(tracker_df['unique_id'])
    print('unique_ids: ', unique_ids)
    browntape_ids = [str(val) for val in list(browntape_df['Order Id'])]
    new_ids = [val for val in browntape_ids if val not in unique_ids]
    print('new ids: ', new_ids)
    
    to_be_pushed = []
    trackerdf = []
    new_orders_browntape_subset = []
    incomplete_orders = []
    cancelled_cod_orders = []

    for idx, row in browntape_df.iterrows():
        dfdict = {}
        if str(row['Order Id']) in new_ids and row['Fulfillment Status'] in {'shipped', 'delivered', 'packed','packing', 'manifested'}:
            phone_num = ''.join(''.join(str(row['Phone']).split(' ')).split('+'))
            if len(phone_num)>10 and phone_num[0] == '0':
                phone_num = ''.join(phone_num[1:])

            order_type = row['Order Type']
            shipping_amount = row['Gross Shipping Amount']
            dfdict['shipping_mode'] = set_shipping_mode(order_type= order_type, shipping_charge= shipping_amount)

            phone_num = '91' + phone_num if len(phone_num)!=12 else phone_num
            print('processed phone num: ', phone_num)
            dfdict['timestamp'] = ''
            dfdict['order_date'] = str(row['Order Date(IST)'])
            dfdict['unique_id'] = str(row['Order Id'])
            dfdict['channel_order_number'] = str(row['Channel Ref'])
            dfdict['channel_order_type'] = str(row['Channel Order Type'])
            dfdict['channel_invoice_number'] = str(row['Channel Invoice No.'])
            dfdict['invoice_number'] = str(row['Invoice Number'])
            dfdict['customer_id'] = str(row['Customer ID'])
            dfdict['name'] = str(row['Customer Name'])
            dfdict['email_id'] = str(row['Customer Email'])
            dfdict['phone_num'] = str(phone_num)
            dfdict['awb'] = str(row['Courier Tracking Number'])
            dfdict['sku'] = str(row['SKU Codes'])
            dfdict['pincode'] = str(row['Pincode'])
            dfdict['state'] = str(row['State'])
            dfdict['city'] = str(row['City'])
            dfdict['status'] = str(row['Fulfillment Status'])
            dfdict['courier'] = str(row['Courier Name'])
            # dfdict['shipping_mode'] =
            dfdict['email_status'] = ''
            dfdict['whatsapp_status'] = ''
            dfdict['usermanual_email_status'] = ''
            dfdict['usermanual_whatsapp_status'] = ''
            dfdict['awb_message_timestamp'] = ''
            dfdict['usermanual_message_timestamp'] = ''
            dfdict['tracking_code_update'] = ''
            dfdict['tracking_status_update'] = ''
            dfdict['tracking_est_update'] = ''
            dfdict['last_tracked_time'] = ''
            dfdict['alarm_status'] = ''
            dfdict['delivery_update_message'] = ''
            dfdict['usermanual_during_delivery_whatsapp'] = ''
            dfdict['usermanual_during_delivery_email'] = ''
            dfdict['delivery_delay_message'] = ''


            trackerdf.append(dfdict)
            new_orders_browntape_subset.append(row)

        elif str(row['Order Id']) in new_ids and row['Fulfillment Status'] not in {'shipped', 'delivered', 'packed','packing', 'manifested', 'cancelled', 'returned'}:
            incomplete_orders.append(row)

        elif row['Fulfillment Status'] == 'cancelled' and row['Order Type'] == 'COD':
            cancelled_cod_orders.append(row)


    if incomplete_orders:
        incomplete_orders_csv = pd.DataFrame(incomplete_orders)
    else:
        incomplete_orders_csv = None

    if cancelled_cod_orders:
        cancelled_cod_orders_csv = pd.DataFrame(cancelled_cod_orders)
    else:
        cancelled_cod_orders_csv = None

    print('trackerdf: ', trackerdf)
    to_be_pushed_df = pd.DataFrame(trackerdf)
    if new_orders_browntape_subset:
        new_browntape_subset_df = pd.DataFrame(new_orders_browntape_subset)
    else:
        new_browntape_subset_df = None
    return to_be_pushed_df, incomplete_orders_csv, cancelled_cod_orders_csv, new_browntape_subset_df


def check_cod_cancellations(tracker_df, cancelled_orders_df):
    cancelled_ids = set(cancelled_orders_df['Order Id'])
    tracker_ids = set(tracker_df['unique_id'])
    id_matches = tracker_ids.intersection(cancelled_ids)

    cancelled_ids_tracker = []
    cancelled_ids_original_df = []
    print('id matches: ', id_matches)
    count = 0
    idx_to_id = {}
    for idx, row in cancelled_orders_df.iterrows():
        idx_to_id[idx] = count
        count += 1

    for idx in id_matches:
        ind = tracker_df.index[tracker_df['unique_id'] == idx].tolist()[0]
        for val in list(cancelled_orders_df['Order Id']):
            print(val, type(val))
        print('idx val: ', idx)
        index_original = cancelled_orders_df.index[cancelled_orders_df['Order Id'] == idx].tolist()[0]
        status_value = tracker_df.at[ind, 'status']
        if status_value not in {'delivered', 'cancelled'}:
            cancelled_ids_tracker.append(idx)
            cancelled_ids_original_df.append(index_original)

    cancelled_indexes = [idx_to_id[val] for val in cancelled_ids_original_df]
    print('original indexes: ', cancelled_ids_original_df)
    print('the cancelled df: ', cancelled_orders_df)
    print('idx to id: ', idx_to_id)
    original_df_cancelled = cancelled_orders_df.iloc[cancelled_indexes]

    return cancelled_ids_tracker, original_df_cancelled

def create_zoho_invoice_csv(new_browntape_df):
    flag = True
    new_browntape_df = input_df_preprocessing(new_browntape_df)
    try:
        for idx, row in new_browntape_df.iterrows():
            #print(row['Invoice Number'])
            if 'SFY' in row['Invoice Number']:
                new_browntape_df.at[idx, 'Channel Ref'] = str(row['Order Reference 2']).replace('#', '')
            if row['Item Total Discount Value'] != '' and row['Order Total Discount Value'] == '':
                new_browntape_df.at[idx, 'Order Total Discount Value'] = row['Item Total Discount Value']
            elif row['Item Total Discount Value'] != '' and row['Order Total Discount Value'] != '':
                flag  = 'Discount calculation failure'
                #print(new_browntape_df['Channel Ref'])
    except:
        print('reference number replace code failed')

    bt_zoho_field_map = {'Invoice Number': 'Invoice Number',
                    'Channel Ref':'Reference#',
                   'Customer Name':'Customer Name',
                    'Invoiced Date': 'Invoice Date',
                   # 'State':'Place of Supply',
                   'Item Titles': 'Item Name',
                   'Quantity': 'Quantity',
                   'SKU Codes': 'SKU',
                   'HSN Code': 'HSN/SAC',
                   'Item Total': 'Item Price',
                   #'Item Total Discount Value':'Entity Discount Amount',
                   'Order Total Discount Value':'Entity Discount Amount'
                         }

    bt_zoho_amount_add_map = { 'Shipping Charge': {'Gross Shipping Amount', 'Gross COD Fee'}}

    bt_customer_fields_map ={
        'Customer Name': {'Customer Name'},
        'Address Line 1': {'Billing Address', 'Shipping Address'},
        'Address Line 2': {'Billing Street2', 'Shipping Street2'},
        'City': {'Billing City', 'Shipping City'},
        'State': {'Billing State', 'Shipping State'},
        'Country': {'Billing Country', 'Shipping Country'},
        'Pincode': {'Billing Code', 'Shipping Code'},
        'Phone': {'Billing Phone', 'Shipping Phone'},
    }

    firstcry_details_map = {
        'Customer Name': 'Digital Age Retail Pvt.Ltd',
        'Billing Address': 'NO.16 GANDHI NAGAR MAIN ROAD EXTN',
        'Shipping Address': 'NO.16 GANDHI NAGAR MAIN ROAD EXTN',
        'Shipping Street2': 'EKKATTUTHANGAL',
        'Billing Street2': 'EKKATTUTHANGAL',
        'Billing City': 'Chennai',
        'Shipping City': 'Chennai',
        'Billing State': 'Tamil Nadu',
        'Shipping State': 'Tamil Nadu',
        'Billing Country': 'India',
        'Shipping Country': 'India',
        'Billing Code': '600032',
        'Shipping Code': '600032',
        'Billing Phone': '',
        'Shipping Phone': '',
        'GST Identification Number (GSTIN)': '33AADCD8136E1ZY',
        'GST Treatment': 'business_gst'
    }

    bt_zoho_static_vals = {'Invoice Status': 'Overdue',
                           'Currency Code': 'INR',
                           'GST Treatment': 'consumer',
                           'Discount Type': 'entity_level',
                           'Is Discount Before Tax': 'TRUE',
                           'GST Identification Number (GSTIN)': '',
                           'Item Type': 'goods',
                           'Usage unit': 'count',
                           'Is Inclusive Tax': 'TRUE',
                           # 'Item Tax Type': 'Tax Group',
                           'Supply Type': 'Taxable',
                           'Account': 'Sales',
                           'Template Name': 'Spreadsheet Template',
                           }

    zoho_csv = []
    item_level_discount_add = []
    bt_cols = list(new_browntape_df.columns)
    for idx, row in new_browntape_df.iterrows():
        if row['Fulfillment Status'] in {'shipped', 'delivered', 'packed','packing', 'manifested'}:
            dfdict = {}
            for c in bt_cols:
                if c in bt_zoho_field_map and c!= 'State' and 'Date' not in c and c!= 'Invoice Number' and c!= 'HSN Code':
                    dfdict[bt_zoho_field_map[c]] = row[c]
                elif c == 'State':
                    try:
                        print(row[c])
                        #print(state_code_map[row[c].lower()])
                        dfdict['Place of Supply'] = state_code_map[row[c].strip().lower()]
                        #dfdict[bt_zoho_field_map[c]] = row[c]
                    except:
                        print(traceback.format_exc())
                        pass
                elif 'Date' in c and str(row[c]) != 'nan':
                    try:
                        #print('c: ', c)
                        date_val = str(row[c]).split(' ')[0]
                        #print(date_val)
                        #print('original date: ', date_val)
                        try:
                            newdate = str(convert_date_format(date_val))
                            #print('newdate: ', newdate)
                            dfdict[bt_zoho_field_map[c]] = newdate
                            #print('success: ', bt_zoho_field_map[c])
                        except:
                            #print(traceback.format_exc())
                            #print('failure in date')
                            pass
                        #print('new date: ', newdate)
                    except:
                        pass
                elif c == 'TAX type':
                    if row[c] == 'IGST':
                        taxval = '18'
                        dfdict['Item Tax'] = str(row[c]) + taxval
                        dfdict['Item Tax %'] = taxval
                        dfdict['Item Tax Type'] = 'Simple'
                    elif row[c] == 'SGST/CGST':
                        taxval = '18'
                        dfdict['Item Tax'] = 'GST' + taxval
                        dfdict['Item Tax %'] = taxval
                        dfdict['Item Tax Type'] = 'Tax Group'
                elif c == 'Invoice Number':
                    invoice_num = str(row[c]).replace('23-24_', 'FY24-')
                    dfdict[c] = invoice_num

                elif c in bt_customer_fields_map:
                    for val in bt_customer_fields_map[c]:
                        dfdict[val] = row[c]
                elif c == 'HSN Code':
                    try:
                        if type(row[c]) == str:
                            dfdict[bt_zoho_field_map[c]] = ''.join(str(row[c])[:-2])
                    except:
                        print(traceback.format_exc())

            #Discount updated logic
            try:
                if dfdict['Entity Discount Amount'] != '':
                    print('discount loop')
                    discount_value = float(dfdict['Entity Discount Amount'].replace(',',''))
                    item_price = float(dfdict['Item Price'].replace(',',''))
                    discount_fraction = (discount_value/item_price)
                    item_price_without_gst = item_price/1.18
                    discount_without_gst = discount_fraction*item_price_without_gst
                    dfdict['Entity Discount Amount'] = str(discount_without_gst)
            except:
                print(traceback.format_exc())

            #Quantity logic
            try:
                dfdict['Item Price'] = str(float(dfdict['Item Price'].replace(',',''))/float(dfdict['Quantity']))
            except:
                print(traceback.format_exc())

            for cols in bt_zoho_static_vals:
                dfdict[cols] = bt_zoho_static_vals[cols]

            for cols in bt_zoho_amount_add_map:
                dfdict[cols] = sum([float(row[bt_col]) for bt_col in bt_zoho_amount_add_map[cols]])

            if 'FRC' in str(row['Invoice Number']):
                for key in firstcry_details_map:
                    dfdict[key] = str(firstcry_details_map[key])

            # if zoho_csv and zoho_csv[-1]['Reference#'] != dfdict['Reference#']:
            #     valid_float_discounts = []
            #     for val in item_level_discount_add:
            #         try:
            #             valid_float_discounts.append(float(str(val.replace(',',''))))
            #         except:
            #             pass
            #     if len(valid_float_discounts)>1:
            #         total_discount_val = sum(valid_float_discounts)
            #         for val in range(len(item_level_discount_add)):
            #             index = -1*(val+1)
            #             zoho_csv[index]['Entity Discount Amount'] = total_discount_val
            #     item_level_discount_add = []
            # item_level_discount_add.append(dfdict['Entity Discount Amount'])
            zoho_csv.append(dfdict)

    return pd.DataFrame(zoho_csv), flag


if __name__ == '__main__':
    browntape_df = pd.read_csv(r'/Users/adithyam.a/Downloads/btreport_898829 (1).csv', index_col = False)
    browntape_df = input_df_preprocessing(browntape_df)
    tracker_df = pd.read_csv(r'/Users/adithyam.a/Downloads/MinitureUserData - Main Dataset.csv')
    to_be_pushed_df, incomplete_orders_csv, cancelled_cod_orders_csv, new_browntape_subset_df = get_order_details(browntape_df= browntape_df, tracker_df=tracker_df)
    check_cod_cancellations(tracker_df=tracker_df, cancelled_orders_df=cancelled_cod_orders_csv)
    # testdf = input_df_preprocessing(testdf)
    # newdf,_ = create_zoho_invoice_csv(new_browntape_df=testdf)
    # newdf.to_csv(r'/Users/adithyam.a/Downloads/zoho_invoices_latest_new5.csv', index= False)


        