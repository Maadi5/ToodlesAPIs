import os
import csv
import json
from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd
import config
import gspread

class googlesheets_apis():

    def __init__(self, spreadsheet_id, credentials_path= config.gsheet_credentails_path):
        # Load the credentials from the JSON key file
        self.credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=['https://www.googleapis.com/auth/spreadsheets'],
        )
        self.spreadsheet_id = spreadsheet_id
        # Build the Sheets API service
        self.service = build('sheets', 'v4', credentials=self.credentials)
        # Authenticate with the API
        self.gspread_gc = gspread.authorize(credentials= self.credentials)
        self.gspread_spreadsheet = self.gspread_gc.open_by_url('https://docs.google.com/spreadsheets/d/' + self.spreadsheet_id + '/edit#gid=0')

    def get_column_names(self, sheet_name):

        # Define the range to retrieve (first row in the sheet)
        range_name = f"{sheet_name}!1:1"

        # Retrieve the values from the first row (header row)
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
        ).execute()

        # Extract the column names from the result
        column_names = result.get('values', [])[0]

        column_dict = {}
        count0 = 0
        for idx, col_name in enumerate(column_names):
            if idx<=25:
                column_dict[col_name] = chr(idx + 65)
            elif idx>25 and idx<=(25+26):
                column_dict[col_name] = chr(65) + chr(65 + count0)
                count0 += 1
        col_index = {col_name: idx for idx, col_name in enumerate(column_names)}

        return column_names, column_dict, col_index

    def is_sheet_blank(self, sheet_name):
        try:
            # Get the sheet data
            range_name = f'{sheet_name}!A1'  # You can adjust the range if you want to check more cells
            result = self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])

            # If there are no values in the response, the sheet is considered blank
            if not values:
                return True
            return False
        except Exception as e:
            print(f"Error checking if the sheet is blank: {e}")
            return False

    def append_csv_to_google_sheets(self, csv_path, sheet_name):

        #Check if sheet already exists
        sheetname_list = self.get_sheet_names()
        print('sheetname list: ', sheetname_list)
        #If sheet does not already exists, add new sheet
        if sheet_name not in sheetname_list:
            self.add_sheet(sheet_name)
        # Read the CSV file
        with open(csv_path, 'r') as csv_file:
            csv_data = csv.reader(csv_file)
            data_to_append = list(csv_data)

        if self.is_sheet_blank(sheet_name=sheet_name):
            include_col_names = True
        else:
            include_col_names = False

        append = False
        if include_col_names == False and len(data_to_append)>1:
            data_to_append = data_to_append[1:]
            append = True
        elif include_col_names == True and len(data_to_append)>=1:
            append = True
        else:
            append = False

        if append:
            # Append the data to the Google Sheets
            range_name = f"{sheet_name}!A:A"  # Change the range as needed
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

    def get_sheet_names(self):
        try:
            # Get the spreadsheet data
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheets = spreadsheet.get('sheets', [])

            # Extract sheet names from the response
            sheet_names = [sheet['properties']['title'] for sheet in sheets]
            return sheet_names
        except Exception as e:
            print(f"Error getting sheet names: {e}")
            return []

    def get_sheet_data(self, sheet_name):
        try:
            # Get the values from the sheet by range
            result = self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=sheet_name).execute()
            values = result.get('values', [])
            return values
        except Exception as e:
            print(f"Error fetching data from the sheet: {e}")
            return None

    def query_data(self, sheet_name, filter_func):
        data = self.get_sheet_data(sheet_name)
        if data:
            if filter_func is not None:
                header_row = data[0]
                filtered_data = [row for row in data[1:] if filter_func(dict(zip(header_row, row)))]
                values = [header_row] + filtered_data
            else:
                values = data
            csv_list = []
            for _, val in enumerate(values[1:]):
                dfdict = {}
                for idx, v in enumerate(val):
                    dfdict[values[0][idx]] = v
                csv_list.append(dfdict)
            return pd.DataFrame(csv_list)
        else:
            return None

    def load_sheet_as_csv(self, sheet_name):

        # Define the range to retrieve (e.g., all data in the sheet)
        range_name = f"{sheet_name}"
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
            for idx, col in enumerate(values[0]):
                try:
                    dfdict[col] = val[idx]
                except:
                    dfdict[col] = ''
            csv_list.append(dfdict)

        return pd.DataFrame(csv_list)


    def add_sheet(self, sheet_name):
        try:
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }
            # Execute the request to add the new sheet
            response = self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id,
                                                          body={'requests': [request]}).execute()
            print(f"New sheet '{sheet_name}' added successfully!")
        except Exception as e:
            print(f"Error adding the new sheet: {e}")

    def add_columns_to_sheet(self, column_names, sheet_name):

        sheet_id = self.get_sheet_id(sheet_name)
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
        range_name = f"{sheet_name}!{chr(ord('A') + insert_index)}1:{chr(ord('A') + insert_index + len(column_names) - 1)}"

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

    def get_sheet_id(self, sheet_name):
        # Retrieve the spreadsheet properties
        spreadsheet = self.service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id
        ).execute()

        # Find the sheet with the specified name
        for sheet in spreadsheet['sheets']:
            properties = sheet['properties']
            if properties['title'] == sheet_name:
                return properties['sheetId']

        return None

    def update_cell(self, values_to_update, sheet_name):
        # Replace A1, B2, etc., with the cell addresses you want to update
        cell_updates = [{'range': f'{sheet_name}!' + str(dct['col']) + str(dct['row']), 'values': [[dct['value']]]} for dct in values_to_update]

        # Perform the batch update to update multiple cells at once
        request = self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={'valueInputOption': 'RAW', 'data': cell_updates}
        )
        response = request.execute()

    def sort_sheet(self, sheet_name, sorting_rule):
        sheet_id = self.get_sheet_id(sheet_name)
        # Sort the sheets based on the values in the specified column
        request_body = {
            "requests": [
                {
                    "sortSheet": {
                        "sheetId": sheet_id,
                        "sortSpecs": [
                            {
                                "dimensionIndex": sorting_rule['col'],
                                "sortOrder": sorting_rule['direction']  # Change to "DESCENDING" for descending order
                            }
                        ]
                    }
                }
            ]
        }

        # Execute the batchUpdate request to sort the sheets
        self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=request_body).execute()

    def update_dropdowns(self, dropdowns_to_update, sheet_name):
        sheet_id = self.get_sheet_id(sheet_name)
        # Define the data validation rule for the dropdown
        request = []
        for dd in dropdowns_to_update:
            validation_rule = dd['dropdown']
            dropdown_loc_row = dd['row']
            dropdown_loc_col = dd['col']

            # Create a request to update the cell with data validation
            r = {
                "setDataValidation": {#"repeatCell": {
                    "range": {
                        "sheetId": sheet_id,  # Use the correct sheet ID
                        "startRowIndex": dropdown_loc_row,  # Use the correct start row index
                        "endRowIndex": dropdown_loc_row+1,  # Use the correct end row index
                        "startColumnIndex": dropdown_loc_col,  # Use the correct start column index
                        "endColumnIndex": dropdown_loc_col+1,  # Use the correct end column index
                    },
                    'rule': validation_rule
                    # "cell": {
                    #     "dataValidation": validation_rule
                    # },
                    # "fields": "dataValidation"
                }
            }
            request.append(r)

        # Execute the request to add the dropdown
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id, body={'requests': request}).execute()
        print('Response: ', response)

    def get_row_numbers(self, column_name, target_values, sheet_name):

        # Get the range of the column data (e.g., 'Sheet1!A:A')
        column_range = f"{sheet_name}!{column_name}:{column_name}"

        # Retrieve the values from the specified column
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=column_range,
        ).execute()

        # Extract the values from the result
        column_values = result.get('values', [])

        # Find the row numbers of the target values in the column
        row_numbers = []
        for row_number, row_value in enumerate(column_values, 1):
            for target_value in target_values:
                if target_value in row_value:
                    row_numbers.append(row_number)

        return row_numbers

    def filter_query_data(self, sheet_name):
        # Define the filter criteria
        filter_criteria = "tracking_code_update != 'DL'"
        sheet_id = self.get_sheet_id(sheet_name)
        # Build the request to retrieve filtered data
        request = self.service.spreadsheets().values().batchGetByDataFilter(
            spreadsheetId= self.spreadsheet_id,
            body={
                "dataFilters": [
                    {
                        "gridRange": {
                            "sheetId": sheet_id,  # You can obtain the sheet_id using the Google Sheets API
                        },
                        "filterCriteria": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": ["DL"]
                            }
                        }
                    }
                ],
                "valueRenderOption": "UNFORMATTED_VALUE",
            }
        )

        # Execute the request to retrieve filtered data
        response = request.execute()

        # Extract and print the filtered data
        if 'valueRanges' in response:
            for value_range in response['valueRanges']:
                values = value_range.get('values', [])
                for row in values:
                    print(row)

    def delete_rows(self, sheet_name, rowids):
        sheet_id = self.get_sheet_id(sheet_name)

        for row_number in rowids:
            #range_to_delete = f"{sheet_name}!A{row_number}:Z{row_number}"

            request = self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={
                    "valueInputOption": "RAW",
                    "data": [
                        {
                            "range": f"{sheet_name}!A{row_number}",
                            "majorDimension": "ROWS",
                            "values": []
                        }
                    ]
                }
            )

            # # Delete the specified row by shifting the cells up
            # request.execute()

            response = request.execute()
            print(response)

    def add_new_sheet(self, new_sheet_name):
        requests = [
            {
                "addSheet": {
                    "properties": {
                        "title": new_sheet_name
                    }
                }
            }
        ]

        # Execute the request to add the new sheet
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id, body={'requests': requests}).execute()

        # Check the response to confirm the sheet was added
        if 'replies' in response:
            print(f"Sheet '{new_sheet_name}' added successfully.")
        else:
            print("Sheet addition failed.")

    def remove_sheet(self, sheet_name):
        sheet_id = self.get_sheet_id(sheet_name)
        requests = [
            {
                "deleteSheet": {
                    "sheetId": sheet_id
                }
            }
        ]

        # Execute the request to delete the sheet
        response = self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id, body={'requests': requests}).execute()

        # Check the response to confirm the sheet was deleted
        if 'replies' in response:
            print(f"Sheet with ID {sheet_id} deleted successfully.")
        else:
            print(f"Sheet deletion failed for sheet with ID {sheet_id}.")


    def add_buttons(self, button_locations, sheet_name):
        sheet_id = self.get_sheet_id(sheet_name)
        requests = []
        for b in button_locations:
            row_loc = b['row']
            col_loc = b['col']
            text = b['text']
            request = {
                "createTextbox": {
                    "textbox": {
                        "text": text,
                        "autofit": "AUTOFIT_NORMAL"
                    },
                    "anchor": {
                        "sheetId": sheet_id,
                        "overlayPosition": {
                            "startColumnIndex": col_loc,
                            "startRowIndex": row_loc
                        },
                    }
                }
            }
            requests.append(request)


        drawing_request = {
            "requests": requests
        }

        # Execute the drawing request to add the text box to the cell
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=drawing_request
        ).execute()

    def get_sheet_names(self):
        # Call the Google Sheets API to get the sheet names
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        return sheets

        # Extract and print the sheet names
        sheet_names = [sheet['properties']['title'] for sheet in sheets]
    def delete_rows2(self, sheet_name, rowids):
        # Get the worksheet by title or other methods
        if rowids:
            worksheet = self.gspread_spreadsheet.worksheet(sheet_name)

            # Get the index of the worksheet
            worksheet_index = worksheet.index
            worksheet = self.gspread_spreadsheet.get_worksheet(index=worksheet_index)
            minval = rowids[0]

            jump = 0
            for idx, r in enumerate(rowids):
                print('doing delete operation for ', r)
                #if idx>0:
                if r<minval:
                    final_row = r
                    minval = r
                elif r>=minval:
                    final_row = r-jump
                jump += 1
                worksheet.delete_rows(final_row, final_row)
            # self.gspread_spreadsheet.update_worksheet(worksheet, value_input_option='RAW')
            # Save changes by updating cells (replace cell values with empty strings)
            # worksheet.update([[""] * len(worksheet.row_values(1)) for _ in range(r, r+2)])

            # Resize the worksheet to remove the empty rows
            # worksheet.resize(rows=len(worksheet.get_all_values()))
            # # Check the response to ensure the row was deleted
            # if 'replies' in response and response['replies'][0].get('deleteDimension', {}).get('rowCount', 0) == 1:
            #     print(f"Row {rowid} deleted successfully.")
            # else:
            #     print(f"Row {rowid} deletion failed.")

