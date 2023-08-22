from flask import Flask, request
from flask_restx import Api, Resource, fields
from werkzeug.datastructures import FileStorage
import pandas as pd
import os
from order_report_process import get_order_details, create_zoho_invoice_csv, check_cod_cancellations
from email_sender import send_dispatch_email, send_usermanual_email, send_dispatch_usermanual_email, send_csv
from wati_apis import WATI_APIS
import traceback
import logging

from product_manual_map import get_product_name_manual
import time
from datetime import datetime
from google_sheets_apis import googlesheets_apis
from validation_utils import match_cols, input_df_preprocessing
import config

print('after all imports')
wati = WATI_APIS()
gsheets_db = googlesheets_apis(spreadsheet_id=config.db_spreadsheet_id)
gsheets_accounts = googlesheets_apis(spreadsheet_id=config.accounts_spreadsheet_id)

print('after initiating google sheets')
columns_list, column_dict = gsheets_db.get_column_names(sheet_name=config.db_sheet_name)

app = Flask(__name__)
api = Api(app, version='1.0', title='CSV API', description='API for processing CSV files')

print('After creating api class')

csv_upload_model = api.model('CSVUpload', {
    'file': fields.Raw(required=True, description='CSV file')
})

upload_parser = api.parser()
upload_parser.add_argument('file', location='files',
                           type=FileStorage, required=True)

print('API Parser')

incomplete_csv_path = os.path.join(os.getcwd(), 'incomplete_csv.csv')
zoho_invoice_csv_path = os.path.join(os.getcwd(), 'zohocsv.csv')
cancelled_csv_path = os.path.join(os.getcwd(), 'cancelled_csv.csv')


def updated_cancelled_records_in_db(cancelled_ids):
    col_id = column_dict['unique_id']
    row_numbers = gsheets_db.get_row_numbers(column_name= col_id, target_values = cancelled_ids, sheet_name=config.db_sheet_name)
    col_id_status = column_dict['status']
    values_to_update = []
    for val in row_numbers:
        values_to_update.append({'col': col_id_status, 'row': val, 'value': 'cancelled'})
    gsheets_db.update_cell(values_to_update=values_to_update, sheet_name=config.db_sheet_name)

