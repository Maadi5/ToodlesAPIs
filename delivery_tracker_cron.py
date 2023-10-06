import schedule
import os
import time
import pandas as pd
from product_manual_map import get_product_name_manual
import traceback
from email_sender import send_usermanual_email
from wati_apis import WATI_APIS
from google_sheets_apis import googlesheets_apis
from utils import match_cols
import config
from datetime import datetime
from bluedart_apis import bluedart_apis
from crm_sheet_mgr import crm_sheet
from miniture_wati_templates import delivery_reminder_whatsapp, usermanual_whatsapp, delivery_delay_whatsapp
import logging

from utils import epoch_to_dd_mm_yy_time, date_string_to_epoch, date_str_to_epoch2

crm_sheet_parser = crm_sheet()

# Configure the logger
logging.basicConfig(
    filename='postapi_logs.log',  # Specify the log file name
    level=logging.DEBUG,        # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

from datetime import datetime

# def create_cust_sheet_payload()
# WOO/FY24-0259
# FRC/FY24-0057
# SFY/FY24-0048
def invoice_number_to_platform(invoice_number):
    platform = 'Not found'
    if 'SFY' in invoice_number:
        platform = 'Shopify'
    elif 'WOO' in invoice_number:
        platform = 'Woocommerce'
    elif 'FRC' in invoice_number:
        platform = 'FirstCry'
    elif 'PEP' in invoice_number:
        platform = 'Pepperfry'

    return platform

def tracking_logic_CTA(old_tracking_code_update, order_date_epoch, bluedart_statustype, delivery_est_epoch, delivery_update_message,
                       shipping_mode, delivery_delay_push, promised_date_epoch,
                       standard_daygap_wati = 5, express_daygap_wati = 2, first_time_data = False):
    actions = {'update values': False, 'usermanual2 push': False, 'order pickup delay alarm': False,
               'delivery update push': False, 'delivery delay alarm': False, 'delivery delay push': False}
    if first_time_data:
        actions['update values'] = True
    current_time = float(time.time())
    ediff_from_order_date = current_time - order_date_epoch
    days_from_order_date = (ediff_from_order_date / (3600 * 24))

    try:
        ediff_del_est_minus_current = delivery_est_epoch - current_time
        days_del_est_minus_current = (ediff_del_est_minus_current / (3600 * 24))
    except:
        ediff_del_est_minus_current = ''
        days_del_est_minus_current = ''

    if bluedart_statustype == 'DL':
        if (current_time - delivery_est_epoch)<= (3600*24) and old_tracking_code_update != 'DL':
            actions['usermanual2 push'] = True
        actions['update values'] = True
    elif bluedart_statustype == 'PU':
        if days_from_order_date>=2:
            actions['order pickup delay alarm'] = True
            actions['update values'] = True
    # elif bluedart_statustype == 'UD':
    #     actions['delivery delay alarm'] = True
    else:
        if delivery_update_message != 'Success':
            if (shipping_mode == 'standard' and days_from_order_date>= standard_daygap_wati)\
                    or  (shipping_mode == 'express' and days_from_order_date>= express_daygap_wati)\
                    or 0.5<days_del_est_minus_current<=1:
                actions['delivery update push'] = True
                actions['update values'] = True

        if delivery_delay_push != 'Success' and days_del_est_minus_current<=0:
            actions['delivery delay push'] = True
            actions['update values'] = True
            if days_del_est_minus_current<=-0.5 or current_time>= promised_date_epoch:
                actions['delivery delay alarm'] = True

    if actions['delivery delay push'] == True:
        actions['delivery update push'] = False

    return actions






wati = WATI_APIS()
gsheets = googlesheets_apis(spreadsheet_id=config.db_spreadsheet_id)

def mark_row_as_skipped(row_number, column_dict, message = 'Skipped'):
    return [{'col': column_dict['tracking_code_update'],
                                                 'row': row_number,
                                                 'value': message},
                                                 {'col': column_dict['tracking_status_update'],
                                                  'row': row_number,
                                                  'value': message},
                                                 {'col': column_dict['tracking_est_update'],
                                                  'row': row_number,
                                                  'value': message},
                                                 {'col': column_dict['last_tracked_time'],
                                                  'row': row_number,
                                                  'value': message},
                                                 {'col': column_dict['usermanual_during_delivery_whatsapp'],
                                                  'row': row_number,
                                                  'value': message},
                                                 {'col': column_dict['delivery_update_message'],
                                                  'row': row_number,
                                                  'value': message},
                                                 {'col': column_dict['delivery_delay_message'],
                                                  'row': row_number,
                                                  'value': message}
                                                 ]

columns_list, column_dict,_ = gsheets.get_column_names(sheet_name=config.db_sheet_name)
bluedart = bluedart_apis()

day_thresh_standard = 8
day_thresh_express = 4


def time_difference_to_track(last_tracked_time, time_diff_hours = .002):
    current_time = time.time()
    track = False
    if current_time - last_tracked_time>= time_diff_hours*(3600):
        track = True
    return track

def bluedart_tracking_checker():
    trackerdf = gsheets.load_sheet_as_csv(sheet_name=config.db_sheet_name)
    #bluedart_csv = pd.read_csv(os.path.join(os.getcwd(), 'bluedart_complete.csv'), index_col=False)
    #bluedart_approx_csv = pd.read_csv(os.path.join(os.getcwd(), 'approx_delivery_times.csv'), index_col=False)
    trackerdf.fillna('', inplace=True)

    rowcount = 2
    values_to_update = []

    idx_to_cind = {}
    count = 0
    for idx, row in trackerdf.iterrows():
        idx_to_cind[idx] = count
        count += 1

    try:
        for idx, row in trackerdf.iterrows():
            # status = 'Failure'
            try:
                status = str(row['status'])
                awb = str(row['status'])
                #Code to skip 'processing' or 'cancelled' orders
                if status in {'cancelled', 'processing'}:
                    skip_values = mark_row_as_skipped(row_number=rowcount, column_dict=column_dict)
                    values_to_update.extend(skip_values)
                #Run pipeline
                else:
                    id = str(row['unique_id'])
                    if id == '9999999999':
                        print('checkpoint')
                    sku = str(row['sku'])
                    awb = str(row['awb'])
                    name = str(row['name'])
                    #Temporarily put my number
                    phone_num = '919176270768' #str(row['phone_num'])
                    invoice_number = str(row['invoice_number'])
                    platform = invoice_number_to_platform(invoice_number)
                    channel_order_num = str(row['channel_order_number'])
                    tracking_code_update = str(row['tracking_code_update'])
                    tracking_status_update = str(row['tracking_status_update'])
                    tracking_est_update = str(row['tracking_est_update'])
                    last_tracked_time = str(row['last_tracked_time'])
                    try:
                        last_tracked_epoch = date_str_to_epoch2(last_tracked_time)
                        last_tracked_epoch_gmt = last_tracked_epoch - 19800
                    except:
                        last_tracked_epoch_gmt = ''

                    try:
                        est_date_epoch = date_string_to_epoch(tracking_est_update)
                    except:
                        est_date_epoch = ''
                    delivery_update_message = str(row['delivery_update_message'])
                    delivery_delay_message = str(row['delivery_delay_message'])
                    usermanual_during_delivery_whatsapp = str(row['usermanual_during_delivery_whatsapp'])
                    usermanual_during_delivery_email = str(row['usermanual_during_delivery_email'])
                    payload_to_add = {'Order Number': channel_order_num,
                                      'Platform': platform,
                                      'Name': name,
                                      'Number': phone_num,
                                      }
                    order_date = str(row['order_date'])
                    print('id: ', id)
                    shipping_mode = str(row['shipping_mode'])

                    if shipping_mode == '':
                        rowcount += 1
                        continue

                    old_tracking_code_update = tracking_code_update

                    indexes = trackerdf.index[trackerdf['awb'] == awb].tolist()
                    cinds = [idx_to_cind[val] for val in indexes]

                    product_list = {}
                    # indexes = []
                    for ind in cinds:
                        sku = trackerdf.at[ind, 'sku']
                        try:
                            product_name, product_manual = get_product_name_manual(sku=sku)
                            product_list[product_name] = product_manual
                        except:
                            pass
                    valid_products = False
                    if product_list != {}:
                        valid_products = True
                    order_date_epoch = ''
                    try:
                        order_date_epoch = date_string_to_epoch(order_date)
                    except:
                        logging.error('epoch to date convert error')
                        logging.error(traceback.format_exc())

                    first_time = False
                    tracking_failed = False
                    if tracking_code_update != 'DL':

                        should_track_again = True
                        try:
                            should_track_again = time_difference_to_track(last_tracked_time= last_tracked_epoch_gmt)
                        except:
                            pass
                        if should_track_again:
                            if tracking_code_update == '':
                                first_time = True
                            try:
                                tracking_status = bluedart.get_tracking_details(awb)
                                tracking_status_update = tracking_status['Status']
                                tracking_code_update = tracking_status['StatusType']
                                if 'ExpectedDeliveryDate' in tracking_status:
                                    tracking_est_update = tracking_status['ExpectedDeliveryDate']
                                    est_date_epoch = date_string_to_epoch(tracking_est_update)
                                else:
                                    tracking_est_update = 'NA'
                                    est_date_epoch = ''
                            except:
                                tracking_failed = True
                                tracking_status_update = 'bluedart failed'
                                tracking_code_update = 'bluedart failed'
                                tracking_est_update = 'bluedart failed'
                                est_date_epoch = 'bluedart failed'
                        else:
                            print('skipped tracking id: ', id)
                            rowcount +=1
                            continue
                    ##Promised date check
                    promised_hard_date = 'promised date'
                    if shipping_mode == 'standard':
                        try:
                            promised_date_epoch = float(order_date_epoch) + (day_thresh_standard*24*3600)
                        except:
                            promised_date_epoch = ''
                        promised_hard_date = epoch_to_dd_mm_yy_time(int(promised_date_epoch), with_time=False)
                    elif shipping_mode == 'express':
                        try:
                            promised_date_epoch = float(order_date_epoch) + (day_thresh_express*24*3600)
                        except:
                            promised_date_epoch = ''
                        promised_hard_date = epoch_to_dd_mm_yy_time(int(promised_date_epoch), with_time=False)

                    if not tracking_failed:
                        try:
                            actions = tracking_logic_CTA(old_tracking_code_update=old_tracking_code_update,order_date_epoch=order_date_epoch, bluedart_statustype=tracking_code_update,
                                               delivery_est_epoch=est_date_epoch, delivery_update_message=delivery_update_message,
                                   shipping_mode=shipping_mode, delivery_delay_push=delivery_delay_message, promised_date_epoch=promised_date_epoch,
                                                         first_time_data=first_time)
                        except:
                            skip_values = mark_row_as_skipped(row_number=rowcount, column_dict=column_dict, message = 'track logic failed')
                            values_to_update.extend(skip_values)

                        '''
                            actions = {'update values': False, 'usermanual2 push': False, 'order pickup delay alarm': False,
                       'delivery update push': False, 'delivery delay alarm': False, 'delivery delay push': False}
                        '''
                        if actions['update values'] == False:
                            rowcount +=1
                            continue
                        else:
                            #Delivery message
                            if actions['usermanual2 push'] and (usermanual_during_delivery_whatsapp != 'Success' and usermanual_during_delivery_whatsapp != 'NA'):
                                count = 0
                                for product_name, product_manual in product_list.items():
                                    status = usermanual_whatsapp(sku=sku, product_name=product_name,
                                                                 product_manual=product_manual, name=name,phone_num=phone_num, wati=wati)
                                    values_to_update.append({'col': column_dict['usermanual_during_delivery_whatsapp'],
                                                         'row': cinds[count] + 2,
                                                         'value': status})
                                    count += 1
                                gsheets.update_cell(values_to_update=values_to_update, sheet_name=config.db_sheet_name)
                                values_to_update = []
                            else:
                                if usermanual_during_delivery_whatsapp != 'Success' and usermanual_during_delivery_whatsapp != 'NA':
                                    status = 'Not Sent'
                                    values_to_update.append({'col': column_dict['usermanual_during_delivery_whatsapp'],
                                                             'row': rowcount,
                                                             'value': status})

                            #delivery update
                            if actions['delivery update push'] and (delivery_update_message != 'Success' and delivery_update_message != 'NA'):
                                status = delivery_reminder_whatsapp(name=name, products= ', '.join(list(product_list)),
                                                                    phone_num=phone_num, delivery_date=tracking_est_update, wati=wati)
                                values_to_update.append({'col': column_dict['delivery_update_message'],
                                                         'row': rowcount,
                                                         'value': status})
                                gsheets.update_cell(values_to_update=values_to_update, sheet_name=config.db_sheet_name)
                                values_to_update = []
                            else:
                                if delivery_update_message != 'Success' and delivery_update_message != 'NA':
                                    status = 'Not Sent'
                                    values_to_update.append({'col': column_dict['delivery_update_message'],
                                                             'row': rowcount,
                                                             'value': status})

                            if actions['delivery delay push'] and (delivery_delay_message != 'Success' and delivery_delay_message != 'NA'):
                                status = delivery_delay_whatsapp(name=name, phone_num=phone_num,
                                                                 products= ', '.join(list(product_list)), wati= wati)
                                values_to_update.append({'col': column_dict['delivery_delay_message'],
                                                         'row': rowcount,
                                                         'value': status})
                                gsheets.update_cell(values_to_update=values_to_update, sheet_name=config.db_sheet_name)
                                values_to_update = []
                            else:
                                if delivery_delay_message != 'Success' and delivery_delay_message != 'NA':
                                    status = 'Not Sent'
                                    values_to_update.append({'col': column_dict['delivery_delay_message'],
                                                             'row': rowcount,
                                                             'value': status})


                            if actions['delivery delay alarm']:
                                delivery_delay_payload = payload_to_add
                                delivery_delay_payload['Suggested Context'] = 'Promised hard date: ' + promised_hard_date + '\nEstimated date: ' + tracking_est_update + '\nDelivery Status: ' + tracking_status_update \
                                                     + '\nDelivery update message: ' + delivery_update_message + '\nDelivery delay message: ' + delivery_delay_message
                                delivery_delay_payload['Alert Type'] = 'Delivery delay'
                                crm_sheet_parser.add_alert_to_sheet(payload=delivery_delay_payload)
                            if actions['order pickup delay alarm']:
                                pickup_delay_alarm = payload_to_add
                                pickup_delay_alarm['Suggested Context'] = 'Order date: ' + order_date + '\nShipping mode: ' + shipping_mode + '\nDelivery Status: ' + tracking_status_update
                                pickup_delay_alarm['Alert Type'] = 'Pickup delay'
                                crm_sheet_parser.add_alert_to_sheet(payload=pickup_delay_alarm)


                            values_to_update.extend([{'col': column_dict['tracking_code_update'],
                                                     'row': rowcount,
                                                     'value': tracking_code_update},
                                                     {'col': column_dict['tracking_status_update'],
                                                      'row': rowcount,
                                                      'value': tracking_status_update},
                                                     {'col': column_dict['tracking_est_update'],
                                                      'row': rowcount,
                                                      'value': tracking_est_update},
                                                     {'col': column_dict['last_tracked_time'],
                                                      'row': rowcount,
                                                      'value': epoch_to_dd_mm_yy_time(int(time.time())+19800)}
                                                     ])
                    else:
                        skip_values = mark_row_as_skipped(row_number=rowcount, column_dict=column_dict, message='tracking api failed')
                        values_to_update.extend(skip_values)


            except:
                print('Exception at checking tracking')
                skip_values = mark_row_as_skipped(row_number=rowcount, column_dict=column_dict,
                                                  message='Loop failed')
                values_to_update.extend(skip_values)
                logging.error('Failed at iteration of eta checker')
                logging.error(traceback.format_exc())
            rowcount += 1

        print('values_to_update: ', values_to_update)
        gsheets.update_cell(values_to_update=values_to_update, sheet_name=config.db_sheet_name)
        print("This is a cron job!")

    except:
        logging.error('bluedart checker script failed')
        logging.error(traceback.format_exc())

    # print('values_to_update: ', values_to_update)
    gsheets.update_cell(values_to_update= values_to_update, sheet_name=config.db_sheet_name)
    print('Cron finished running at: ', epoch_to_dd_mm_yy_time(time.time()))

##Run every n hour

starting_epoch = time.time()

all_times = []

every_n_hours = 3

for idx, val in enumerate(range(0,24)):
    if val%every_n_hours == 0:
        date_time_obj = datetime.utcfromtimestamp(starting_epoch + 3600*val + 60)
        hour = date_time_obj.strftime('%H')
        minute = date_time_obj.strftime('%M')
        all_times.append(hour + ':' + minute)


times_to_run = all_times

print(times_to_run)
## Schedule the job to run every day at 3pm (test)
for time_str in times_to_run:
    schedule.every().day.at(time_str).do(bluedart_tracking_checker)
    break
#
print('running cron...')
while True:
    schedule.run_pending()
    time.sleep(1)

# bluedart_tracking_checker()