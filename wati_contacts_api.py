from flask import Flask, request
from flask_restx import Api, Resource, fields
from werkzeug.datastructures import FileStorage
import pandas as pd
import os
from google_sheets_apis import googlesheets_apis
from utils import match_cols, input_df_preprocessing, check_fields
import config
import traceback
from wati_apis import WATI_APIS
from email_sender import send_dispatch_email, send_usermanual_email, send_dispatch_usermanual_email, send_csv
from google_sheets_apis import googlesheets_apis
import logging

gsheets_db = googlesheets_apis(spreadsheet_id= config.db_spreadsheet_id)

app = Flask(__name__)
api = Api(app, version='1.0', title='CSV API', description='API for updating WATI contacts')

print('After creating api class')

csv_upload_model = api.model('CSVUpload', {
    'file': fields.Raw(required=True, description='CSV file')
})

upload_parser = api.parser()
upload_parser.add_argument('file', location='files',
                           type=FileStorage, required=True)

print('API Parser')

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
            df = pd.read_csv(csv_file)
            #print('read file')
            logging.info("read file")
            # df = input_df_preprocessing(df)
            tracker_df = gsheets_db.load_sheet_as_csv(sheet_name=config.db_sheet_name)
            wati_new_list = []
            for idx, row in df.iterrows():
                wati_number = row['Phone']
                if wati_number in list(tracker_df['phone_num']):
                    #number exists. Check if not 'cancelled'
                    if list(tracker_df[tracker_df['phone_num'] == wati_number]['status'])[0] not in {'cancelled'}:
                        row['attribute 1'] = 'customer'
                    else:
                        row['attribute 1'] = 'non_customer'
                else:
                    row['attribute 1'] = 'non_customer'
                wati_new_list.append(row)
            wati_updated_df = pd.DataFrame(wati_new_list)
            wati_updated_df.to_csv(r'wati_df.csv', index= False)
            status = send_csv(csvfile='wati_df.csv', subject='wati_list')
            return 'success'
        except:
            logging.error("email csv failed for wati df")
            logging.error(traceback.format_exc())
            return 'failure'


if __name__ == '__main__':
    # Custom Swagger UI template configuration
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response


    app.run(debug=True, host= '0.0.0.0', port = 5007)