@api.route('/process_csv')
class CSVProcessing(Resource):
    @api.expect(upload_parser)
    def post(self):
        # app.logger.warning('testing warning log')
        # app.logger.error('testing error log')
        # app.logger.info('testing info log')
        # print('testing print log')
        try:
            args = upload_parser.parse_args()
            csv_file = args['file']
            df = pd.read_csv(csv_file)
            print('read file')
            df = input_df_preprocessing(df)
            tracker_df = gsheets_db.load_sheet_as_csv(sheet_name=config.db_sheet_name)
            live_data, incomplete_csv, cancelled_orders_csv, browntape_new_csv = get_order_details(browntape_df=df, tracker_df=tracker_df)

            if browntape_new_csv is not None:
                ## send csv email for zoho invoice sheet
                try:
                    invoice_csv = create_zoho_invoice_csv(browntape_new_csv)
                    invoice_csv.to_csv(zoho_invoice_csv_path, index=False)
                    order_dates = list(live_data['order_date'])
                    first_date = order_dates[0]
                    last_date = order_dates[-1]
                    if first_date != last_date:
                        date_range = first_date + '-' + last_date
                    else:
                        date_range = first_date
                    #gsheets_accounts.add_sheet(sheet_name=date_range)
                    gsheets_accounts.append_csv_to_google_sheets(csv_path=zoho_invoice_csv_path, sheet_name=date_range)
                    # status = send_csv(csvfile=zoho_invoice_csv_path, subject='order_report')
                except:
                    print('email csv failed for zoho invoice: ', traceback.format_exc())

            if cancelled_orders_csv is not None:
                cancelled_unique_ids, cancelled_orders_df = check_cod_cancellations(tracker_df= tracker_df, cancelled_orders_df=cancelled_orders_csv)
                cancelled_orders_df.to_csv(cancelled_csv_path, index= False)
                updated_cancelled_records_in_db(cancelled_ids= cancelled_unique_ids)
                ## send csv email for cancelled orders
                try:
                    status = send_csv(csvfile=cancelled_csv_path, subject='cancelled_orders')
                    # idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                    # trackerdf.at[idx, 'email_status'] = status
                    # email_status = status
                except:
                    # idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                    # trackerdf.at[idx, 'email_status'] = 'Failure_exception'
                    # email_status = 'Failure_exception'
                    print('email csv failed: ', traceback.format_exc())



            if incomplete_csv is not None:
                incomplete_csv.to_csv(incomplete_csv_path, index= False)
                ## send csv email for incomplete orders
                try:
                    status = send_csv(csvfile=incomplete_csv_path, subject='incomplete_orders')
                    # idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                    # trackerdf.at[idx, 'email_status'] = status
                    # email_status = status
                except:
                    # idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                    # trackerdf.at[idx, 'email_status'] = 'Failure_exception'
                    # email_status = 'Failure_exception'
                    print('email csv failed: ', traceback.format_exc())
            statuses = []

            live_data.fillna('', inplace= True)

            for idx, row in live_data.iterrows():
                try:
                    id = str(row['unique_id'])
                    sku = str(row['sku'])
                    email = str(row['email_id'])
                    phone_num = str(row['phone_num'])
                    name = str(row['name'])
                    awb = str(int(float(row['awb'])))
                    invoice_number = str(int(float(row['invoice_number'])))
                    product_name, product_manual = get_product_name_manual(sku=sku)
                    #product_name, product_manual = get_product_name_manual(sku=sku)
                    ## send template message
                    if str(row['whatsapp_status']) == '' and invoice_number[:3] in {'WOO', 'SFY'}:
                        try:
                            custom_params=[{'name': 'awb_number', 'value': awb}]
                            status = wati.send_template_message(contact_name=name, contact_number= phone_num, template_name='order_dispatched_with_awb2',
                                                    custom_params=custom_params)
                            if not status:
                                ## Store timeframe n number of times based on number of rows per order
                                idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                print('idx: ', idx)
                                for idx in idxs:
                                    live_data.at[idx, 'whatsapp_status'] = 'Failure'
                                wa_status = 'Failure'
                            else:
                                ## Store timeframe n number of times based on number of rows per order
                                idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                # idx = live_data.index[live_data['unique_id'] == id].tolist()[0]
                                # print('idx: ', idx)
                                for idx in idxs:
                                    live_data.at[idx, 'whatsapp_status'] = 'Success'
                                    live_data.at[idx, 'awb_message_timestamp'] = time.time()
                                wa_status = 'Success'
                        except:
                            idxs = live_data.index[live_data['unique_id'] == id].tolist()
                            for idx in idxs:
                                live_data.at[idx, 'whatsapp_status'] = 'Failure_exception'
                            wa_status = 'Failure_exception'
                            print('whatsapp failed: ', traceback.format_exc())

                    if str(row['usermanual_whatsapp_status']) == '':
                        #send user manual whatsapp
                        try:
                            custom_params = [{'name': 'product_name', 'value': str(product_name)},
                                             {'name': 'media_url', 'value': str(product_manual)}]
                            status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                                                template_name='usermanual_short3',
                                                                custom_params=custom_params)
                            print('Status of whatsapp: ', status)
                            if not status:
                                ## Store timeframe n number of times based on number of rows per order
                                idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                print('idx: ', idx)
                                for idx in idxs:
                                    live_data.at[idx, 'usermanual_whatsapp_status'] = 'Failure'
                                wa_status_usermanual = 'Failure'
                            else:
                                ## Store timeframe n number of times based on number of rows per order
                                idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                # idx = live_data.index[live_data['unique_id'] == id].tolist()[0]
                                # print('idx: ', idx)
                                for idx in idxs:
                                    live_data.at[idx, 'usermanual_whatsapp_status'] = 'Success'
                                    #live_data.at[idx, 'awb_message_timestamp'] = time.time()
                                wa_status_usermanual = 'Success'
                        except:
                            idxs = live_data.index[live_data['unique_id'] == id].tolist()
                            for idx in idxs:
                                live_data.at[idx, 'usermanual_whatsapp_status'] = 'Failure_exception'
                            wa_status_usermanual = 'Failure_exception'
                            print('whatsapp failed: ', traceback.format_exc())

                    if str(row['email_status']) == '' and invoice_number[:3] in {'WOO', 'SFY'}:
                        ## send email
                        try:
                            status = send_dispatch_email(name= name, to_address= email,awb_number=awb)
                            idxs = live_data.index[live_data['unique_id'] == id].tolist()
                            for idx in idxs:
                                live_data.at[idx, 'email_status'] = status
                                live_data.at[idx, 'awb_message_timestamp'] = time.time()
                            email_status = status
                        except:
                            idxs = live_data.index[live_data['unique_id'] == id].tolist()
                            for idx in idxs:
                                live_data.at[idx, 'email_status'] = 'Failure_exception'
                            email_status = 'Failure_exception'
                            print('email failed: ', traceback.format_exc())

                    if str(row['usermanual_email_status']) == '':
                        ## send email for usermanual
                        try:
                            status = send_usermanual_email(name=name, to_address=email, product_name=product_name,
                                                           product_manual_link=product_manual)
                            idxs = live_data.index[live_data['unique_id'] == id].tolist()
                            for idx in idxs:
                                live_data.at[idx, 'usermanual_email_status'] = status
                                #live_data.at[idx, 'awb_message_timestamp'] = time.time()
                            email_status_usermanual = status
                        except:
                            idxs = live_data.index[live_data['unique_id'] == id].tolist()
                            for idx in idxs:
                                live_data.at[idx, 'usermanual_email_status'] = 'Failure_exception'
                            email_status_usermanual = 'Failure_exception'
                            print('email failed: ', traceback.format_exc())

                    processing_time_stamp = time.strftime('%d-%m-%Y %H:%M', time.localtime(time.time()))

                    idxs = live_data.index[live_data['unique_id'] == id].tolist()
                    for idx in idxs:
                        live_data.at[idx, 'timestamp'] = processing_time_stamp

                    statuses.append({'id': id, 'email_status': email_status, 'wa_status': wa_status
                                        , 'email_manual_status': email_status_usermanual,
                                     'wa_manual_status': wa_status_usermanual})
                except:
                    print(traceback.format_exc())
                    statuses.append({'id': id, 'email_status': 'Failure', 'wa_status': 'Failure'})
                    #trackerdf_original = pd.read_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index_col = False)
                    #trackerdf = pd.concat([trackerdf_original,trackerdf])
                    # trackerdf.to_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index = False)
            
            #trackerdf_original = pd.read_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index_col = False)
            #trackerdf = pd.concat([trackerdf_original,trackerdf])
            try:
                live_data = match_cols(live_data, col_names=columns_list)
                live_data.to_csv(os.path.join(os.getcwd(), 'livedata.csv'), index=False)
                gsheets_db.append_csv_to_google_sheets(csv_path=os.path.join(os.getcwd(), 'livedata.csv'), sheet_name=config.db_sheet_name)
            except:
                print('Failure at pushing to LIVE: ')
                print(traceback.format_exc())
                statuses = {'Failed to push to main data!'}
            return statuses

        except:
            print('api failed: ', traceback.format_exc())
            return traceback.format_exc()


if __name__ == '__main__':
    # Custom Swagger UI template configuration
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response


    app.run(debug=True, host= '0.0.0.0', port = 5003)
