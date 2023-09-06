import pandas as pd
import re
import json
import os

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
            verdict = 'email pattern match failed'

    elif field == 'phone_num':
        clean_number = clean_phone_number(val)
        if clean_number is None:
            verdict = 'phone-num pattern fail'
        else:
            if float(clean_number[0])<6:
                verdict= 'phone-num unusual'
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
    # df['Order Id'] = df['Order Id'].astype(str)
    # df['Phone'] = df['Phone'].astype(str)
    return df


