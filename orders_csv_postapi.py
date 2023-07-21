from flask import Flask, request
from flask_restx import Api, Resource, fields
from werkzeug.datastructures import FileStorage
import pandas as pd
import os
from order_report_process import get_order_details, create_zoho_invoice_csv
from email_sender import send_dispatch_email, send_usermanual_email, send_dispatch_usermanual_email, send_csv
from wati_apis import WATI_APIS
import traceback
from product_manual_map import get_product_name_manual
import time
from google_sheets_apis import googlesheets_apis
from validation_utils import match_cols

wati = WATI_APIS()
gsheets = googlesheets_apis()

columns_list, _ = gsheets.get_column_names()

app = Flask(__name__)
api = Api(app, version='1.0', title='CSV API', description='API for processing CSV files')

csv_upload_model = api.model('CSVUpload', {
    'file': fields.Raw(required=True, description='CSV file')
})

upload_parser = api.parser()
upload_parser.add_argument('file', location='files',
                           type=FileStorage, required=True)

incomplete_csv_path = os.path.join(os.getcwd(), 'incomplete_csv.csv')
zoho_invoice_csv_path = os.path.join(os.getcwd(), 'zohocsv.csv')

@api.route('/process_csv')
class CSVProcessing(Resource):
    @api.expect(upload_parser)
    def post(self):
        try:
            args = upload_parser.parse_args()
            csv_file = args['file']
            df = pd.read_csv(csv_file)
            tracker_df = gsheets.load_sheet_as_csv()
            print('loaded tracker df again')
            print('ids: ', set(tracker_df['unique_id']))
            live_data, incomplete_csv = get_order_details(browntape_df=df, tracker_df=tracker_df)

            incomplete_csv.to_csv(incomplete_csv_path, index= False)
            statuses = []

            for idx, row in live_data.iterrows():
                try:
                    id = row['unique_id']
                    sku = row['sku']
                    email = row['email_id']
                    phone_num = row['phone_num']
                    name = row['name']
                    awb = row['awb']
                    #product_name, product_manual = get_product_name_manual(sku=sku)
                    ## send template message
                    try:
                        custom_params=[{'name': 'awb_number', 'value': awb}]
                        status = wati.send_template_message(contact_name=name, contact_number= phone_num, template_name='order_dispatched_with_awb2',
                                                custom_params=custom_params)
                        if not status:
                            idx = live_data.index[live_data['unique_id'] == id].tolist()[0]
                            print('idx: ', idx)
                            live_data.at[idx, 'whatsapp_status'] = 'Failure'
                            wa_status = 'Failure'
                        else:
                            idx = live_data.index[live_data['unique_id'] == id].tolist()[0]
                            print('idx: ', idx)
                            live_data.at[idx, 'whatsapp_status'] = 'Success'
                            live_data.at[idx, 'awb_message_timestamp'] = time.time()
                            wa_status = 'Success'
                    except:
                        idx = live_data.index[live_data['unique_id'] == id].tolist()[0]
                        live_data.at[idx, 'whatsapp_status'] = 'Failure_exception'
                        wa_status = 'Failure_exception'
                        print('whatsapp failed: ', traceback.format_exc())
                    
                    ## send email
                    try:
                        status = send_dispatch_email(name= name, to_address= email,awb_number=awb)
                        idx = live_data.index[live_data['unique_id'] == id].tolist()[0]
                        live_data.at[idx, 'email_status'] = status
                        live_data.at[idx, 'awb_message_timestamp'] = time.time()
                        email_status = status
                    except:
                        idx = live_data.index[live_data['unique_id'] == id].tolist()[0]
                        live_data.at[idx, 'email_status'] = 'Failure_exception'
                        email_status = 'Failure_exception'
                        print('email failed: ', traceback.format_exc())

                    ## send csv email for incomplete orders
                    try:
                        status = send_csv(csvfile= incomplete_csv_path, subject='incomplete_orders')
                        # idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                        # trackerdf.at[idx, 'email_status'] = status
                        # email_status = status
                    except:
                        # idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                        # trackerdf.at[idx, 'email_status'] = 'Failure_exception'
                        # email_status = 'Failure_exception'
                        print('email csv failed: ', traceback.format_exc())


                    # ## send manual email
                    # try:
                    #     status = send_usermanual_email(name= name, to_address= email, product_name=product_name, product_manual_link= product_manual)
                    #     trackerdf[trackerdf['unique_id'] == id]['usermanual_email_status'] = status
                    #     email_manual_status = status
                    # except:
                    #     trackerdf[trackerdf['unique_id'] == id]['usermanual_email_status'] = 'Failure_exception'
                    #     email_manual_status = 'Failure_exception'
                    #     print('email failed: ', traceback.format_exc())
                    statuses.append({'id': id, 'email_status': email_status, 'wa_status': wa_status})#, 'email_manual_status': email_manual_status,})
                    #'wa_manual_status': wa_manual_status})
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

                ## send csv email for zoho invoice sheet
                try:
                    invoice_csv = create_zoho_invoice_csv(live_data)
                    invoice_csv.to_csv(zoho_invoice_csv_path, index=False)
                    status = send_csv(csvfile=zoho_invoice_csv_path, subject='order_report')
                except:
                    print('email csv failed for zoho invoice: ', traceback.format_exc())

                gsheets.append_csv_to_google_sheets(os.path.join(os.getcwd(), 'livedata.csv'))
            except:
                print('Failure at pushing to LIVE: ')
                print(traceback.format_exc())
                statuses = {'Failed to push to main data!'}


            return statuses

        except:
            print('api failed: ', traceback.format_exc())
            return 'Failure'   


if __name__ == '__main__':
    # Custom Swagger UI template configuration
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response


    app.run(debug=True, host= '0.0.0.0', port = 5003)
