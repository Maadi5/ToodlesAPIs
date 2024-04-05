import os
import traceback

import pandas as pd
import json
from product_manual_map import get_product_name_manual
from google_sheets_apis import googlesheets_apis
import config
from wati_apis import WATI_APIS
import urllib.request

wati = WATI_APIS()

sheets_read_api = googlesheets_apis(spreadsheet_id=config.db_spreadsheet_id)


#First capture all phone numbers from the db, and check if it exists in the db, and get all order details. Have a flag if this is captured.
class gpt_functions():
    def __init__(self, phone_number, name=None):
        self.phone_number= phone_number
        self.get_phone_number_list()
        self.number_exists = True if self.phone_number in self.phone_number_list else False
        if self.number_exists:
            self.order_details = self.order_details_from_field(value= self.phone_number, field= 'phone_num')
        else:
            self.order_details = None

    def get_phone_number_list(self):
        dataset = sheets_read_api.query_data(sheet_name=config.db_sheet_name, filter_func=None)
        self.phone_number_list = list(dataset['phone_num'])
        del dataset

    def get_gptfunction_list(self):

        # if not self.number_exists:
        tracking_id_function = {
                  "name": "get_tracking_number_from_order_number",
                  "description": "Get the tracking number for an order for tracking it's location.",
                  "parameters": {
                      "type": "object",
                      "properties": {
                          "order_number": {
                              "type": "string",
                              "description": "The order number of the order"
                          },
                      },
                      "required": ["order_number"]
                  }
                  }
        send_user_manual_function = {"name": "get_usermanual_from_order_number",
            "description": "Get the assembly guide PDF for an order, based on the order number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "The order number of the order"
                    },
                },
                "required": ["order_number"]
            }
            }

        get_delivery_time_estimate = {"name": "get_delivery_est_frompincode",
            "description": "Get a delivery time estimate based on the provided pincode",
            "parameters": {
                "type": "object",
                "properties": {
                    "pin_code": {
                        "type": "string",
                        "description": "The area code of the user (also called as pincode)"
                    },
                },
                "required": ["pin_code"]
            }
            }

        return [tracking_id_function,send_user_manual_function, get_delivery_time_estimate]




    def order_details_from_field(self, value, field, preload_csv = None):
        filter_func = lambda row: row[field] == value
        if preload_csv == None:
            out = sheets_read_api.query_data(sheet_name=config.db_sheet_name, filter_func= filter_func)
        else:
            data = preload_csv.values.tolist()
            header_row = list(preload_csv)
            filtered_data = [row for row in data if filter_func(dict(zip(header_row, row)))]
            values = [header_row] + filtered_data
            csv_list = []
            for _, val in enumerate(values[1:]):
                dfdict = {}
                for idx, v in enumerate(val):
                    dfdict[values[0][idx]] = v
                csv_list.append(dfdict)
            out = pd.DataFrame(csv_list)
        if out.shape[0] == 0:
            return None
        else:
            return out

    def get_delivery_est_frompincode(self, pin_code):
        try:
            bluedart_approx_csv = pd.read_csv(os.path.join(os.getcwd(), 'approx_delivery_times_2.csv'), index_col=False)
            if bluedart_approx_csv[bluedart_approx_csv['Pincode'] == int(float(pin_code))].shape[0]>0:
                tat_value = list(bluedart_approx_csv[bluedart_approx_csv['Pincode'] == int(float(pin_code))]['TAT'])[0]
            else:
                return 'HITL'
            return str(round(tat_value/24)) + ' days from the date of ordering.'
        except:
            print(traceback.format_exc())
            return 'HITL'

    def get_tracking_number_from_order_number(self, order_number):
        output_val = self.get_awb_from_order_number(value= order_number)
        return output_val

    def get_tracking_number(self):
        try:
            awb = list(self.order_details['awb'])[0]
            return awb
        except:
            print(traceback.format_exc())
            return 'HITL - exception'

    def get_awb_from_order_number(self, value):
        order_details= self.order_details_from_field(value= value, field= 'channel_order_number')
        try:
            awb = list(order_details['awb'])[0]
            return 'Your BlueDart tracking number is: ' + awb + '. Please track it on www.bluedart.in/tracking'
        except:
            print(traceback.format_exc())
            return 'HITL - exception'

    def download_file(self, download_url, filename):
        response = urllib.request.urlopen(download_url)
        file = open(filename + ".pdf", 'wb')
        file.write(response.read())
        file.close()

    def get_usermanual_from_order_number(self, order_number):
        order_details = self.order_details_from_field(value=order_number, field='channel_order_number')
        failed = False
        statuses = []
        try:
            for val in list(order_details['sku']):
                product_name, product_manual,_, _ = get_product_name_manual(sku=val)
                self.download_file(download_url=product_manual, filename= 'usermanual')
                try:
                    wati.send_session_pdf_file(contact_number=self.phone_number, filename_to_user=product_name+'_usermanual.pdf',
                                               local_file_name='usermanual.pdf')
                except:
                    print(traceback.format_exc())
                    statuses.append(False)
        except:
            failed = True
        if False in statuses:
            return "Coundn't send document (HITL)"
        elif failed:
            return "Couldn't find order number (HITL)"
        else:
            return '<Document Attached>'

if __name__ == '__main__':
    gptclass = gpt_functions(phone_number='919176270768')

    gptclass.get_delivery_est_frompincode('600020')











