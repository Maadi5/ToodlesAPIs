import requests
import json
import config

class WATI_APIS:
    def __init__(self):
        self.wati_endpoint = config.wati_end_point
        self.wati_auth = config.wati_auth
        self.significant_keys = {'phone': 'phone_number', 'fullName': 'name'}
        self.preloaded_contacts = self.get_contact_list()

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
    test.send_text_message_response(text_to_send='Sure! The 6 in 1 super desk is a multifunctional desk that can be transformed into 6 different functions. It can be used as a magnetic drawing easel, building block table, study desk with chair, water/sand sensory play, and a building block wall. It comes with a chair and 101 pcs of building blocks. It is suitable for ages 2-7 and is made of HDPE plastic. You can use any duplo blocks with it, and whiteboard/washable markers like crayola markers with the whiteboard easel. It folds back completely in 3 steps and can be stowed away when not in use.', contact_number='919176270768', contact_name='M A Adithya')
    contactlist = test.preloaded_contacts
    phone_number_list = [val['phone_number'] for val in contactlist]

    print('phone number list: ', phone_number_list)
    print(len(phone_number_list))
    woocommerce_contacts = pd.read_csv(r'C:\\woocommerce_contacts_w_names.csv')

    # for idx, row in woocommerce_contacts.iterrows():
    #     contact_name = row['Name']
    #     contact_number = str(row['Phone'])
    #     if contact_number not in phone_number_list:
    #         is_added = test.add_contact_number(contact_number=contact_number, contact_name=contact_name)