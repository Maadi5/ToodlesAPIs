import os
import json
from google_sheets_apis import googlesheets_apis
import traceback
from wati_apis import WATI_APIS
import pandas as pd
import config
from utils import epoch_to_dd_mm_yy_time
import time
from miniture_wati_templates import delivery_delay_alarm_message, chat_revive_message

class crm_sheet():
    def __init__(self):
        self.wati = WATI_APIS()
        self.gsheets = googlesheets_apis(spreadsheet_id=config.crm_spreadsheet_id)
        self.columns_list, self.column_dict, self.col_index = self.gsheets.get_column_names(sheet_name=config.crm_open_sheet_name)
        # self.col_list =
        self.update_csv_path = os.path.join(os.getcwd(), 'update_csv_temp.csv')
        self.dropdown_payload = {
        "condition": {
            "type": "ONE_OF_LIST",
            "values": [{'userEnteredValue': 'Resolved'}, {'userEnteredValue': 'Delay by 2 hours'}]
        },
        "showCustomUi": True
        }
        self.dropdown_payload_chat = {
        "condition": {
            "type": "ONE_OF_LIST",
            "values": [{'userEnteredValue': 'Revive chat'}]
        },
        "showCustomUi": True
        }
        self.crm_alarm_contacts = {'Javith': '919698606713', 'Milan': '919445574311',
                                 'Sanaa': '919731011565', 'Adithya': '919176270768'}
        self.wati = WATI_APIS()
        self.alert_types = ['Delivery delay', 'Query reply SLA']
        self.tempdf_to_closed_path = os.path.join(os.getcwd(), 'tempdf_to_closed.csv')


    def check_recurrance_ops_ticket(self, opendf, closeddf, order_number, alert):
        newdf = pd.concat([opendf, closeddf])
        already_exists = False
        for idx, row in newdf.iterrows():
            if row['Order Number'] == order_number and row['Alert Type'] == alert:
                already_exists = True
        return already_exists

    def check_recurrance_chat_ticket(self, opendf, closeddf, phone_num):
        already_exists = False
        if phone_num in list(closeddf['Number']):
            index = None
            count = 0
            for val in list(closeddf['Number']):
                if val == phone_num:
                    index= count
                    break
                count += 1
            realtime_gsheet = googlesheets_apis(spreadsheet_id=config.crm_spreadsheet_id)
            realtime_gsheet.delete_rows2(rowids=index, sheet_name=config.crm_closed_sheet_name)
        elif phone_num in list(opendf['Number']):
            already_exists = True
        return already_exists




    def add_alert_to_sheet(self, payload, sla_value = float(2)):
        try:
            opendf = self.gsheets.load_sheet_as_csv(sheet_name=config.crm_open_sheet_name)
            closeddf = self.gsheets.load_sheet_as_csv(sheet_name=config.crm_closed_sheet_name)
            alert = payload['Alert Type']
            phone_num = payload['Number']
            sla_value = round(sla_value, 2)
            if alert in {'Delivery delay', 'Pickup delay'}:
                order_number = payload['Order Number']
                already_exists = self.check_recurrance_ops_ticket(opendf=opendf, closeddf=closeddf, order_number=order_number, alert=alert)
            elif alert in {'Reply delay'}:
                already_exists = self.check_recurrance_chat_ticket(opendf=opendf, closeddf=closeddf, phone_num=phone_num)
            self.columns_list, self.column_dict, self.col_index = self.gsheets.get_column_names(sheet_name=config.crm_open_sheet_name)
            if not already_exists:
                set_of_tickets = set(opendf['Ticket No']).union(set(closeddf['Ticket No']))
                number_of_entries = len(set_of_tickets)
                number_of_tickets_in_open = len(set(opendf['Ticket No']))
                float_tickets = [float(val) for val in set_of_tickets]
                max_val = max(float_tickets)
                new_ticket = int(max_val+1)
                payload['Ticket No'] = str(new_ticket)
                payload['SLA(Hours)'] = sla_value
                payload['Date Opened'] = epoch_to_dd_mm_yy_time(int(time.time()))
                # payload['Suggested Context'] = 'Promised date: ' + payload['Promised Date'] + '\nEstimated date: ' + payload['Estimated Date'] + '\nDelivery Status: ' + payload['Delivery Status']
                # if alert in {'Reply delay'}: #{'Delivery delay', 'Pickup delay'}:
                push_csv_dict = {}
                for val in self.columns_list:
                    if val in payload:
                        push_csv_dict[val] = payload[val]
                    elif val not in payload and val != 'Status':
                        push_csv_dict[val] = '--'
                    elif val == 'Status':
                        push_csv_dict[val] = ''

                push_csv = pd.DataFrame([push_csv_dict])
                push_csv.to_csv(self.update_csv_path, index=False)
                self.gsheets.append_csv_to_google_sheets(csv_path=self.update_csv_path,
                                                       sheet_name=config.crm_open_sheet_name)

                if alert in {'Delivery delay', 'Pickup delay'}:
                    dropdowns_to_update = [{'dropdown': self.dropdown_payload, 'row': number_of_tickets_in_open+1, 'col': self.col_index['Status']}]
                    self.gsheets.update_dropdowns(dropdowns_to_update=dropdowns_to_update, sheet_name=config.crm_open_sheet_name)
                print('google sheets api call to add content done')
        except:
            print('Add to CRM failed')
            # self.gsheets.sort_sheet(sheet_name=config.crm_open_sheet_name,
            #                        sorting_rule={'col': self.col_index['SLA(Hours)'], 'direction': 'ASCENDING'})

    def send_wati_alarm(self, mode='Delivery delay'):
        if mode == 'Delivery delay':
            for name, phone_num in self.crm_alarm_contacts.items():
                status = self.wati.send_template_message(contact_name=name, contact_number=phone_num,
                                                    template_name='delivery_delay_opsmessage')

    def update_context_time(self, suggested_context, update_freq):
        context_params = suggested_context.split('\n')
        new_context = []
        for line in context_params:
            if 'Time left to reply(hours):' in line:
                timeval = float(line.split(':')[1].replace(' ', ''))
                updated_timestr = str(timeval-update_freq)
                newstr = 'Time left to reply(hours): ' + updated_timestr
                new_context.append(newstr)
            else:
                new_context.append(line)
        return '\n'.join(new_context)


    def sheet_mgr_cron_job(self, update_freq):
        print('Running crm script...')
        '''
        Goals-
        1.Decrease SLAs by 1h since this will be an hourly cron
        2.Trigger alarm based on SLA
        3.Push resolved issues to the closed section
        :return:
        '''
        #Load sheet again for each cron job
        realtime_gsheet = googlesheets_apis(spreadsheet_id=config.crm_spreadsheet_id)
        realtime_df = realtime_gsheet.load_sheet_as_csv(sheet_name=config.crm_open_sheet_name)
        rowcount = 2
        rows_to_add_to_closed = []
        values_to_update = []
        remove_from_opened = []
        # rowid = 2
        #dropdowns_to_update = []
        sla_breach_types = set()
        add_buttons = []
        for idx, row in realtime_df.iterrows():
            ## Remove from opened sheet
            current_context = row['Suggested Context']
            updated_context = self.update_context_time(current_context, update_freq=update_freq)
            row['Suggested Context'] = updated_context
            if rowcount>2:
                if row['Alert Type'] in {'Delivery delay', 'Pickup delay'}:
                    if str(row['SLA(Hours)']) == 'NA':
                        remove_from_opened.append(rowcount)
                        row['Date Closed'] = epoch_to_dd_mm_yy_time(int(time.time()))
                        rows_to_add_to_closed.append(row)
                    else:
                        if float(row['SLA(Hours)'])<=2:
                            sla_breach_types.add(str(row['Alert Type']))

                        values_to_update.extend([{'col': self.column_dict['SLA(Hours)'],
                                                 'row': rowcount,
                                                 'value': float(row['SLA(Hours)'])-update_freq},
                                                {'col': self.column_dict['Suggested Context'],
                                                 'row': rowcount,
                                                 'value': updated_context}
                                                ])
                        ##Decrease SLAs by 1h
                elif row['Alert Type'] in {'Reply delay'}:
                    if str(row['SLA(Hours)']).lower() == 'revive requested':
                        try:
                            status = chat_revive_message(wati=self.wati, name=row['Name'], phone_num='919176270768')
                        except:
                            status = 'Failure'

                        if status == 'Success':
                            remove_from_opened.append(rowcount)
                            row['Date Closed'] = epoch_to_dd_mm_yy_time(int(time.time()))
                            rows_to_add_to_closed.append(row)
                        else:
                            values_to_update.append({'col': self.column_dict['SLA(Hours)'],
                                                     'row': rowcount,
                                                     'value': 'Revive failed'})
                    else:
                        if float(row['SLA(Hours)'])<=10:
                            sla_breach_types.add(str(row['Alert Type']))

                        if float(row['SLA(Hours)']) > 1:
                            values_to_update.extend([{'col': self.column_dict['SLA(Hours)'],
                                                     'row': rowcount,
                                                     'value': float(row['SLA(Hours)'])-update_freq},
                                                    {'col': self.column_dict['Suggested Context'],
                                                     'row': rowcount,
                                                     'value': updated_context}
                                                    ])
                        else:
                            values_to_update.extend([{'col': self.column_dict['SLA(Hours)'],
                                                     'row': rowcount,
                                                     'value': 'Expired'},
                                                    {'col': self.column_dict['Suggested Context'],
                                                     'row': rowcount,
                                                     'value': updated_context}
                                                    ])


            rowcount += 1

        #SLA breach:
        if sla_breach_types:
            delay_trigger = False
            customer_message_delay = False
            for val in sla_breach_types:
                if val in {'Delivery delay', 'Pickup delay'}:
                    delay_trigger = True
                elif val in {'Reply delay'}:
                    customer_message_delay = True

            if delay_trigger:
                for name, contact in self.crm_alarm_contacts.items():
                    status = delivery_delay_alarm_message(wati=self.wati, name= name, phone_num=contact)
            if customer_message_delay:
                for name, contact in self.crm_alarm_contacts.items():
                    status = delivery_delay_alarm_message(wati=self.wati, name= name, phone_num=contact, wati_template='miniture_reply_delay')


        new_to_closed = pd.DataFrame(rows_to_add_to_closed)
        new_to_closed.to_csv(self.tempdf_to_closed_path, index=False)
        realtime_gsheet.append_csv_to_google_sheets(csv_path=self.tempdf_to_closed_path,
                                               sheet_name=config.crm_closed_sheet_name)
        realtime_gsheet.update_cell(values_to_update=values_to_update, sheet_name=config.crm_open_sheet_name)
        # if add_buttons:
        #     realtime_gsheet.add_buttons(button_locations=add_buttons, sheet_name=config.crm_open_sheet_name)
        try:
            realtime_gsheet.delete_rows2(rowids= remove_from_opened, sheet_name = config.crm_open_sheet_name)
        except:
            print('row delete failed')

if __name__ == '__main__':
    crm_obj = crm_sheet()
    crm_obj.sheet_mgr_cron_job()








