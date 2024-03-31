from flask import Flask, request
from flask_restx import Api, Resource, fields
from werkzeug.datastructures import FileStorage
import pandas as pd
import os
from google_sheets_apis import googlesheets_apis
from utils import clean_phone_number
import config
import traceback
from wati_apis import WATI_APIS
from email_sender import send_dispatch_email, send_usermanual_email, send_dispatch_usermanual_email, send_csv
from google_sheets_apis import googlesheets_apis
import logging
from copy import deepcopy

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

accessory_skus = {'MN-ACS-001',
'MN-ACS-002',
'MN-ACS-004',
'MN-ACS-003-BLUE',
'MN-ACS-003-GREEN',
'MN-ACS-007',
'MN-ACS-005',
'MN-ACS-008',
'MN-ACS-009-GREEN',
'MN-ACS-009-BLUE',
'MN-ACS-010',
'SBI-ACS-001',
'SBI-ACS-002',
'SBI-ACS-003',
'SBI-ACS-004',
'SBI-ACS-005',
'MN-ACS-003-PINK',
'MN-ACS-003-PURPLE',
'MN-ACS-009-PINK',
'MN-ACS-009-PURPLE',
'MN-O-005'}

furniture_skus = {
'YK-KW-007-2',
'YK-KW-006',
'YK-PZ-015-2',
'YK-YH-001-3',
'YK-KW-012',
'YK-KW-006-1',
'YK-SQ-022-3 - WHITE',
'YK-SQ-022-3 - PINK',
'YK-SQ-022-1',
'YK-NH-006 - PINK',
'YK-NH-006 - BLU & YEL',
'YK-PZ-007 - BLUE',
'YK-PZ-007 - PINK',
'YK-PZ-007 - WHITE',
'YK-PZ-002-2 - PINK',
'YK-PZ-002-2 - GREY',
'YK-PZ-002-2 - BLUE',
'YK-SQ-022-4',
'YK-SQ-022-2',
'YK-KW-027',
'YK-NH-006 - GREEN',
'YK-KW-080',
'YK-YH-001-3-YEL',
'MN-O-005',
'MN-B-002',
'MN-O-006',
}

def update_wati_df(tracker_df, wati_df):
    wati_updated_list = []
    for idx, row in wati_df.iterrows():
        wati_number = str(row['Phone'])
        dictrow = deepcopy(dict(row))
        try:
            dictrow['CountryCode'] = deepcopy(row['Country code'])
            del dictrow['Country code']
        except:
            pass
        try:
            del dictrow['attribute_1']
            del dictrow['attribute_2']
        except:
            pass
        dictrow['attribute 1'] = ''
        dictrow['attribute 2'] = ''
        cleaned_wati_number = clean_phone_number(wati_number)
        if type(cleaned_wati_number) == str:
            fixed_number = cleaned_wati_number
        else:
            fixed_number = wati_number

        dictrow['Phone'] = fixed_number

        if fixed_number in list(tracker_df['phone_num']):
            # number exists. Check if not 'cancelled'
            if list(tracker_df[tracker_df['phone_num'] == fixed_number]['status'])[0] not in {'cancelled'}:
                primary_sku = None
                try:
                    skus_of_customer = list(tracker_df[tracker_df['phone_num'] == fixed_number]['sku'])
                    # for furn_sku in furniture_skus:
                    #     if furn_sku in skus_of_customer:
                    #         primary_sku = furn_sku
                    #         break
                    # if primary_sku is None:
                    #     primary_sku = skus_of_customer[0]
                    comma_separated_skus = ','.join(skus_of_customer)
                    dictrow['attribute 2'] = comma_separated_skus
                except:
                    print('sku capture failed')

                dictrow['attribute 1'] = 'customer'

                # print('#######  NUMBER FOUND  ###########!')

            elif len(str(dictrow['awb_number'])) != 3:
                dictrow['attribute 1'] = 'customer'
            else:
                dictrow['attribute 1'] = 'non_customer'

        elif len(str(dictrow['awb_number'])) != 3:
            dictrow['attribute 1'] = 'customer'
        else:
            dictrow['attribute 1'] = 'non_customer'
        # print(dictrow)
        wati_updated_list.append(dictrow)
    # print('FINAL DF LIST')
    # print(wati_updated_list)
    wati_updated_df = pd.DataFrame(wati_updated_list)
    return wati_updated_df

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
            wati_updated_df = update_wati_df(tracker_df=tracker_df, wati_df=df)
            wati_updated_df.to_csv(r'wati_df.csv', index= False)
            status = send_csv(csvfile='wati_df.csv', subject='wati_list')
            return 'success'
        except:
            logging.error("email csv failed for wati df")
            logging.error(traceback.format_exc())
            print(traceback.format_exc())
            return 'failure'


if __name__ == '__main__':
    # df = pd.read_csv('wati_contacts2.csv', index_col=False)
    # gsheets_db = googlesheets_apis(spreadsheet_id=config.db_spreadsheet_id)
    # tracker_df = gsheets_db.load_sheet_as_csv(sheet_name=config.db_sheet_name)
    # wati_updated_df = update_wati_df(tracker_df=tracker_df, wati_df=df)
    # wati_updated_df.to_csv(r'wati_df.csv', index=False)


    # Custom Swagger UI template configuration
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response


    app.run(debug=True, host= '0.0.0.0', port = 5007)






