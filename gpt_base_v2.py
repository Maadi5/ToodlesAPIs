import sys
import os
import openai
from openai.embeddings_utils import cosine_similarity, get_embedding
import pandas as pd
import numpy as np

openai.api_key = "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"

class GPT_Inference():
    def __init__(self):
        self.details_df = pd.read_csv('./toodles_doc_embedding.csv')
        print(self.details_df)
    
    def search_notebook(self, df, search_term, n=3, pprint=True):
        # Convert the embeddings in the 'embedding' column from strings to numpy arrays. Run only if saving and loading the DF as CSV
        df["embedding"] = df["embedding"].apply(eval).apply(np.array)
        # Get the embedding for the `search_term` using the "text-embedding-ada-002" engine.
        search_embeddings = get_embedding(search_term, engine="text-embedding-ada-002")

        # Calculate the cosine similarity between
        df["similarity"] = df["embedding"].apply(
            lambda x: cosine_similarity(x, search_embeddings)
        )

        # Sort the notes by similarity in descending order and select the top `n` notes.
        results = df.sort_values("similarity", ascending=False).head(n)
        return results

    def answer_this(self, query):
      #get the closest matching embeddings
      search_df = self.search_notebook(self.details_df, query, 3, True)
      search_list = search_df.text.head(3).tolist()

      #prompt + openai call
      prompt = """You are meant to be a friendly and sassy humanized virtual assistant for our brand called Toodles. 
      We are a kid’s furniture brand and our products are aesthetic, multifunctional and encourage independence and free play. 
      \nInfo:""" + '\n'.join(search_list) +"\nAnswer the following query based on the above Info - \n" + query + '\n'
      print('PROMPT\n',prompt)
      
      response = openai.Completion.create(
          model = "text-davinci-003",
          max_tokens = 1000,
          temperature = 0.3,
          prompt = prompt
          )
      
      print(response)
      print(query)
      print(response['choices'][0]['text'])
      return response['choices'][0]['text']


if __name__ == '__main__':
    gpt_inference = GPT_Inference()
    print('Finished loading init')
    response = gpt_inference.answer_this('Tell me about the superdesk')
    print("Response to 'Tell me about the superdesk': ")
    print(response)
