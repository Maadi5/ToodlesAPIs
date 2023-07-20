import schedule
import os
import time
import pandas as pd
from product_manual_map import get_product_name_manual
import traceback
from email_sender import send_usermanual_email
from wati_apis import WATI_APIS
from google_sheets_apis import googlesheets_apis
from validation_utils import match_cols

wati = WATI_APIS()
gsheets = googlesheets_apis()

columns_list, column_dict = gsheets.get_column_names()

def job():
    trackerdf = gsheets.load_sheet_as_csv()
    bluedart_csv = pd.read_csv(os.path.join(os.getcwd(), 'bluedart_complete.csv'), index_col=False)
    bluedart_approx_csv = pd.read_csv(os.path.join(os.getcwd(), 'approx_delivery_times.csv'), index_col=False)
    trackerdf.fillna('', inplace=True)

    rowcount = 2
    values_to_update = []
    for idx, row in trackerdf.iterrows():
        status = 'Failure'
        try:
            id = row['unique_id']
            print('id: ', id)
            name = str(row['name'])
            email = str(row['email_id'])
            sku = str(row['sku'])
            phone_num = str(row['phone_num'])
            product_name, product_manual = get_product_name_manual(sku=sku)
            try:
                approx_time = list(bluedart_csv[bluedart_csv['Pincode'] == row['pincode']]['TAT'])[0]
                approx_time_in_days = float(approx_time)/24
            except:
                #print('exact pincode code match failed. Taking approx')
                try:
                    if row['city'] in set(bluedart_approx_csv['Location']):
                        approx_time = list(bluedart_approx_csv[bluedart_approx_csv['Location']==row['city']]['Appox_time'])[0]
                        approx_time_in_days = float(approx_time[0])
                    else:
                        approx_time = list(bluedart_approx_csv[bluedart_approx_csv['Location']==row['state']]['Appox_time'])[0]
                        approx_time_in_days = float(approx_time[0])
                except:
                    print('approx time retrieval failed! Assuming')
                    approx_time_in_days = 2
            ##Calculate when to send manual
            try:
                timediff = float(time.time()) - float(row['awb_message_timestamp'])
                timediff_in_days = timediff/(60*60*24)
            except:
                print('time diff calc failed! Assuming')
                timediff_in_days = 1

            ##Time logic on when to send user manuals
            if timediff_in_days>= (approx_time_in_days/2):
                ## send manual pdf whatsapp
                if row['usermanual_whatsapp_status'] == '' or row['usermanual_whatsapp_status'] == 'Failure_exception':
                    print('entering if loop')
                    print('attempt sending whatsapp for ' + phone_num + '... ')
                    try:
                        custom_params=[{'name': 'product_name', 'value': str(product_name)},
                                    {'name': 'media_url', 'value': str(product_manual)}]
                        status = wati.send_template_message(contact_name=name, contact_number= phone_num,
                        template_name='product_instructions_short_manual',custom_params=custom_params)
                        print('Status of whatsapp: ', status)
                        if not status:
                            #trackerdf.at[idx, 'usermanual_whatsapp_status'] = 'Failure'
                            values_to_update.append({'col': column_dict['usermanual_whatsapp_status'],
                                                     'row': rowcount,
                                                     'value': 'Failure'})
                            wa_manual_status = 'Failure'
                        else:
                            #trackerdf.at[idx, 'usermanual_whatsapp_status'] = 'Success'
                            values_to_update.append({'col': column_dict['usermanual_whatsapp_status'],
                                                     'row': rowcount,
                                                     'value': 'Success'})
                            wa_manual_status = 'Success'
                    except:
                        trackerdf.at[idx, 'usermanual_whatsapp_status'] = 'Failure_exception'
                        values_to_update.append({'col': column_dict['usermanual_whatsapp_status'],
                                                 'row': rowcount,
                                                 'value': 'Failure_exception'})
                        wa_manual_status = 'Failure_exception'
                        print('whatsapp usermanual failed: ', traceback.format_exc())

                ##send manual email
                if row['usermanual_email_status'] == '' or row['usermanual_email_status'] == 'Failure_exception':
                    print('attempt sending email to ' + phone_num + '... ')
                    try:
                        status = send_usermanual_email(name= name, to_address= email, product_name=product_name,
                                                    product_manual_link= product_manual)
                        # idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                        trackerdf.at[idx, 'usermanual_email_status'] = status
                        values_to_update.append({'col': column_dict['usermanual_email_status'],
                                                 'row': rowcount,
                                                 'value': status})

                        #email_status = status
                    except:

                        # idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                        trackerdf.at[idx, 'usermanual_email_status'] = 'Failure_exception'
                        values_to_update.append({'col': column_dict['usermanual_email_status'],
                                                 'row': rowcount,
                                                 'value': 'Failure_exception'})
                        #email_status = 'Failure_exception'
                        print('email failed: ', traceback.format_exc())
            # trackerdf.to_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index = False)
        except:
            print('failed for order id: ', row['unique_id'])
            print(traceback.format_exc())
            #trackerdf.to_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index=False)
        rowcount += 1

    print('values_to_update: ', values_to_update)
    gsheets.update_cell(values_to_update= values_to_update)
    print("This is a cron job!")

# Schedule the job to run every day at 3pm (test)
schedule.every().day.at("9:30").do(job)
#
while True:
    schedule.run_pending()
    time.sleep(1)
