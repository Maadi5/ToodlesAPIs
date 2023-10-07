import requests
import json
import config
from miniture_wati_templates import chat_revive_message
class WATI_APIS:
    def __init__(self):
        self.wati_endpoint = config.wati_end_point
        self.wati_auth = config.wati_auth
        self.significant_keys = {'phone': 'phone_number', 'fullName': 'name'}
        self.preloaded_contacts = self.get_contact_list()

    def get_previous_n_chats(self, contact_number, n):
        url = "https://" + self.wati_endpoint +"/api/v1/getMessages/" + contact_number + "?pageSize=" + str(n) + "&pageNumber=1"

        headers = {
                    "Authorization": self.wati_auth
        }

        response = requests.get(url, headers=headers)
        if str(response) == '<Response [200]>':
            message_payload = json.loads(response.content.decode('utf8'))
        else:
            message_payload = {}
        return message_payload

    def send_template_message(self, contact_number, contact_name, template_name = "new_chat_v1", broadcast_name= "my_broadcast",
                              custom_params= None):#[{"name": "name", "value": "there"}]):

        if custom_params is None:
            custom_params = []
        if 'name' not in [v['name'] for v in custom_params]:
            custom_params.append({'name': 'name', 'value': contact_name})

        url = "https://" + self.wati_endpoint +"/api/v2/sendTemplateMessage?whatsappNumber=" + str(contact_number)

        contactlist = self.preloaded_contacts
        phone_number_list = [val['phone_number'] for val in contactlist]

        print('phone number list: ', phone_number_list)

        if contact_number not in phone_number_list:
            is_added = self.add_contact_number(contact_number= contact_number, contact_name= contact_name)
        else:
            print('phone number already exists')
            is_added = True

        if is_added:

            headers = {
                "content-type": "text/json",
                "Authorization": self.wati_auth
            }

            payload = {
                "template_name": template_name,
                "broadcast_name":broadcast_name,
                "parameters": custom_params
            }
            response = requests.post(url, headers=headers, data=json.dumps(payload))

            if str(response) == '<Response [200]>':
                print('successfully sent template message to ', contact_number)
                return True

            else:
                print(response.text)
                return False
        else:
            print('phone number add failed')
            return False

    def send_session_pdf_file(self, contact_number, filename_to_user, local_file_name):
        url = "https://" + self.wati_endpoint + "/api/v1/sendSessionFile/" + contact_number

        files = [
            ('file', (filename_to_user, open(
                local_file_name, 'rb'), 'application/pdf'))
        ]

        headers = {
            'Authorization': self.wati_auth,
        }

        response = requests.request(
            "POST", url, headers=headers, files=files)

        print(response.text)

    def send_text_message_response(self, text_to_send, contact_number, contact_name):
        conversion_dict = {"'": '%27', ' ': '%20', '.': '.'}

        ntext = []
        for t in text_to_send:
            if not (t.isalpha() or t.isdigit()):
                if t in conversion_dict:
                    ntext.append(conversion_dict[t])
                else:
                    ntext.append(conversion_dict[' '])
            else:
                ntext.append(t)
        ntext = ''.join(ntext)

        url = "https://" + self.wati_endpoint + "/api/v1/sendSessionMessage/" + contact_number + "?messageText=" + ntext

        headers = {
            "Authorization": self.wati_auth
        }
        contactlist = self.preloaded_contacts
        phone_number_list = [val['phone_number'] for val in contactlist]

        print('phone number list: ', phone_number_list)

        if contact_number not in phone_number_list:
            is_added = self.add_contact_number(contact_number= contact_number, contact_name= contact_name)
        else:
            print('phone number already exists')
            is_added = True

        if is_added:
            print('url: ', url)
            response = requests.post(url, headers=headers)
            print('response: ', response)
            if str(response) == '<Response [200]>':
                print('successfully sent template message to ', contact_number)
                return True

            else:
                print(response.text)
                return False
        else:
            print('sent text message response failed')


    def add_contact_number(self, contact_number, contact_name,
                              custom_params= None):

        if custom_params is None:
            custom_params = [{"name": "country","value": "india"}]

        url = "https://" + self.wati_endpoint +"/api/v2/sendTemplateMessage?whatsappNumber=" + str(contact_number)

        headers = {
            "content-type": "text/json",
            "Authorization": self.wati_auth
        }

        payload = {
            "customParams": custom_params,
            "name": contact_name
        }
        response = requests.post(url, json=payload, headers=headers)

        if str(response) == '<Response [200]>':
            print('successfully added contact number ', contact_number)
            return True
        else:
            print(response.text)
            return False


    def get_contact_list(self):
        url = "https://" + self.wati_endpoint +"/api/v1/getContacts"

        headers = {
            "Authorization": self.wati_auth
        }
        response = requests.get(url, headers=headers)
        if str(response) == '<Response [200]>':
            print('success')
        contact_list = json.loads(response.content.decode('utf8'))['contact_list']
        simplified_list = []
        for val in contact_list:
            dct = {}
            for k in self.significant_keys:
                dct[self.significant_keys[k]] = val[k]
            simplified_list.append(dct)
        return simplified_list



if __name__ == '__main__':
    import pandas as pd

    test = WATI_APIS()

    # preorder_customers = pd.read_csv(r'/Users/adithyam.a/Documents/woocommerce_contacts_w_names2.csv')
    # for idx, row in preorder_customers.iterrows():
    #     customer_name = row['Name']
    #     customer_phone_number = row['Phone']
    #     # estimated_delivery_date = 'static date string value'
    #     custom_params = []
    #     status = test.send_template_message(contact_name=customer_name, contact_number=customer_phone_number,
    #                                         template_name='miniture_reveal')#, custom_params=custom_params)
    #     print('sent to: ', customer_phone_number)

    # customers_to_revive = {
    # 'Afeefa': '917025292204',
    # 'Ruch': '917044057565'}
    #
    # for name, contact in customers_to_revive.items():
    #     status = chat_revive_message(wati=test, name=name, phone_num=contact)