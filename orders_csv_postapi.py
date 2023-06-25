from flask import Flask, request
from flask_restx import Api, Resource, fields
from werkzeug.datastructures import FileStorage
import pandas as pd



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
        # Perform operations on the DataFrame here

        # Example: Calculate the sum of values in the 'column_name' column
        print(df.columns)

        return {'sum': 'hi da'}


if __name__ == '__main__':
    # Custom Swagger UI template configuration
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response


    app.run(debug=True, port = 5000)
