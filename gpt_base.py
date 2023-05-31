from gpt_index import SimpleDirectoryReader, GPTListIndex, GPTSimpleVectorIndex, LLMPredictor, PromptHelper, ServiceContext
from langchain.chat_models import ChatOpenAI
import gradio as gr
import sys
import os
import config

os.environ["OPENAI_API_KEY"] = config.openai_api_key

class GPT_Inference():
    def __init__(self, max_input_size= 4096, num_outputs=512, max_chunk_overlap= 20,
                 chunk_size_limit = 20, model_name = 'text-davinci-003', temperature = 0.7):
        self.max_input_size = max_input_size
        self.num_outputs = num_outputs
        self.max_chunk_overlap = max_chunk_overlap
        self.chunk_size_limit = chunk_size_limit
        self.model_name = model_name
        self.temperature = temperature
        self.vector_index = self.construct_index(config.prompthelper_path)



    def construct_index(self, directory_path):

        prompt_helper = PromptHelper(self.max_input_size, self.num_outputs, self.max_chunk_overlap, chunk_size_limit=self.chunk_size_limit)
        llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=self.temperature, model_name=self.model_name, max_tokens=self.num_outputs))

        doc = SimpleDirectoryReader(directory_path).load_data()

        service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)

        index = GPTSimpleVectorIndex.from_documents(documents=doc, service_context=service_context)

        index.save_to_disk('index.json')

        return index

    #Q and A implementation. Update the below function to v2
    def get_response(self, prompt):
        vIndex = GPTSimpleVectorIndex.load_from_disk('index.json')
        # while True:
        response = vIndex.query(prompt, response_mode='compact')
        return response


if __name__ == '__main__':
    gpt_inference = GPT_Inference()
    print('Finished loading init')
    response = gpt_inference.get_response('Tell me about the superdesk')
    print("Response to 'Tell me about the superdesk': ")
    print(response)