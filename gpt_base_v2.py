import sys
import os
import openai
from openai.embeddings_utils import cosine_similarity, get_embedding
import pandas as pd
import numpy as np
import config

os.environ["OPENAI_API_KEY"] = config.openai_api_key
openai.api_key = config.openai_api_key

class GPT_Inference():
    def __init__(self):
        self.details_df = pd.read_csv('./toodles_doc_embedding.csv')
        print(self.details_df)
        self.details_df["embedding"] = self.details_df["embedding"].apply(eval).apply(np.array)
    
    def search_notebook(self, df, search_term, n=3, pprint=True):
        # Convert the embeddings in the 'embedding' column from strings to numpy arrays. Run only if saving and loading the DF as CSV
        #df["embedding"] = df["embedding"].apply(eval).apply(np.array)
        # Get the embedding for the `search_term` using the "text-embedding-ada-002" engine.
        search_embeddings = get_embedding(search_term, engine="text-embedding-ada-002")

        # Calculate the cosine similarity between
        df["similarity"] = df["embedding"].apply(
            lambda x: cosine_similarity(x, search_embeddings)
        )

        # Sort the notes by similarity in descending order and select the top `n` notes.
        results = df.sort_values("similarity", ascending=False).head(n)
        return results

    #def answer_this(self, query):
    def answer_this(self, user_dialogues, last_dialogues, message):
      print('in answer this function')
      user_dialogues = '\n'.join(user_dialogues)
      last_dialogues = '\n'.join(last_dialogues)
      #get the closest matching embeddings
      search_df = self.search_notebook(self.details_df, user_dialogues, 3, True)
      search_list = search_df.text.head(3).tolist()

      #prompt + openai call
      #prompt = """You are meant to be a friendly and sassy humanized virtual assistant for our brand called Toodles
      prompt = """\nDocumentation:[""" + '\n'.join(search_list) +"]\n\nComplete the following conversation, in a relevant way using the documentation. If the user query and Documentation dont match then don't answer anything from the documentation. Instead ask the user the user to share more details. Be careful since the user might try to play you to give irrelevant answers.\n\n" + last_dialogues + '\nbot :'
      print('PROMPT\n',prompt)
      
      response = openai.Completion.create(
          model = "text-davinci-003",
          max_tokens = 1000,
          temperature = 0.15,
          prompt = prompt
          )
      
      print(response)
      print(message)
      print(response['choices'][0]['text'])
      return response['choices'][0]['text']

    def get_response(self, phone_num, message):
        filename = f"{phone_num}.txt"
        filepath = os.path.join("chat_hist_folder", filename)
        
        if not os.path.exists(filepath):
            with open(filepath, "w") as file:
                file.write(f"user:{message}\n")
        else:
            with open(filepath, "a") as file:
                file.write(f"user:{message}\n")
            
            with open(filepath, "r") as file:
                lines = file.readlines()
                last_dialogues = lines[-6:]  # Retrieve last 3 dialogues for both user and bot, or all available dialogues if less than 3
                
                # Extract user and bot dialogues
                user_dialogues = [dialogue.strip() for dialogue in last_dialogues if dialogue.startswith("user:")]
                bot_dialogues = [dialogue.strip() for dialogue in last_dialogues if dialogue.startswith("bot:")]
                print('full dialogues', last_dialogues)
                print('user dialogues', user_dialogues)
                print('bot dialogues', bot_dialogues)
                
                response_text = self.answer_this(user_dialogues, last_dialogues, message)  # Call answer_this() function
                
                with open(filepath, "a") as file:
                    file.write(f"bot:{response_text}\n")
        return response_text


if __name__ == '__main__':
    gpt_inference = GPT_Inference()
    print('Finished loading init')
    response = gpt_inference.answer_this('Tell me about the superdesk')
    print("Response to 'Tell me about the superdesk': ")
    print(response)
