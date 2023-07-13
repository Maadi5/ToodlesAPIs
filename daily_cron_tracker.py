import schedule
import time
import pandas as pd
from product_manual_map import get_product_name_manual

def job():
    trackerdf = pd.read_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index_col=False)
    trackerdf.fillna('', inplace=True)
    for idx, row in trackerdf.iterrows():
        if row['usermanual_whatsapp_status'] == '' or row['usermanual_whatsapp_status'] == 'Failure_exception':
            timestamp_of_dispatch = row['awb_message_timestamp']
            try:
                approx_time = list(bluedart_csv[bluedart_csv['Pincode'] == row['pincode']]['TAT'])[0]
                approx_time_in_days = float(approx_time)/24
            except:
                print('exact pincode code match failed. Taking approx')
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
                try:  
                    custom_params=[{'name': 'product_name', 'value': str(product_name)},
                                {'name': 'media_url', 'value': str(product_manual)}]
                    status = wati.send_template_message(contact_name=name, contact_number= phone_num, 
                    template_name='product_instructions_short_manual',custom_params=custom_params)
                    if not status:
                        trackerdf[trackerdf['unique_id'] == row['unique_id']]['usermanual_whatsapp_status'] = 'Failure'
                        wa_manual_status = 'Failure'
                    else:
                        trackerdf[trackerdf['unique_id'] == row['unique_id']]['usermanual_whatsapp_status'] = 'Success'
                        wa_manual_status = 'Success'
                except:
                    trackerdf[trackerdf['unique_id'] == row['unique_id']]['usermanual_whatsapp_status'] = 'Failure_exception'
                    wa_manual_status = 'Failure_exception'
                    print('whatsapp usermanual failed: ', traceback.format_exc())
                
            ##send manual email
            if row['usermanual_email_status'] == '' or row['usermanual_email_status'] == 'Failure_exception':
                try:
                    sku = row['sku']
                    product_name, product_manual = get_product_name_manual(sku=sku)
                    status = send_usermanual_email(name= name, to_address= email, product_name=product_name, 
                                                product_manual_link= product_manual)
                    idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                    trackerdf.at[idx, 'usermanual_email_status'] = status
                    email_status = status
                except:
                    idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                    trackerdf.at[idx, 'usermanual_email_status'] = 'Failure_exception'
                    email_status = 'Failure_exception'
                    print('email failed: ', traceback.format_exc())

    print("This is a cron job!")

# Schedule the job to run every day at 8:00 AM
schedule.every().day.at("17:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
