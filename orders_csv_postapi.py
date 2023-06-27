from flask import Flask, request
from flask_restx import Api, Resource, fields
from werkzeug.datastructures import FileStorage
import pandas as pd
import os
from order_report_process import get_order_details
from email_sender import send_dispatch_email
from wati_apis import WATI_APIS


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
        args = upload_parser.parse_args()
        csv_file = args['file']
        df = pd.read_csv(csv_file)
        to_be_pushed = get_order_details(df)
        trackerdf = pd.read_csv(os.path.join(os.get_cwd(), 'order_tracker.csv'))

        statuses = []

        for idx, row in to_be_pushed.iterrows():
            try:
                id = row['unique_id']
                email = row['email_id']
                phone_num = row['phone_num']
                name = row['name']
                awb = row['awb']
                ## send template message
                try:
                    custom_params=[{'name': 'awb', 'value': awb}]
                    status = wati.send_template_message(contact_name=name, template_name='order_dispatched_with_awb', 
                                            custom_params=custom_params)
                    if not status:
                        trackerdf[trackerdf['unique_id'] == id]['whatsapp_status'] = 'Failure'
                        wa_status = 'Failure'
                    else:
                        trackerdf[trackerdf['unique_id'] == id]['whatsapp_status'] = 'Success'
                        wa_status = 'Success'
                except:
                    trackerdf[trackerdf['unique_id'] == id]['whatsapp_status'] = 'Failure_exception'
                    wa_status = 'Failure_exception'
                
                ## send email
                try:
                    status = send_dispatch_email(name= name, to_address= email, awb_number=awb)
                    trackerdf[trackerdf['unique_id'] == id]['email_status'] = status
                    email_status = status
                except:
                    trackerdf[trackerdf['unique_id'] == id]['email_status'] = 'Failure_exception'
                    email_status = 'Failure_exception'
                statuses.append({'id': id, 'email_status': email_status, 'wa_status': wa_status})
            except:
                trackerdf.to_csv(os.path.join(os.get_cwd(), 'order_tracker.csv'))
            

        trackerdf.to_csv(os.path.join(os.get_cwd(), 'order_tracker.csv'))


        return statuses


if __name__ == '__main__':
    # Custom Swagger UI template configuration
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response


    app.run(debug=True, port = 5003)
