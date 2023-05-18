import requests
import json
import config

class WATI_APIS:
    def __init__(self):
        self.wati_endpoint = config.wati_end_point#'live-server-106096.wati.io'
        self.wati_auth = config.wati_auth#"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIxOWZkYmIyZC0wODVkLTQ4NTUtODRjZC0xOWM2MGIxNGUyN2YiLCJ1bmlxdWVfbmFtZSI6Im9wZXJhdGlvbnNAdG9vZGxlcy5pbiIsIm5hbWVpZCI6Im9wZXJhdGlvbnNAdG9vZGxlcy5pbiIsImVtYWlsIjoib3BlcmF0aW9uc0B0b29kbGVzLmluIiwiYXV0aF90aW1lIjoiMDUvMTUvMjAyMyAxODoxOTowNiIsImRiX25hbWUiOiIxMDYwOTYiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3JvbGUiOiJBRE1JTklTVFJBVE9SIiwiZXhwIjoyNTM0MDIzMDA4MDAsImlzcyI6IkNsYXJlX0FJIiwiYXVkIjoiQ2xhcmVfQUkifQ.4lApLxn8boU1H1IMN8HqDJlfzdHC3j5fwyZ7dzaUpjg"
        self.significant_keys = {'phone': 'phone_number', 'fullName': 'name'}
        self.preloaded_contacts = self.get_contact_list()

    def send_template_message(self, contact_number, contact_name, template_name = "new_chat_v1", broadcast_name= "my_broadcast",
                              custom_params= None):#[{"name": "name", "value": "there"}]):

        if custom_params is None:
            custom_params = []
        if 'name' not in [v['name'] for v in custom_params]:
            custom_params.append({'name': 'name', 'value': contact_name})

        url = "https://" + self.wati_endpoint +"/api/v2/sendTemplateMessage?whatsappNumber=" + contact_number

        contactlist = self.preloaded_contacts
        phone_number_list = [val['phone'] for val in contactlist]

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

    def add_contact_number(self, contact_number, contact_name,
                              custom_params= None):

        if custom_params is None:
            custom_params = [{"name": "country","value": "india"}]

        url = "https://" + self.wati_endpoint +"/api/v2/sendTemplateMessage?whatsappNumber=" + contact_number

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