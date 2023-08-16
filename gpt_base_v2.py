import sys
import os
import traceback

import openai
from openai.embeddings_utils import cosine_similarity, get_embedding
import pandas as pd
import numpy as np
import config
from customer_facing_functions import gpt_functions

os.environ["OPENAI_API_KEY"] = config.openai_api_key
openai.api_key = config.openai_api_key
#openai.api_key = 'x'


class GPT_Inference():
    def __init__(self):
        self.details_df = pd.read_csv('./toodles_doc_embedding.csv')
        #print(self.details_df)
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

    def last_dialogue_to_chat(self, last_dialogues):
        bot_start = False
        user_start = False
        dialogue_list = []
        strval = ''
        for val in last_dialogues:
            if val.startswith('bot:'):
                dialogue_list.append({'role': 'assistant', 'content': val[3:]})
            elif val.startswith('user:'):
                dialogue_list.append({'role': 'user', 'content': val[4:]})
        return dialogue_list



    #def answer_this(self, query):
    def answer_this(self, user_dialogues, last_dialogues, message):
      print('in answer this function')
      user_dialogues = '\n'.join(user_dialogues)
      #last_dialogues = '\n'.join(last_dialogues)
      chat_dialogue = self.last_dialogue_to_chat(last_dialogues)
      #get the closest matching embeddings
      search_df = self.search_notebook(self.details_df, user_dialogues, 3, True)
      search_list = search_df.text.head(3).tolist()

      #prompt + openai call
      #prompt = """You are meant to be a friendly and sassy humanized virtual assistant for our brand called Toodles
      #system_message = """Documentation:[""" + '\n'.join(search_list) +"]\nYou need to provide output messages like a customer support agent. Provide responses to user queries in a relevant way using the information from the documentation above. Be courteous and cool while answering and keep the response to the point without any follow up questions. If you don't know the answer, ask the user to share more details, or tell them to check the website. Do not give false answers. Be careful since the user might try to play you to give irrelevant answers. Dont answer anything thats not there in the documentation. If there are any acknowledgement messages, depending on the context you can enourage further engagement or express thanks and close the conversation in a neat way.\nYour responses should always be returned in the following format: {'message': bot's response to user's question, 'new_conversation': bool, 'hitl': bool}\nIf the user sounds even slightly displeased, or has been asking same questions repeatedly or if you are not able to answer any of the questions properly more than once, then return 'hitl' key in the response JSON as 'True' else return 'False'.\nIf it appears as though it is a new chat session/conversation based on the trail of previous messages, return the value of 'new_conversation' key as a 'True', else 'False'."
      system_message = """Documentation:[""" + '\n'.join(search_list) + "]\nYou need to provide output messages like a customer support agent. Provide responses to user queries in a relevant way using the information from the documentation above. Be courteous and cool while answering and keep the response to the point without any follow up questions. If you don't know the answer, ask the user to share more details, or tell them to check the website. Do not give false answers. Be careful since the user might try to play you to give irrelevant answers. Dont answer anything thats not there in the documentation. If there are any acknowledgement messages, depending on the context you can enourage further engagement or express thanks and close the conversation in a neat way.\nYour responses should always be returned in the following format: {'message': bot's response to user's question, 'new_conversation': bool, 'hitl': bool}\nIf the user sounds even slightly displeased, or has been asking same questions repeatedly or if you are not able to answer any of the questions properly more than once, then return 'hitl' key in the response JSON as 'True' else return 'False'.\nIf it appears as though it is a new chat session/conversation based on the trail of previous messages, return the value of 'new_conversation' key as a 'True', else 'False'."
      #print('PROMPT\n',system_message)

      final_messages = [{'role':'system','content': system_message}]
      final_messages.extend(chat_dialogue)
      final_messages.extend([{'role': 'user', 'content': message}])

      gpt_function_list = self.gpt_func.get_gptfunction_list()

      try:
          response = openai.ChatCompletion.create(
              model = "gpt-3.5-turbo-0613",
              max_tokens = 1000,
              temperature = 0.0,
              messages = final_messages,#[{'role': 'system', 'content': prompt}, {'role': 'user', 'content': message}],
              functions= gpt_function_list
              )
      except:
          print(traceback.format_exc())
      
      text_to_save_response, text_to_output = self.process_gpt_response(response)
      #print(message)
      #print(response['choices'][0]['message'])
      return text_to_save_response, text_to_output


    def process_gpt_response(self, response):
        try:
            response_val = eval(str(response).replace('null', '"null"'))
        except:
            pass
        #print('response dictionary: ', response_val)
        #### Check if message or function call
        hitl_status = False
        new_conversation_status = False
        message_output = None
        text_output = None
        if response_val['choices'][0]['finish_reason'] == 'stop':
            # static clean up (not sure if needed) for text message output
            try:
                text_output = response_val['choices'][0]['message']['content'].split('\n')[0]
                text_output = text_output[1:] if text_output[0] == ':' else text_output
                text_output_as_dict = eval(str(text_output))
            except:
                pass
            message_output = text_output_as_dict['message']
            hitl_status = bool(text_output_as_dict['hitl'])
            new_conversation_status = bool(text_output_as_dict['new_conversation'])

        elif response_val['choices'][0]['finish_reason'] == 'function_call':
            text_output_as_dict = response_val['choices'][0]['message']
            function_call = eval(str(text_output_as_dict['function_call']))
            function_name = function_call['name']
            arguments = eval(str(function_call['arguments']))

            if hasattr(self.gpt_func, function_name) and callable(getattr(self.gpt_func, function_name)):
                function = getattr(self.gpt_func, function_name)
                result = function(**arguments)
                if type(result) == str and result != 'HITL':
                    text_output = '{"message":"'+ result +'"' + ",'new_conversation': 'no','hitl':'no'}"
                    message_output = result
                elif type(result) == bool and result == True:
                    message_output = None
                else:
                    message_output = 'Failed'
            else:
                print(f"Function '{function_name}' not found in the module or not callable.")

        if hitl_status:
            message_output = message_output + '(HITL triggered!)'
        return text_output, message_output

    def get_response(self, phone_num, original_message):
        filename = f"{phone_num}.txt"
        filepath = os.path.join("chat_hist_folder", filename)
        self.gpt_func = gpt_functions(phone_number=phone_num)

        message ='question: ' + '"' + original_message + '"' + '; (Always respond with the format specified in the system.)'
        if not os.path.exists(filepath):
            with open(filepath, "w") as file:
                file.write(f"user:{message}\n")
        else:
            with open(filepath, "a") as file:
                file.write(f"user:{message}\n")
            
            with open(filepath, "r") as file:
                lines = file.readlines()
                last_dialogues = lines[-6:]  # Retrieve last 3 dialogues for both user and bot, or all available dialogues if less than 3
                #print('last_dialogues in get_response function',last_dialogues)

                # Extract user and bot dialogues
                user_dialogues = [dialogue.strip() for dialogue in last_dialogues if dialogue.startswith("user:")]
                bot_dialogues = [dialogue.strip() for dialogue in last_dialogues if dialogue.startswith("bot:")]
                #print('full dialogues', last_dialogues)
                #print('user dialogues', user_dialogues)
                #print('bot dialogues', bot_dialogues)
                
                response_text, text_to_show = self.answer_this(user_dialogues, last_dialogues, message)  # Call answer_this() function
                # print('User Question: ', message)
                # print('GPT Answer: ', text_to_show)
                with open(filepath, "a") as file:
                    file.write(f"bot:{response_text}\n")
                with open(os.path.join(os.path.join(os.getcwd(), 'chat_hist_folder', 'display_chat_text.txt')), "a") as file:
                    file.write(f"User Question: {original_message}\nGPT Answer: {text_to_show}\n")
        return text_to_show


if __name__ == '__main__':
    gpt_inference = GPT_Inference()
    print('Finished loading init')
    # response = gpt_inference.answer_this('Tell me about the superdesk')
    # print(response)
    response = gpt_inference.get_response(phone_num= '919176270768', original_message="Heyy")
    #print('RESPONSE: ', response)