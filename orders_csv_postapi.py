from flask import Flask, request
from flask_restx import Api, Resource, fields
from werkzeug.datastructures import FileStorage
import pandas as pd
import os
from order_report_process import get_order_details, create_zoho_invoice_csv, check_cod_cancellations
from email_sender import send_dispatch_email, send_usermanual_email, send_dispatch_usermanual_email, send_csv
import traceback
from product_manual_map import get_product_name_manual
import time
from datetime import datetime
from google_sheets_apis import googlesheets_apis
from utils import match_cols, input_df_preprocessing, check_fields
import config
import logging
from wati_apis import WATI_APIS
from config import ops_automation_alarm_contacts

'''
API that allows for 2 toggles:
a. Order Processing
b. Zoho Accounting CSV generation - and Email push to operations ID

a. Order Processing Code: (args['toggle'] == 1)
- Checks for Unprocessed (incomplete) or Cancelled orders
- Sends tracking email + WhatsApp information if it's a Woocommerce order (some code might be unused now)
- Validates data based on phone number and email format (check_fields function)
- Failed order information captured and sent to ops team (based on check_fields function or if any other exception) 

b. Zoho Accounting CSV generation: (args['toggle'] == 2)
- Converts Browntape CSV into Zoho Books bulk import format CSV using create_zoho_invoice_csv function
- Adds the processed sheet to a Google Sheets file connected to finance team
'''


pre_order_skus = {'YK-KW-006', 'YK-KW-012','YK-KW-027','YK-PZ-007 - BLUE',
                  'YK-PZ-007 - PINK','YK-KW-080', 'YK-KW-007-2','YK-SQ-022-3'}


usermanual_skus_without_video = {'YK-PZ-007 - BLUE', 'YK-PZ-007 - PINK', 'YK-PZ-007 - WHITE','YK-KW-080',
                                 'YK-KW-012'}

