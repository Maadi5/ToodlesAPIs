import schedule
import time
import pandas as pd
from product_manual_map import get_product_name_manual
import traceback
from email_sender import send_usermanual_email
from wati_apis import WATI_APIS
from google_sheets_apis import googlesheets_apis
from utils import match_cols
import config
from miniture_wati_templates import marketing_campaign_wati
import logging
from datetime import datetime

# Get the current year
current_year = datetime.now().year


# crm_sheet_parser = crm_sheet()
wati = WATI_APIS()
gsheets = googlesheets_apis(spreadsheet_id=config.marketing_campaigns_gsheets_id)

community_gsheets = googlesheets_apis(spreadsheet_id=config.community_sheet_id)


columns_list, column_dict,_ = gsheets.get_column_names(sheet_name=config.marketing_all_sheet_name)
# Configure the logger
logging.basicConfig(
    filename='postapi_logs.log',  # Specify the log file name
    level=logging.DEBUG,        # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def phone_number_format(phone):
    phone = phone[1:] if phone[0] == '0' else phone
    phone = phone.replace('-', '')
    phone = ''.join(''.join(phone.split(' ')).split('+'))
    phone = '91' + phone if len(phone) != 12 else phone
    return phone

def epoch_to_dd_mm_yy_time(epoch_timestamp, with_time = True):
    # Convert the epoch timestamp to a datetime object
    date_time_obj = datetime.utcfromtimestamp(epoch_timestamp)

    # Extract the day, month, year, hour, minute, and second components
    day = date_time_obj.strftime('%d')
    month = date_time_obj.strftime('%B')
    year = date_time_obj.strftime('%y')
    hour = date_time_obj.strftime('%H')
    minute = date_time_obj.strftime('%M')
    second = date_time_obj.strftime('%S')

    # Create the formatted date and time string
    if with_time:
        formatted_date_time = f'{day}-{month}-{year}, {hour}:{minute}:{second}'
    else:
        formatted_date_time = f'{day}-{month}-{year}'

    return formatted_date_time

def date_string_to_epoch(date_str):
    # Define a list of possible date formats
    date_formats = ['%d %B %Y', '%d-%b-%Y', '%d %B %Y']

    # Try parsing the date string using each format until one succeeds
    for date_format in date_formats:
        try:
            date_obj = datetime.strptime(date_str, date_format)
            # Convert the datetime object to epoch time (seconds since January 1, 1970)
            epoch_time = int(date_obj.timestamp())
            return epoch_time
        except ValueError:
            pass

    # If none of the formats match, raise an exception or return a default value
    raise ValueError("Invalid date format")

def marketing_campaign_cron():
    marketing_sheet = gsheets.load_sheet_as_csv(sheet_name=config.marketing_all_sheet_name)
    community_members = community_gsheets.load_sheet_as_csv(sheet_name='Sheet7')
    number_lists = {'community_members': []}
    for idx, row in community_members.iterrows():
        if str(row['Valid']).lower() == 'yes':
            name = str(row['Name'])
            phone_num = str(row['Number'])
            phone_num = phone_number_format(phone=phone_num)
            number_lists['community_members'].append(phone_num)
    print('number list: ', number_lists)


    marketing_sheet.fillna('', inplace = True)
    values_to_update = []
    rowcount = 2
    for idx, row in marketing_sheet.iterrows():
        try:
            print('idx: ', idx, ' row: ', rowcount)
            try:
                print('Template: ', row['WATI template'])
            except:
                pass
            date = row['Date']
            timeval = row['Time']
            status = row['Sent?']
            template_name = row['WATI template']
            skus = str(row['SKU'])
            sku_payload = None

            if skus != '':
                sku_payload = skus.split(',')
            print('Status: ', status)

            sku_payload = ['non-community']

            # Define the date and time as a string
            date_time_str = f'{date} {timeval}'

            # Parse the date and time string into a datetime object
            date_time_obj = datetime.strptime(date_time_str, '%m/%d/%Y %I:%M %p')

            # Convert the datetime object to an epoch timestamp (seconds since January 1, 1970)
            epoch_timestamp = int(date_time_obj.timestamp()) - (5.5*3600)

            #Provide a 10-12 hour timeframe to send message
            # if True:
            if (epoch_timestamp-1600)< time.time()<= (epoch_timestamp+1600) and status =='FALSE':
                print('Trigger campaign function')
                status_response = marketing_campaign_wati(wati=wati, template=template_name, skus=sku_payload,
                                                          number_lists=number_lists)
                values_to_update.append({'col': column_dict['Sent?'],
                                                     'row': rowcount,
                                                     'value': status_response})
            print(epoch_timestamp, time.time())
        except:
            print('FAILED AT ROW: ', rowcount)
            print(traceback.format_exc())
        rowcount += 1



    gsheets.update_cell(values_to_update=values_to_update, sheet_name=config.marketing_all_sheet_name)
    print('Cron finished running at: ', epoch_to_dd_mm_yy_time(time.time()))


all_times = []

every_n_hours = 1

starting_epoch = time.time()

for idx, val in enumerate(range(0,24)):
    if val%every_n_hours == 0:
        date_time_obj = datetime.utcfromtimestamp(starting_epoch + 3600*val+ 60)
        hour = date_time_obj.strftime('%H')
        minute = date_time_obj.strftime('%M')
        all_times.append(hour + ':' + minute)

# # Schedule the job to run every day at 3pm (test)
# for time_str in all_times:
#     schedule.every().day.at(time_str).do(marketing_campaign_cron)
#
# print(all_times)
# print('running cron...')
# while True:
#     try:
#         schedule.run_pending()
#         time.sleep(1)
#     except:
#         pass

marketing_campaign_cron()
