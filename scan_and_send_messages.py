# import schedule
import os
import time
import pandas as pd
from product_manual_map import get_product_name_manual
import traceback
from email_sender import send_usermanual_email, send_dispatch_email
from wati_apis import WATI_APIS
from google_sheets_apis import googlesheets_apis
from miniture_wati_templates import usermanual_whatsapp, awb_whatsapp
from utils import match_cols
import config

wati = WATI_APIS()
gsheets = googlesheets_apis(spreadsheet_id=config.db_spreadsheet_id)

ops_automation_alarm_contacts = {'Javith': '919698606713', 'Milan': '919445574311',
                                 'Adithya': '919176270768'}



columns_list, column_dict,_ = gsheets.get_column_names(sheet_name=config.db_sheet_name)
fields_to_check = {'usermanual_whatsapp_status', 'usermanual_email_status', 'email_status', 'whatsapp_status'}

def job():
    trackerdf = gsheets.load_sheet_as_csv(sheet_name=config.db_sheet_name)
    trackerdf.fillna('', inplace=True)

    rowcount = 2
    values_to_update = []
    for idx, row in trackerdf.iterrows():
        status = 'Failure'
        empty_fields = set()
        for f in fields_to_check:
            if row[f] == '':
                empty_fields.add(f)


        try:
            id = row['unique_id']
            print('id: ', id)
            name = str(row['name'])
            email = str(row['email_id'])
            sku = str(row['sku'])
            phone_num = str(row['phone_num'])
            invoice = str(row['invoice_number'])
            try:
                product_name, product_manual = get_product_name_manual(sku=sku)
            except:
                product_name, product_manual = '--','--'
            ## awb whatsapp status
            if 'whatsapp_status' in empty_fields:# or row['usermanual_whatsapp_status'] == 'Failure_exception':
                print('entering if loop')
                try:
                    awb = str(int(float(row['awb'])))
                    status = awb_whatsapp(name=name, phone_num=phone_num, wati=wati, awb= awb)
                    values_to_update.append({'col': column_dict['whatsapp_status'],
                                                 'row': rowcount,
                                                 'value': status})
                except:
                    values_to_update.append({'col': column_dict['whatsapp_status'],
                                             'row': rowcount,
                                             'value': 'Failure_exception'})


            ## send manual pdf whatsapp
            if 'usermanual_whatsapp_status' in empty_fields:# or row['usermanual_whatsapp_status'] == 'Failure_exception':
                print('entering if loop')
                print('attempt sending whatsapp for ' + phone_num + '... ')
                try:
                    status = usermanual_whatsapp(sku=sku, product_name=product_name, product_manual=product_manual, name=name,
                                                 phone_num=phone_num, wati=wati)
                    values_to_update.append({'col': column_dict['usermanual_whatsapp_status'],
                                                 'row': rowcount,
                                                 'value': status})
                except:
                    values_to_update.append({'col': column_dict['usermanual_whatsapp_status'],
                                             'row': rowcount,
                                             'value': 'Failure_exception'})

            ##awb email status
            if 'email_status' in empty_fields:
                try:
                    awb = str(int(float(row['awb'])))
                    status = send_dispatch_email(name=name, to_address=email, awb_number=awb)

                    values_to_update.append({'col': column_dict['email_status'],
                                             'row': rowcount,
                                             'value': status})
                except:
                    values_to_update.append({'col': column_dict['email_status'],
                                             'row': rowcount,
                                             'value': 'Failure_exception'})
                    print('email failed: ', traceback.format_exc())

            ##send manual email
            if 'usermanual_email_status' in empty_fields:
                print('attempt sending email to ' + phone_num + '... ')
                try:
                    status = send_usermanual_email(name=name, to_address=email, product_name=product_name,
                                                   product_manual_link=product_manual)

                    values_to_update.append({'col': column_dict['usermanual_email_status'],
                                             'row': rowcount,
                                             'value': status})
                except:
                    values_to_update.append({'col': column_dict['usermanual_email_status'],
                                             'row': rowcount,
                                             'value': 'Failure_exception'})
                    print('email failed: ', traceback.format_exc())
        except:
            print('failed for order id: ', row['unique_id'])
            for e in empty_fields:
                values_to_update.append({'col': column_dict[e],
                                         'row': rowcount,
                                         'value': 'Failure_exception2'})
            print(traceback.format_exc())
        rowcount += 1

    print('values_to_update: ', values_to_update)
    gsheets.update_cell(values_to_update= values_to_update, sheet_name=config.db_sheet_name)

job()