# Configure the logger
logging.basicConfig(
    filename='postapi_logs.log',  # Specify the log file name
    level=logging.DEBUG,        # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format= '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
print('after all imports')
wati = WATI_APIS()

gsheets_db = googlesheets_apis(spreadsheet_id= config.db_spreadsheet_id)
gsheets_accounts = googlesheets_apis(spreadsheet_id= config.accounts_spreadsheet_id)
gsheets_preorders = googlesheets_apis(spreadsheet_id= config.preorder_spreadsheet_id)

print('after initiating google sheets')
columns_list, column_dict,_ = gsheets_db.get_column_names(sheet_name=config.db_sheet_name)

app = Flask(__name__)
api = Api(app, version='1.0', title='CSV API', description='API for processing CSV files')

print('After creating api class')

csv_upload_model = api.model('CSVUpload', {
    'file': fields.Raw(required=True, description='CSV file')
})

upload_parser = api.parser()
upload_parser.add_argument('file', location='files',
                           type=FileStorage, required=True)
upload_parser.add_argument('toggle', type=int, default=1, choices=[1, 2], help='Choose 1 for Order Processing & 2 for Accounting CSV Creation')

print('API Parser')

incomplete_csv_path = os.path.join(os.getcwd(), 'incomplete_csv.csv')
zoho_invoice_csv_path = os.path.join(os.getcwd(), 'zohocsv.csv')
cancelled_csv_path = os.path.join(os.getcwd(), 'cancelled_csv.csv')

def check_existence_in_df(row, df):
    '''
    check existence in terms of sku and orderid
    :param row:
    :param df:
    :return:
    '''
    exists = False
    for idx, rw in df.iterrows():
        if rw['unique_id'] == row['unique_id'] and rw['sku'] == row['sku']:
            exists = True
            break
    return exists


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
            failure_statements = []
            failed_ids = set()

            args = upload_parser.parse_args()
            csv_file = args['file']
            input_df = pd.read_csv(csv_file, index_col=False)
            #print('read file')
            logging.info("read file")
            if args['toggle'] == 1:

                df = input_df_preprocessing(input_df)
                tracker_df = gsheets_db.load_sheet_as_csv(sheet_name=config.db_sheet_name)
                preorder_df = gsheets_preorders.load_sheet_as_csv(sheet_name= config.preorder_sheet_name)
                live_data, incomplete_csv, cancelled_orders_csv, browntape_new_csv = get_order_details(browntape_df=df, tracker_df=tracker_df)

                if cancelled_orders_csv is not None:
                    cancelled_unique_ids, cancelled_orders_df = check_cod_cancellations(tracker_df= tracker_df, cancelled_orders_df=cancelled_orders_csv)
                    cancelled_orders_df.to_csv(cancelled_csv_path, index= False)
                    updated_cancelled_records_in_db(cancelled_ids= cancelled_unique_ids)
                    ## send csv email for cancelled orders
                    try:
                        status = send_csv(csvfile=cancelled_csv_path, subject='cancelled_orders')
                    except:
                        print('email csv failed: ', traceback.format_exc())
                        logging.error("email csv failed for cancelled orders")
                        logging.error(traceback.format_exc())



                if incomplete_csv is not None:
                    incomplete_csv.to_csv(incomplete_csv_path, index= False)
                    ## send csv email for incomplete orders
                    try:
                        status = send_csv(csvfile=incomplete_csv_path, subject='incomplete_orders')
                    except:
                        print('email csv failed: ', traceback.format_exc())
                        logging.error("email csv failed for incomplete orders")
                        logging.error(traceback.format_exc())
                statuses = []

                live_data.fillna('', inplace= True)
                cols = list(live_data.columns)
                print(live_data)

                preorder_list = []
                for idx, row in live_data.iterrows():
                    ##Validate all variables
                    sku = str(row['sku'])
                    try:
                        valid = True
                        failure_reasons = []
                        for c in cols:
                            verdict = check_fields(val=row[c], field=c, awb_required=True)
                            print('verdict: ', verdict)
                            if verdict is not True:
                                failure_reasons.append(verdict)
                                valid = False
                    except:
                        logging.error('verdict block failed for ID: '+ row['unique_id'])
                        logging.error(traceback.format_exc())
                        failure_reasons = []
                        valid = False

                    print('valid: ', valid)

                    if valid is not True:
                        id = str(row['unique_id'])
                        invoice_number = str(row['invoice_number'])
                        name = str(row['name'])
                        if invoice_number[:3] in {'AMZ'} or name == 'ENCRYPTED DATA':
                            live_data.at[idx, 'whatsapp_status'] = 'NA'
                            live_data.at[idx, 'usermanual_whatsapp_status'] = 'NA'
                            live_data.at[idx, 'email_status'] = 'NA'
                            live_data.at[idx, 'usermanual_email_status'] = 'NA'
                        else:
                            failure_statement = id + ': ' + ', '.join(failure_reasons)
                            failure_statements.append(failure_statement)
                            failed_ids.add(idx)
                    else:
                        try:
                            id = str(row['unique_id'])
                            sku = str(row['sku'])
                            email = str(row['email_id'])
                            phone_num = str(row['phone_num'])
                            name = str(row['name'])
                            invoice_number = str(row['invoice_number'])
                            valid_manual = False
                            try:
                                product_name, product_manual, review_url, cashback = get_product_name_manual(sku=sku)
                                if product_manual != '':
                                    valid_manual = True
                            except:
                                pass
                            ## send template message
                            wa_status = 'NA'
                            val = invoice_number[:3] in {'WOO'}
                            #print('bool: ', val)
                            if str(row['whatsapp_status']) == '' and invoice_number[:3] in {'WOO'}:
                                #print('Going into the if statement validating that its a woocommerce order!')
                                try:
                                    awb = str(int(float(row['awb'])))
                                    custom_params=[{'name': 'awb_number', 'value': awb}]
                                    status = wati.send_template_message(contact_name=name, contact_number= phone_num, template_name='order_dispatched_with_awb2',
                                                            custom_params=custom_params)
                                    #print('WATI message status: ', status)
                                    if not status:
                                        ## Store timeframe n number of times based on number of rows per order
                                        idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                        #print('idx: ', idx)
                                        for ix in idxs:
                                            live_data.at[ix, 'whatsapp_status'] = 'Failure'
                                        wa_status = 'Failure'
                                    else:
                                        #print('status is true')
                                        ## Store timeframe n number of times based on number of rows per order
                                        idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                        # idx = live_data.index[live_data['unique_id'] == id].tolist()[0]
                                        # print('idx: ', idx)
                                        for ix in idxs:
                                            live_data.at[ix, 'whatsapp_status'] = 'Success'
                                            live_data.at[ix, 'awb_message_timestamp'] = time.time()
                                        #print('livedata updation for whatsapp')
                                        #print(live_data['whatsapp_status'])
                                        wa_status = 'Success'
                                except:
                                    try:
                                        idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                        for ix in idxs:
                                            live_data.at[ix, 'whatsapp_status'] = 'Failure_exception'
                                        wa_status = 'Failure_exception'
                                        #print('whatsapp failed awb: ', traceback.format_exc())
                                        logging.error("whatsapp failed exception for: " + id)
                                        logging.error(traceback.format_exc())
                                    except:
                                        logging.error("exception block for whatsapp awb failed")
                                        logging.error(traceback.format_exc())
                                        failure_statement = id + ': ' + ', '.join('Adding to database might have failed at exception for awb whatsapp')
                                        failure_statements.append(failure_statement)
                                        failed_ids.add(idx)
                            elif str(row['whatsapp_status']) == '':
                                print('it better not be coming here')
                                try:
                                    idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                    # idx = live_data.index[live_data['unique_id'] == id].tolist()[0]
                                    # print('idx: ', idx)
                                    for ix in idxs:
                                        live_data.at[ix, 'whatsapp_status'] = 'NA'
                                        live_data.at[ix, 'awb_message_timestamp'] = time.time()
                                except:
                                    logging.error('Failed at else block (if its not woocommerce order)')
                                    logging.error(traceback.format_exc())
                                    failure_statement = id + ': ' + ', '.join('Adding to database might have failed for non-woo awb whatsapp')
                                    failure_statements.append(failure_statement)
                                    failed_ids.add(idx)

                            #print('live_data after whatsapp status', live_data['whatsapp_status'])

                            wa_status_usermanual = 'NA'
                            if str(row['usermanual_whatsapp_status']) == '':
                                #send user manual whatsapp
                                if valid_manual:
                                    try:
                                        # if sku in usermanual_skus_without_video:
                                        #     wati_template = 'miniture_usermanual_5'
                                        # else:
                                        #     wati_template = 'miniture_usermanual_5'
                                        # custom_params = [{'name': 'product_name', 'value': str(product_name)},
                                        #                  {'name': 'media_url', 'value': str(product_manual)}]
                                        # status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                        #                                     template_name= wati_template,
                                        #                                     custom_params=custom_params)
                                        # #print('Status of whatsapp: ', status)
                                        # if not status:
                                        #     ## Store timeframe n number of times based on number of rows per order
                                        #     # idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                        #     # print('idx: ', idx)
                                        #     # for idx in idxs:
                                        #     live_data.at[idx, 'usermanual_whatsapp_status'] = 'Failure'
                                        #     wa_status_usermanual = 'Failure'
                                        # else:
                                        #     ## Store timeframe n number of times based on number of rows per order
                                        #     # idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                        #     # # idx = live_data.index[live_data['unique_id'] == id].tolist()[0]
                                        #     # # print('idx: ', idx)
                                        #     # for ix in idxs:
                                            live_data.at[idx, 'usermanual_whatsapp_status'] = 'Not Sent'
                                                #live_data.at[idx, 'awb_message_timestamp'] = time.time()
                                            wa_status_usermanual = 'Not Sent'
                                    except:
                                        try:
                                            live_data.at[idx, 'usermanual_whatsapp_status'] = 'Failure_exception'
                                            wa_status_usermanual = 'Failure_exception'
                                            #print('whatsapp failed: ', traceback.format_exc())
                                            logging.error("whatsapp failed usermanual for: " + id)
                                            logging.error(traceback.format_exc())
                                        except:
                                            logging.error("exception block for whatsapp usermanual failed")
                                            logging.error(traceback.format_exc())
                                            failure_statement = id + ': ' + ', '.join('Adding to database might have failed at exception for usermanual whatsapp')
                                            failure_statements.append(failure_statement)
                                            failed_ids.add(idx)

                                else:
                                    live_data.at[idx, 'usermanual_whatsapp_status'] = 'Skipped'
                                    wa_status_usermanual = 'Failure'

                            #print('livedata after whatsapp usermanual: ', live_data['whatsapp_status'])
                            email_status = 'NA'
                            if str(row['email_status']) == '' and invoice_number[:3] in {'WOO'}:
                                ## send email
                                try:
                                    awb = str(int(float(row['awb'])))
                                    status = send_dispatch_email(name= name, to_address= email,awb_number=awb)
                                    idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                    for ix in idxs:
                                        live_data.at[ix, 'email_status'] = status
                                        live_data.at[ix, 'awb_message_timestamp'] = time.time()
                                    email_status = status
                                except:
                                    try:
                                        idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                        for ix in idxs:
                                            live_data.at[ix, 'email_status'] = 'Failure_exception'
                                        email_status = 'Failure_exception'
                                        #print('email failed: ', traceback.format_exc())
                                        logging.error("email failed awb for: " + id)
                                        logging.error(traceback.format_exc())
                                    except:
                                        logging.error("exception block for email awb failed")
                                        logging.error(traceback.format_exc())
                                        failure_statement = id + ': ' + ', '.join('Adding to database might have failed at exception for awb email')
                                        failure_statements.append(failure_statement)
                                        failed_ids.add(idx)
                            elif str(row['email_status']) == '':
                                try:
                                    idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                    for ix in idxs:
                                        live_data.at[ix, 'email_status'] = 'NA'
                                        # live_data.at[ix, 'awb_message_timestamp'] = time.time()
                                except:
                                    logging.error("exception block for email awb failed- for non woocommerce")
                                    logging.error(traceback.format_exc())
                                    failure_statement = id + ': ' + ', '.join('Adding to database might have failed for awb email')
                                    failure_statements.append(failure_statement)
                                    failed_ids.add(idx)
                            #print('livedata after email: ', live_data['whatsapp_status'])
                            email_status_usermanual = 'NA'
                            if str(row['usermanual_email_status']) == '':
                                ## send email for usermanual
                                if valid_manual:
                                    try:
                                        # status = send_usermanual_email(name=name, to_address=email, product_name=product_name,
                                        #                                product_manual_link=product_manual)
                                        # # idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                        # # for ix in idxs:
                                        live_data.at[idx, 'usermanual_email_status'] = 'Not Sent'
                                            #live_data.at[idx, 'awb_message_timestamp'] = time.time()
                                        email_status_usermanual = 'Not Sent'
                                    except:
                                        # idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                        # for ix in idxs:
                                        try:
                                            live_data.at[idx, 'usermanual_email_status'] = 'Failure_exception'
                                            email_status_usermanual = 'Failure_exception'
                                            logging.error("email failed usermanual for: " + id)
                                            logging.error(traceback.format_exc())
                                        except:
                                            logging.error("exception block for email usermanual failed")
                                            logging.error(traceback.format_exc())
                                            failure_statement = id + ': ' + ', '.join('Adding to database might have failed at exception for usermanual email')
                                            failure_statements.append(failure_statement)
                                            failed_ids.add(idx)
                                else:
                                    live_data.at[idx, 'usermanual_email_status'] = 'Skipped'
                                    # live_data.at[idx, 'awb_message_timestamp'] = time.time()
                                    email_status_usermanual = 'Skipped'

                            #print('livedata after usermanual eamil: ', live_data['whatsapp_status'])

                            try:
                                processing_time_stamp = time.strftime('%d-%m-%Y %H:%M', time.localtime(time.time()))

                                idxs = live_data.index[live_data['unique_id'] == id].tolist()
                                for ix in idxs:
                                    live_data.at[ix, 'timestamp'] = processing_time_stamp
                            except:
                                logging.error('processing and adding timestamp failed')
                                logging.error(traceback.format_exc())

                            statuses.append({'id': id, 'email_status': email_status, 'wa_status': wa_status,
                                             'email_manual_status': email_status_usermanual,
                                             'wa_manual_status': wa_status_usermanual})
                        except:
                            print(traceback.format_exc())
                            logging.error("LOOP FAILED FOR ENTRY")
                            logging.error(traceback.format_exc())
                            try:
                                id = str(row['unique_id'])
                                statuses.append({'id': id, 'email_status': 'Failure', 'wa_status': 'Failure'})
                                failure_statement = id + ': ' + 'Processing of entire order failed'
                            except:
                                statuses.append({'email_status': 'Failure', 'wa_status': 'Failure'})
                                failure_statement = 'Processing of entire order failed'
                            failure_statements.append(failure_statement)
                            failed_ids.add(idx)
                            #trackerdf_original = pd.read_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index_col = False)
                            #trackerdf = pd.concat([trackerdf_original,trackerdf])
                            # trackerdf.to_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index = False)

                #trackerdf_original = pd.read_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index_col = False)
                #trackerdf = pd.concat([trackerdf_original,trackerdf])

                try:
                    print('Failed ids: ', failed_ids)
                    live_data = live_data.drop(failed_ids)
                    print('live data: ', live_data)
                    print('columns_list: ', columns_list)
                    live_data = match_cols(live_data, col_names=columns_list)
                    print('post match cols: ', live_data)
                    #print('live_data before pushing: ')
                    #print(live_data['whatsapp_status'])
                    live_data.to_csv(os.path.join(os.getcwd(), 'livedata.csv'), index=False)
                    gsheets_db.append_csv_to_google_sheets(csv_path=os.path.join(os.getcwd(), 'livedata.csv'), sheet_name=config.db_sheet_name)

                    try:
                        preorder_df = pd.DataFrame(preorder_list)
                        preorder_df = match_cols(preorder_df, col_names=columns_list)
                        preorder_df.to_csv(os.path.join(os.getcwd(), 'preorder_df.csv'), index=False)
                        gsheets_preorders.append_csv_to_google_sheets(csv_path=os.path.join(os.getcwd(), 'preorder_df.csv'),
                                                               sheet_name=config.preorder_sheet_name)
                    except:
                        print('failed at adding to preorder sheet')
                        traceback.format_exc()
                except:
                    #print('Failure at pushing to LIVE: ')
                    #print(traceback.format_exc())
                    logging.error("failure at pushing to LIVE")
                    logging.error(traceback.format_exc())
                    statuses = {'Failed to push to main data!'}
                    failure_statement = '*Failed to push all data to db!*'
                    failure_statements.append(failure_statement)
                    failed_ids.add(id)

                # print('failure_statements: ', failure_statement)
                try:
                    if failure_statements:
                            failure_message_alarm = '; '.join(failure_statements)
                            for name, phone_num in ops_automation_alarm_contacts.items():
                                custom_params = [{'name': 'orderlist', 'value': failure_message_alarm}]
                                status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                                                    template_name='failed_orders_processing',
                                                                    custom_params=custom_params)
                except:
                    logging.error('Failed to send failure message')
                    logging.error(traceback.format_exc())


                return statuses

            elif args['toggle'] == 2:
                if input_df is not None:
                    ## send csv email for zoho invoice sheet
                    try:
                        invoice_csv, flag = create_zoho_invoice_csv(input_df)
                        invoice_csv.to_csv(zoho_invoice_csv_path, index=False)
                        order_dates = list(input_df['Order Date(IST)'])
                        first_date = order_dates[0]
                        last_date = order_dates[-1]
                        if first_date != last_date:
                            date_range = first_date + '-' + last_date
                        else:
                            date_range = first_date
                        #gsheets_accounts.add_sheet(sheet_name=date_range)
                        if flag is not True:
                            failure_statements.append('Accounting CSV failed due to both item and order discount')
                        gsheets_accounts.append_csv_to_google_sheets(csv_path=zoho_invoice_csv_path, sheet_name=date_range)
                        # status = send_csv(csvfile=zoho_invoice_csv_path, subject='order_report')
                        return 'Success'
                    except:
                        #print('email csv failed for zoho invoice: ', traceback.format_exc())
                        logging.error("email csv failed for zoho invoice")
                        logging.error(traceback.format_exc())
                        return 'Failure'


        except:
            print('api failed: ', traceback.format_exc())
            logging.error('API FAILED')
            logging.error(traceback.format_exc())
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
