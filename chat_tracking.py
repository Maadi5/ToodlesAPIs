import os
import traceback
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
        print('Sheet names: ', sheet_names)
        phone_num = payload['phone_num']
        timestamp = payload['timestamp']
        name = payload['name']
        time = epoch_to_dd_mm_yy_time(timestamp)
        message = payload['message']

        if phone_num not in sheet_names:
            self.gsheets.add_new_sheet(new_sheet_name=phone_num)
            self.gsheets.append_csv_to_google_sheets(csv_path=os.path.join(os.getcwd(), 'temp_new_df.csv'), sheet_name=phone_num)

        ##Check if messsage is repeating
        current_sheet  = self.gsheets.load_sheet_as_csv(sheet_name=phone_num)
        already_exists = self.check_if_already_exists(originaldf=current_sheet, payload={'Message': message, 'Timestamp': timestamp})

        if not already_exists:
            get_prev_chat = self.get_previous_chat_chunk(name=name, phone_num= phone_num, n=6, include_latest=True)
            print('previous chats: ', get_prev_chat)
            try:
                last_message = list(current_sheet['Message'])[-1]
                last_timestamp = list(current_sheet['Timestamp'])[-1]
            except:
                last_message = ''
                last_timestamp = ''
            new_chats = []
            start_collecting = False
            for chat in get_prev_chat:
                if chat['Message'] == last_message and chat['Timestamp'] == last_timestamp:
                    start_collecting = True
                check_if_already_exists_in_sheet = self.check_if_already_exists(originaldf=current_sheet, payload=chat)
                check_if_already_exists_in_list = self.check_if_already_exists(originaldf=new_chats, payload=chat)

                if start_collecting and not check_if_already_exists_in_sheet and not check_if_already_exists_in_list:
                    new_chats.append(chat)

            if new_chats == []:
                for i in reversed(range(len(get_prev_chat))):
                    if 'user' not in get_prev_chat[i]['From'].lower():
                        if not self.check_if_already_exists(originaldf=current_sheet, payload=get_prev_chat[i]) and not self.check_if_already_exists(originaldf=new_chats, payload=get_prev_chat[i]):
                            new_chats.append(get_prev_chat[i])
                    else:
                        break
                new_chats.reverse()

            # get_prev_chat.append({'From': 'User: ' + name, 'Message': message, 'Time': time, 'Timestamp': timestamp})
            get_prev_chat = sorted(get_prev_chat, key=lambda x:x['Timestamp'])
            add_df = pd.DataFrame(get_prev_chat)
            add_df.to_csv(self.add_to_csv_path, index=False)
            self.gsheets.append_csv_to_google_sheets(csv_path=self.add_to_csv_path, sheet_name=phone_num)


    def check_if_already_exists(self, originaldf, payload):
        exists = False
        try:
            if str(type(originaldf)) == "<class 'pandas.core.frame.DataFrame'>":
                for idx, row in originaldf.iterrows():
                    # print('row: ', row)
                    if row['Message'] == payload['Message'] and row['Timestamp'] == str(payload['Timestamp']):
                        print("message exists: ", payload['Message'])
                        exists = True
                        break
            elif type(originaldf) == list:
                for idx, row in enumerate(originaldf):
                    # print('row: ', row)
                    if row['Message'] == payload['Message'] and row['Timestamp'] == str(payload['Timestamp']):
                        print("message exists: ", payload['Message'])
                        exists = True
                        break
        except:
            pass
        return exists


    def update_chats(self):
        sheet_names = self.gsheets.get_sheet_names()
        for phone_num in sheet_names:
            current_sheet = self.gsheets.load_sheet_as_csv(sheet_name=phone_num)
            name = ''
            try:
                for n in list(current_sheet['From']):
                    if 'user' in n.lower():
                        name = n.split(':')[1][1:] if n.split(':')[1][0] == ' ' else n.split(':')[1]
                        break
            except:
                name = None

            if name is not None:
                try:
                    get_prev_chat = self.get_previous_chat_chunk(name=name, phone_num=phone_num, n=25, include_latest=True)
                except:
                    get_prev_chat = []
                print('previous chats: ', get_prev_chat)
                try:
                    last_message = list(current_sheet['Message'])[-1]
                    last_timestamp = list(current_sheet['Timestamp'])[-1]
                except:
                    last_message = ''
                    last_timestamp = ''
                new_chats = []
                start_collecting = False
                for chat in get_prev_chat:
                    check_if_already_exists_in_sheet = self.check_if_already_exists(originaldf=current_sheet,
                                                                                    payload=chat)
                    check_if_already_exists_in_list = self.check_if_already_exists(originaldf=new_chats, payload=chat)
                    if start_collecting and not check_if_already_exists_in_sheet and not check_if_already_exists_in_list:
                        new_chats.append(chat)
                    if chat['Message'] == last_message and chat['Timestamp'] == last_timestamp:
                        start_collecting = True
                if new_chats == []:
                    try:
                        for i in reversed(range(len(get_prev_chat))):
                            if 'user' not in get_prev_chat[i]['From'].lower():
                                if not self.check_if_already_exists(originaldf=current_sheet, payload=get_prev_chat[i]) and not self.check_if_already_exists(originaldf=new_chats, payload=get_prev_chat[i]):
                                    new_chats.append(get_prev_chat[i])
                            else:
                                break
                        new_chats.reverse()
                    except:
                        pass

                # get_prev_chat.append({'From': 'User: ' + name, 'Message': message, 'Time': time, 'Timestamp': timestamp})
                add_df = pd.DataFrame(get_prev_chat)
                add_df.to_csv(self.add_to_csv_path, index=False)
                self.gsheets.append_csv_to_google_sheets(csv_path=self.add_to_csv_path, sheet_name=phone_num)
                self.gsheets.sort_all_sheets()

    def get_previous_chat_chunk(self, name, phone_num, n=5, include_latest = False):
        chat_history_payload = self.wati.get_previous_n_chats(contact_number= phone_num, n=n)
        message_items = chat_history_payload['messages']['items']
        chat_interactions = []
        chat_track = 0
        # print('message_items: ', message_items)
        if include_latest == False:
            messagelist = message_items[1:]
        else:
            messagelist = message_items
        for item in messagelist:
            if item['eventType'] == 'ticket':
                    wati_time = item['created']
                    timestamp = wati_date_to_epoch(wati_time)
                    time = epoch_to_dd_mm_yy_time(timestamp)
                    chat_interactions.append(
                        {chat_track: {'From': item['actor'], 'Message': item['eventDescription'], 'Time': time, 'Timestamp': timestamp}})

            elif item['eventType'] == 'message':
                if item['owner'] == True:
                    from_person = 'Admin'
                else:
                    from_person = 'User: ' + name
                timestamp = float(item['timestamp'])
                time = epoch_to_dd_mm_yy_time(timestamp)
                chat_interactions.append({chat_track: {'From': from_person, 'Message': item['text'], 'Time': time, 'Timestamp': timestamp}})
                # elif item['owner'] == False:
                #     break
            chat_track += 1
        try:
            chat_interactions = sorted(chat_interactions, key=lambda x: list(x.keys())[0], reverse=True)
        except:
            traceback.format_exc()
        print('chat interactions: ', chat_interactions)
        chat_interactions_list = []
        for val in chat_interactions:
            print('val: ', val)
            print('val.items(): ', val.items())
            chat_interactions_list.append(list(val.items())[0][1])
        return chat_interactions_list

    def chat_manager_cron(self):
        gsheets = googlesheets_apis(spreadsheet_id=config.chats_spreadsheet_id)
        sheet_names = self.gsheets.get_sheet_names()
        for s in sheet_names:
            try:
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
                                   'Suggested Context': 'Message: ' + message + '\nTime left to reply(hours): ' + str(round(24-time_since_message,2)) + '\nTime of message: ' + str(time_of_message),
                                   'Alert Type': 'Reply delay'}
                        self.crm.add_alert_to_sheet(payload=payload, sla_value= round(24-time_since_message,2))
                elif 'has been closed' in list(sheet_df['Message'])[-1].lower():
                    gsheets.remove_sheet(phone_num)
            except:
                print(s, ': processing failed.')
if __name__ == '__main__':
    chats = chat_tracker()

    # chats.chat_manager_cron()
    # chats.get_previous_chat_chunk(phone_num='919176270768')
    # chats.update_chats()
    chats.add_chat(payload={'name': 'M A Adithya', 'phone_num': '919176270768',
                            'timestamp': time.time(), 'message': 'This is a test message'})









