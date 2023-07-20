import os
import csv
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd


class googlesheets_apis():

    def __init__(self, spreadsheet_id, sheet_name, credentials_path):
        # Load the credentials from the JSON key file
        self.credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=['https://www.googleapis.com/auth/spreadsheets'],
        )
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        # Build the Sheets API service
        self.service = build('sheets', 'v4', credentials=self.credentials)

    def get_column_names(self):

        # Define the range to retrieve (first row in the sheet)
        range_name = f"{self.sheet_name}!1:1"

        # Retrieve the values from the first row (header row)
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
        ).execute()

        # Extract the column names from the result
        column_names = result.get('values', [])[0]

        column_dict = {col_name: chr(idx + 65) for idx, col_name in enumerate(column_names)}

        return column_names, column_dict


    def append_csv_to_google_sheets(self, csv_path):
        # Read the CSV file
        with open(csv_path, 'r') as csv_file:
            csv_data = csv.reader(csv_file)
            data_to_append = list(csv_data)

        if len(data_to_append)>1:
            data_to_append = data_to_append[1:]
        # Append the data to the Google Sheets
            range_name = f"{self.sheet_name}!A:A"  # Change the range as needed
            value_input_option = 'RAW'  # You can also use 'USER_ENTERED' for more advanced formatting
            body = {'values': data_to_append}

            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            ).execute()

        else:
            print('No Data To Append')

    def load_sheet_as_csv(self):

        # Define the range to retrieve (e.g., all data in the sheet)
        range_name = f"{self.sheet_name}"
        # Retrieve the values from the specified range
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
        ).execute()

        # Extract the values from the result
        values = result.get('values', [])

        csv_list = []
        for _, val in enumerate(values[1:]):
            dfdict = {}
            for idx, v in enumerate(val):
                dfdict[values[0][idx]] = v
            csv_list.append(dfdict)

        return pd.DataFrame(csv_list)

    def add_columns_to_sheet(self, column_names):

        sheet_id = self.get_sheet_id()
        # Get the current column count in the sheet
        sheet_properties = self.service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id,
            ranges=[f"'Sheet1'!A1:Z1"],  # Adjust the range as needed
            fields='sheets.properties.gridProperties.columnCount',
        ).execute()

        grid_size = sheet_properties['sheets'][0]['properties']['gridProperties']['columnCount']
        # Calculate the position to insert the new columns (startIndex)
        insert_index = grid_size  # 0-based indexing

        current_column_count = sheet_properties['sheets'][0]['properties']['gridProperties']['columnCount']

        # Calculate the position to insert the new columns (startIndex)
        #insert_index = current_column_count  # 0-based indexing

        # Define the request to add columns
        request_body = {
            'requests': [
                {
                    'insertDimension': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': insert_index,
                            'endIndex': insert_index + len(column_names),
                        },
                        'inheritFromBefore': False,
                    }
                }
            ]
        }

        # Send the request to add columns
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=request_body
        ).execute()

        # Update the values in the added columns with the specified value ('Not Applicable')
        range_name = f"{self.sheet_name}!{chr(ord('A') + insert_index)}1:{chr(ord('A') + insert_index + len(column_names) - 1)}"

        values_to_update = [['Not Applicable'] * len(column_names)]
        request_body = {
            'valueInputOption': 'RAW',
            'data': [
                {
                    'range': range_name,
                    'values': values_to_update,
                }
            ]
        }

        # Send the request to update the values in the added columns
        response = self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=request_body
        ).execute()

    def get_sheet_id(self):
        # Retrieve the spreadsheet properties
        spreadsheet = self.service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id
        ).execute()

        # Find the sheet with the specified name
        for sheet in spreadsheet['sheets']:
            properties = sheet['properties']
            if properties['title'] == self.sheet_name:
                return properties['sheetId']

        return None

    def update_cell(self, values_to_update):
        # Replace A1, B2, etc., with the cell addresses you want to update
        cell_updates = [{'range': f'{self.sheet_name}!' + str(dct['col']) + str(dct['row']), 'values': [[dct['value']]]} for dct in values_to_update]

        # Perform the batch update to update multiple cells at once
        request = self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'valueInputOption': 'RAW', 'data': cell_updates}
        )
        response = request.execute()


# # Usage example:
# csv_file_path = os.path.join(os.getcwd(), 'order_tracker2.csv')
# google_sheets_id = '1CfdXQAtmQAmDbB0DjhmJqC3YnoluUmhEIgm75T1tvNU'
# sheet_name = 'Sheet1'  # Replace with the desired sheet name

# append_csv_to_google_sheets(csv_file_path, google_sheets_id, sheet_name)


if __name__ == '__main__':
    googlesheet = googlesheets_apis(spreadsheet_id='1dnLgADu0BgLKIh2riM2OZ6SVEQvHADJ3pZ6AsglLttY',
                                    sheet_name= 'Sheet1', credentials_path= r'C:\Users\Adithya\Downloads\userdataminiture-8a7384575c3f.json')

    cols, coldict = googlesheet.get_column_names()
    # # googlesheet.append_csv_to_google_sheets(os.path.join(os.getcwd(), 'order_tracker2.csv'))
    # out = googlesheet.load_sheet_as_csv()
    # id = googlesheet.get_sheet_id()
    # print('id: ', id)
    # googlesheet.add_columns_to_sheet(['hi da', 'h2blu'])
    # print(out.columns)
    # out.to_csv(os.path.join(os.getcwd(), 'testing.csv'))
    print('cols: ', cols, 'col_dict: ', coldict)
    googlesheet.update_cell([{'col':'Q', 'row':'1', 'value':'Success'}])