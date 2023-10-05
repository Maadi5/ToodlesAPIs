from crm_sheet_mgr import crm_sheet
import os
from datetime import datetime
import schedule
import time

crm_cron = crm_sheet()

all_times = []

every_n_hours = 1

starting_epoch = time.time()

for idx, val in enumerate(range(0,24)):
    if val%every_n_hours == 0:
        date_time_obj = datetime.utcfromtimestamp(starting_epoch + 3600*val+ 60)
        hour = date_time_obj.strftime('%H')
        minute = date_time_obj.strftime('%M')
        all_times.append(hour + ':' + minute)



print(all_times)
# Schedule the job to run every day at 3pm (test)
for time_str in all_times:
    schedule.every().day.at(time_str).do(crm_cron.sheet_mgr_cron_job)
#
print('running cron...')
while True:
    schedule.run_pending()
    time.sleep(1)

# crm_cron.sheet_mgr_cron_job


