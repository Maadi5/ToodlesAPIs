import os 
import json
import pandas as pd 

def get_order_details(df):
    if not os.path.exists(os.path.join(os.get_cwd(), 'order_tracker.csv')):
        tracker_df = pd.DataFrame({'unique_id': [''], 'email_status': [''], 'whatsapp_status': []})
    else:
        unique_ids = list(tracker_df['unique_id'])


        