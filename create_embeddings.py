import openai
from openai.embeddings_utils import cosine_similarity, get_embedding
import pandas as pd
import numpy as np

openai.api_key = "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"

if __name__ == '__main__':
    with open('./toodles_doc.txt', 'r') as file:
        txt_prod_details = file.read()
    list_prod_details = txt_prod_details.split('<SEP>')
    print(list_prod_details)
    details_df = pd.DataFrame({'text':list_prod_details})
    print('getting embeddings')
    details_df['embedding'] = details_df['text'].apply(lambda x: get_embedding(x, engine = 'text-embedding-ada-002'))
    details_df.to_csv('./toodles_doc_embedding.csv')
