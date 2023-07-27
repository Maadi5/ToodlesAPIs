import pandas as pd
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
    if isinstance(val, (int, float)):
        return str(int(val))  # Convert number to string without the '.'
    else:
        return str(val)

def input_df_preprocessing(df):
    df.fillna('', inplace= True)
    df = df.applymap(custom_to_string)
    # df['Order Id'] = df['Order Id'].astype(str)
    # df['Phone'] = df['Phone'].astype(str)
    return df
