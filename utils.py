import traceback

import pandas as pd
import re
import json
import os
import logging

# Configure the logger
logging.basicConfig(
    filename='postapi_logs.log',  # Specify the log file name
    level=logging.DEBUG,        # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def sum_amounts_across_order(browntape_df, field = 'Entity Discount Amount'):
    updated_bt_df = []
    item_level_discount_add = []
    for idx, row in browntape_df.iterrows():
        if updated_bt_df and updated_bt_df[-1]['Order Id'] != row['Order Id']:
            valid_float_discounts = []
            for val in item_level_discount_add:
                try:
                    valid_float_discounts.append(float(str(val.replace(',', ''))))
                except:
                    pass
            if len(valid_float_discounts) > 1:
                total_discount_val = sum(valid_float_discounts)
                for val in range(len(item_level_discount_add)):
                    index = -1 * (val + 1)
                    updated_bt_df[index][field] = total_discount_val
            item_level_discount_add = []
        item_level_discount_add.append(row[field])
        updated_bt_df.append(row)
    return pd.DataFrame(updated_bt_df)

def fix_amount_summation(browntape_df):

    try:
        browntape_df = sum_amounts_across_order(browntape_df= browntape_df, field = 'Order Total Discount Value')
    except:
        logging.error('In utils, error while summing discount')
        logging.error(traceback.format_exc())

    try:
        browntape_df = sum_amounts_across_order(browntape_df= browntape_df, field = 'Shipping Tax')
    except:
        logging.error('In utils, error while summing shipping tax')
        logging.error(traceback.format_exc())

    try:
        browntape_df = sum_amounts_across_order(browntape_df=browntape_df, field='Net Shipping')
    except:
        logging.error('In utils, error while summing net shipping amount')
        logging.error(traceback.format_exc())

    try:
        browntape_df = sum_amounts_across_order(browntape_df=browntape_df, field='Gross Shipping Amount')
    except:
        logging.error('In utils, error while summing gross shipping amount')
        logging.error(traceback.format_exc())

    return browntape_df


def match_cols(csvfile, col_names):
    fixed_dflist = []
    if len(set(csvfile.columns).difference(set(col_names))) == len(set(col_names).difference(set(csvfile.columns))) == 0:
        for idx, row in csvfile.iterrows():
            dfdict = {}
            for c in col_names:
                dfdict[c] = row[c]
            fixed_dflist.append(dfdict)
    elif len(set(csvfile.columns).difference(set(col_names)))< len(set(col_names).difference(set(csvfile.columns))):
        for idx, row in csvfile.iterrows():
            dfdict = {}
            for c in col_names:
                if c in list(csvfile.columns):
                    dfdict[c] = row[c]
                else:
                    dfdict[c] = 'Not Applicable'
            fixed_dflist.append(dfdict)
    return pd.DataFrame(fixed_dflist)

# Convert all values to strings and remove the '.' for numbers
def custom_to_string(val):
    if isinstance(val, int):
        return str(int(val))  # Convert number to string without the '.'
    elif isinstance(val, float):
        return str(val)


def validate_email(email):
    # Regular expression for a simple email validation
    pattern = r'^\S+@\S+\.\S+$'

    # Use re.match to check if the email matches the pattern
    if re.match(pattern, email):
        return True
    else:
        return False


def clean_phone_number(phone_number):
    # Remove all non-digit characters
    if len(phone_number)>10 and phone_number[0] == '0':
        phone_number = ''.join(phone_number[1:])
    cleaned_number = re.sub(r'\D', '', phone_number)

    # Check if the cleaned number has a valid length
    if len(cleaned_number) == 10:
        return cleaned_number
    elif len(cleaned_number) == 12 and cleaned_number.startswith('91'):
        return cleaned_number[2:]
    else:
        return None


def forced_float_removal(val):
    if val[-2:] == '.0':
        val = val[:-2]
    return val

def check_fields(val, field):
    if field == 'email_id':
        validate = validate_email(val)
        if validate == True:
            verdict = True
        elif val == '':
            verdict = True
        else:
            verdict = 'email pattern match failed: ' + val

    elif field == 'phone_num':
        clean_number = clean_phone_number(val)
        if clean_number is None:
            verdict = 'phone-num pattern fail: ' + val
        else:
            if float(clean_number[0])<6:
                verdict= 'phone-num unusual: ' + val
            else:
                verdict = True
    elif field in {'awb', 'pincode', 'state', 'city', 'status'}:
        if val:
            verdict = True
        else:
            field_name = ' '.join(field.split('_'))
            verdict = field_name + ' missing'
    else:
        verdict= True
    return verdict




def input_df_preprocessing(df):
    df.fillna('', inplace= True)
    # df = df.applymap(custom_to_string)
    df = df.applymap(str)
    df = df.applymap(forced_float_removal)
    df = fix_amount_summation(browntape_df=df)
    # df['Order Id'] = df['Order Id'].astype(str)
    # df['Phone'] = df['Phone'].astype(str)

    return df

if __name__ == '__main__':
    browntape_df = pd.read_csv(r'/Users/adithyam.a/Downloads/btreport_894565.csv', index_col = False)
    browntape_df = input_df_preprocessing(browntape_df)
    # browntape_df = fix_amount_summation(browntape_df)
    browntape_df.to_csv(r'/Users/adithyam.a/Downloads/btreport_894565_fixedamounts.csv', index= False)
    # sum_amounts_across_order(browntape_df)
