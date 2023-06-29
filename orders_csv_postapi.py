from flask import Flask, request
from flask_restx import Api, Resource, fields
from werkzeug.datastructures import FileStorage
import pandas as pd
import os
from order_report_process import get_order_details
from email_sender import send_dispatch_email, send_usermanual_email, send_dispatch_usermanual_email
from wati_apis import WATI_APIS
import traceback
from product_manual_map import get_product_name_manual


wati = WATI_APIS()
app = Flask(__name__)
api = Api(app, version='1.0', title='CSV API', description='API for processing CSV files')

csv_upload_model = api.model('CSVUpload', {
    'file': fields.Raw(required=True, description='CSV file')
})

upload_parser = api.parser()
upload_parser.add_argument('file', location='files',
                           type=FileStorage, required=True)


@api.route('/process_csv')
class CSVProcessing(Resource):
    @api.expect(upload_parser)
    def post(self):
        try:
            args = upload_parser.parse_args()
            csv_file = args['file']
            df = pd.read_csv(csv_file)
            to_be_pushed = get_order_details(df)
            trackerdf = pd.read_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index_col=False)

            statuses = []

            for idx, row in to_be_pushed.iterrows():
                try:
                    id = row['unique_id']
                    sku = row['sku']
                    email = row['email_id']
                    phone_num = row['phone_num']
                    name = row['name']
                    awb = row['awb']
                    product_name, product_manual = get_product_name_manual(sku=sku)
                    ## send template message
                    try:
                        custom_params=[{'name': 'awb_number', 'value': awb}]
                        status = wati.send_template_message(contact_name=name, contact_number= phone_num, template_name='order_dispatched_with_awb',
                                                custom_params=custom_params)
                        if not status:
                            idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                            print('idx: ', idx)
                            trackerdf.at[idx, 'whatsapp_status'] = 'Failure'
                            wa_status = 'Failure'
                        else:
                            idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                            print('idx: ', idx)
                            trackerdf.at[idx, 'whatsapp_status'] = 'Success'
                            wa_status = 'Success'
                    except:
                        idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                        trackerdf.at[idx, 'whatsapp_status'] = 'Failure_exception'
                        wa_status = 'Failure_exception'
                        print('whatsapp failed: ', traceback.format_exc())

                    # ## send manual pdf
                    # try:
                    #     
                    #     custom_params=[{'name': 'product_name', 'value': str(product_name)},
                    #                    {'name': 'media_url', 'value': str(product_manual)}]
                    #     status = wati.send_template_message(contact_name=name, contact_number= phone_num, 
                    #     template_name='product_instructions_short_manual',custom_params=custom_params)
                    #     if not status:
                    #         trackerdf[trackerdf['unique_id'] == id]['usermanual_whatsapp_status'] = 'Failure'
                    #         wa_manual_status = 'Failure'
                    #     else:
                    #         trackerdf[trackerdf['unique_id'] == id]['usermanual_whatsapp_status'] = 'Success'
                    #         wa_manual_status = 'Success'
                    # except:
                    #     trackerdf[trackerdf['unique_id'] == id]['usermanual_whatsapp_status'] = 'Failure_exception'
                    #     wa_manual_status = 'Failure_exception'
                    #     print('whatsapp usermanual failed: ', traceback.format_exc())
                    
                    ## send email
                    try:
                        status = send_dispatch_usermanual_email(name= name, to_address= email, product_name=product_name, product_manual_link= product_manual, awb_number=awb)
                        idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                        trackerdf.at[idx, 'email_status'] = status
                        email_status = status
                    except:
                        idx = trackerdf.index[trackerdf['unique_id'] == id].tolist()[0]
                        trackerdf.at[idx, 'email_status'] = 'Failure_exception'
                        email_status = 'Failure_exception'
                        print('email failed: ', traceback.format_exc())

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
                    trackerdf_original = pd.read_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index_col = False)
                    trackerdf = pd.concat([trackerdf_original,trackerdf])
                    # trackerdf.to_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index = False)
            
            trackerdf_original = pd.read_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index_col = False)
            trackerdf = pd.concat([trackerdf_original,trackerdf])
            trackerdf.to_csv(os.path.join(os.getcwd(), 'order_tracker.csv'), index = False)

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