# # Usage example:
# csv_file_path = os.path.join(os.getcwd(), 'order_tracker2.csv')
# google_sheets_id = '1CfdXQAtmQAmDbB0DjhmJqC3YnoluUmhEIgm75T1tvNU'
# sheet_name = 'Sheet1'  # Replace with the desired sheet name

# append_csv_to_google_sheets(csv_file_path, google_sheets_id, sheet_name)


if __name__ == '__main__':
    googlesheet = googlesheets_apis(spreadsheet_id=config.crm_spreadsheet_id)

    # cols, coldict = googlesheet.get_column_names()
    # # # googlesheet.append_csv_to_google_sheets(os.path.join(os.getcwd(), 'order_tracker2.csv'))
    # # out = googlesheet.load_sheet_as_csv()
    # # id = googlesheet.get_sheet_id()
    # # print('id: ', id)
    # # googlesheet.add_columns_to_sheet(['hi da', 'h2blu'])
    # # print(out.columns)
    # # out.to_csv(os.path.join(os.getcwd(), 'testing.csv'))
    # print('cols: ', cols, 'col_dict: ', coldict)
    # googlesheet.update_cell([{'col':'Q', 'row':'1', 'value':'Success'}])
    dropdown_payload = {
        "condition": {
            "type": "ONE_OF_LIST",
            "values": [{'userEnteredValue': 'Resolved'}, {'userEnteredValue': 'Delay by 2 hours'}]
        },
        "showCustomUi": True
    }
    # googlesheet.update_dropdowns(dropdowns_to_update=[{'dropdown': dropdown_payload, 'row': 7, 'col': 7}], sheet_name=config.crm_open_sheet_name)

    # googlesheet.sort_sheet(sheet_name=config.crm_open_sheet_name, sorting_rule={'col': 10, 'direction': 'ASCENDING'})

    gdb = googlesheets_apis(spreadsheet_id=config.db_spreadsheet_id)
    #query = f"SELECT unique_id, awb, name, phone_num, invoice_number, channel_order_number, order_date, shipping_mode WHERE tracking_code_update != 'DL'"
    # gdb.filter_query_data(sheet_name='dev_test')

    gdb.delete_rows2(sheet_name='dev_test', rowids= [149,147,151])
    # filter_func = lambda row: row['phone_num'] == '919900159770'
    # out = googlesheet.query_data(sheet_name=config.db_sheet_name, filter_func= filter_func)
    # # out = googlesheet.get_row_numbers(column_name='A', target_values=['13892283644'])
    # print(out)
    # print(out.shape)
    # print(out.values.tolist())