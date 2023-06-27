import os 
import json
import pandas as pd 

def get_order_details(df):
    if not os.path.exists(os.path.join(os.getcwd(), 'order_tracker.csv')):
        tracker_df = pd.DataFrame({'unique_id': [], 'name': [], 'phone_num': [], 'email_id': [], 'awb': [], 
                                   'email_status': [], 'whatsapp_status': []})
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
            to_be_pushed.append(dfdict)
            dfdict['email_status'] = ''
            dfdict['whatsapp_status'] = ''
            trackerdf.append(dfdict)
    del df
    to_be_pushed_df = pd.DataFrame(to_be_pushed)
    del to_be_pushed
    tracker_df = pd.DataFrame(trackerdf)
    del trackerdf
    tracker_df.to_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index = False)
    return to_be_pushed_df


        