import os

from google_sheets_apis import googlesheets_apis
import config
import pandas as pd
from utils import epoch_to_dd_mm_yy_time, wati_date_to_epoch
import time
from crm_sheet_mgr import crm_sheet
from wati_apis import WATI_APIS
class chat_tracker():
    def __init__(self):
        self.gsheets = googlesheets_apis(spreadsheet_id=config.chats_spreadsheet_id)
        self.tempdf_new = pd.DataFrame([{'From': 'NEWCHAT', 'Message': 'NEWCHAT', 'Time': 'NEWCHAT', 'Timestamp': 'NEWCHAT'}])
        self.tempdf_new.to_csv(os.path.join(os.getcwd(), 'temp_new_df.csv'), index=False)
        self.add_to_csv_path = os.path.join(os.getcwd(), 'tempdf.csv')
        self.crm = crm_sheet()
        self.wati = WATI_APIS()

    def add_chat(self, payload):
        sheet_names = self.gsheets.get_sheet_names()
        phone_num = payload['phone_num']
        timestamp = payload['timestamp']
        name = payload['name']
        time = epoch_to_dd_mm_yy_time(timestamp)
        message = payload['message']
        if phone_num not in sheet_names:
            self.gsheets.add_new_sheet(new_sheet_name=phone_num)
            self.gsheets.append_csv_to_google_sheets(csv_path=os.path.join(os.getcwd(), 'temp_new_df.csv'))
        get_prev_chat = self.get_previous_chat_chunk(phone_num= phone_num, n=10)
        get_prev_chat.append({'From': 'User: ' + name, 'Message': message, 'Time': time, 'Timestamp': timestamp})
        add_df = pd.DataFrame(get_prev_chat)
        add_df.to_csv(self.add_to_csv_path)
        self.gsheets.append_csv_to_google_sheets(csv_path=self.add_to_csv_path, sheet_name=phone_num)


    def get_previous_chat_chunk(self, phone_num, n=5):
        chat_history_payload = self.wati.get_previous_n_chats(phone_num= phone_num, n=n)
        message_items = chat_history_payload['messages']['items']
        chat_interactions = []
        chat_track = 0
        for item in message_items:
            if item['eventType'] == 'ticket':
                    wati_time = item['created']
                    timestamp = wati_date_to_epoch(wati_time)
                    time = epoch_to_dd_mm_yy_time(timestamp)
                    chat_interactions.append(
                        {chat_track: {'From': item['actor'], 'Message': item['eventDescription'], 'Time': time, 'Timestamp': timestamp}})

            elif item['eventType'] == 'message':
                if item['owner'] == True:
                    timestamp = float(item['timestamp'])
                    time = epoch_to_dd_mm_yy_time(timestamp)
                    chat_interactions.append({chat_track: {'From': 'Admin', 'Message': item['text'], 'Time': time, 'Timestamp': timestamp}})
                elif item['owner'] == False:
                    break
            chat_track += 1
        chat_interactions = sorted(chat_interactions, key=lambda x: x[0], reverse=True)
        chat_interactions_list = []
        for val in chat_interactions:
            chat_interactions_list.append(list(val.items())[1])
        return chat_interactions_list

    def chat_manager_cron(self):
        gsheets = googlesheets_apis(spreadsheet_id=config.chats_spreadsheet_id)
        sheet_names = self.gsheets.get_sheet_names()


        for s in sheet_names:
            sheet_df = gsheets.load_sheet_as_csv(sheet_name=s)
            phone_num = s
            current_time = time.time()
            if 'User' in list(sheet_df['From'])[-1]:
                message = list(sheet_df['Message'])[-1]
                timestamp = float(list(sheet_df['Timestamp'])[-1])
                if (current_time-timestamp)>= (10*3600):
                    time_since_message = round((current_time-timestamp)/3600, 1)
                    time_of_message = list(sheet_df['Time'])[-1]
                    #Add alarm to crm
                    name = list(sheet_df['From'])[-1].split('User: ')[1]
                    payload = {'Name': name,
                               'Number': phone_num,
                               'Suggested Context': 'Message: ' + message + '\nTime left to reply(hours): ' + 24-time_since_message + '\nTime of message: ' + time_of_message,
                               'Alert Type': 'Reply delay'}
                    self.crm.add_alert_to_sheet(payload=payload, sla_value= float(24-time_since_message - 10))
            elif 'has been closed' in list(sheet_df['Message'])[-1].lower():
                gsheets.remove_sheet(phone_num)








