import os
import json
from google_sheets_apis import googlesheets_apis
import traceback
from wati_apis import WATI_APIS
import pandas as pd
import config
from utils import epoch_to_dd_mm_yy_time
import time
from miniture_wati_templates import delivery_delay_alarm_message

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
        self.crm_alarm_contacts = {'Javith': '919698606713', 'Milan': '919445574311',
                                 'Sanaa': '919731011565', 'Adithya': '919176270768'}
        self.wati = WATI_APIS()
        self.alert_types = ['Delivery delay', 'Query reply SLA']
        self.tempdf_to_closed_path = os.path.join(os.getcwd(), 'tempdf_to_closed.csv')


    def check_recurrance(self, opendf, closeddf, order_number, alert):
        newdf = pd.concat([opendf, closeddf])
        already_exists = False
        for idx, row in newdf.iterrows():
            if row['Order Number'] == order_number and row['Alert Type'] == alert:
                already_exists = True
        return already_exists

    def add_alert_to_sheet(self, payload, sla_value = float(2)):
        opendf = self.gsheets.load_sheet_as_csv(sheet_name=config.crm_open_sheet_name)
        closeddf = self.gsheets.load_sheet_as_csv(sheet_name=config.crm_closed_sheet_name)
        order_number = payload['Order Number']
        alert = payload['Alert Type']
        already_exists = self.check_recurrance(opendf=opendf, closeddf=closeddf, order_number=order_number, alert=alert)
        self.columns_list, self.column_dict, self.col_index = self.gsheets.get_column_names(sheet_name=config.crm_open_sheet_name)
        if not already_exists:
            set_of_tickets = set(opendf['Ticket No']).union(set(closeddf['Ticket No']))
            number_of_entries = len(set_of_tickets)
            float_tickets = [float(val) for val in set_of_tickets]
            max_val = max(float_tickets)
            new_ticket = int(max_val+1)
            payload['Ticket No'] = str(new_ticket)
            payload['SLA(Hours)'] = sla_value
            payload['Date Opened'] = epoch_to_dd_mm_yy_time(int(time.time()))
            # payload['Suggested Context'] = 'Promised date: ' + payload['Promised Date'] + '\nEstimated date: ' + payload['Estimated Date'] + '\nDelivery Status: ' + payload['Delivery Status']
            push_csv_dict = {}
            for val in self.columns_list:
                if val in payload:
                    push_csv_dict[val] = payload[val]
                elif val not in payload and val != 'Status':
                    push_csv_dict[val] = '--'
                elif val == 'Status':
                    push_csv_dict[val] = ''
            dropdowns_to_update = [{'dropdown': self.dropdown_payload, 'row': number_of_entries+1, 'col': self.col_index['Status']}]
            push_csv = pd.DataFrame([push_csv_dict])
            push_csv.to_csv(self.update_csv_path, index=False)
            self.gsheets.append_csv_to_google_sheets(csv_path=self.update_csv_path,
                                                   sheet_name=config.crm_open_sheet_name)
            self.gsheets.update_dropdowns(dropdowns_to_update=dropdowns_to_update, sheet_name=config.crm_open_sheet_name)
            print('google sheets api call to add content done')
            # self.gsheets.sort_sheet(sheet_name=config.crm_open_sheet_name,
            #                        sorting_rule={'col': self.col_index['SLA(Hours)'], 'direction': 'ASCENDING'})

    def send_wati_alarm(self, mode='Delivery delay'):
        if mode == 'Delivery delay':
            for name, phone_num in self.crm_alarm_contacts.items():
                status = self.wati.send_template_message(contact_name=name, contact_number=phone_num,
                                                    template_name='delivery_delay_opsmessage')

    def sheet_mgr_cron_job(self):
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
        for idx, row in realtime_df.iterrows():
            ## Remove from opened sheet
            if rowcount>2:
                if str(row['SLA(Hours)']) == 'NA':
                    remove_from_opened.append(rowcount)
                    row['Date Closed'] = epoch_to_dd_mm_yy_time(int(time.time()))
                    rows_to_add_to_closed.append(row)
                elif float(row['SLA(Hours)'])<=2:
                    sla_breach_types.add(str(row['Alert Type']))
                    ##Decrease SLAs by 1h
                    values_to_update.append({'col': self.column_dict['SLA(Hours)'],
                                             'row': rowcount,
                                             'value': float(row['SLA(Hours)'])-1})
            rowcount += 1

        #SLA breach:
        if sla_breach_types:
            delay_trigger = False
            customer_message_delay = False
            for val in sla_breach_types:
                if 'delay' in val:
                    delay_trigger = True

            if delay_trigger:
                for name, contact in self.crm_alarm_contacts.items():
                    status = delivery_delay_alarm_message(wati=self.wati, name= name, phone_num=contact,
                                                 wati_template='delivery_delay_opsmessage')


        new_to_closed = pd.DataFrame(rows_to_add_to_closed)
        new_to_closed.to_csv(self.tempdf_to_closed_path, index=False)
        realtime_gsheet.append_csv_to_google_sheets(csv_path=self.tempdf_to_closed_path,
                                               sheet_name=config.crm_closed_sheet_name)
        realtime_gsheet.update_cell(values_to_update=values_to_update, sheet_name=config.crm_open_sheet_name)
        realtime_gsheet.delete_rows2(rowids= remove_from_opened, sheet_name = config.crm_open_sheet_name)

if __name__ == '__main__':
    crm_obj = crm_sheet()
    crm_obj.sheet_mgr_cron_job()








