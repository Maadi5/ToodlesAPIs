import requests
import xmltodict
import json
import config

loginid = 'MAA10825'
awb = '50914641713'
apikey = 'mmfroorqlkeuitqrifsopmnfthlqlsjx'

class bluedart_apis():
    def get_tracking_details(self, awb):
        url = "https://api.bluedart.com/servlet/RoutingServlet?handler=tnt&action=custawbquery&loginid=" + config.loginid_bluedart + "&awb=awb&numbers=" + awb + "&format=xml&lickey=" + config.apikey_bluedart_tracking +"&verno=1.3&scan=1"

        # headers = {
        #     "Authorization": self.wati_auth
        # }
        response = requests.get(url)
        if str(response) == '<Response [200]>':
            print('success at get api for bluedart')
            tracking_payload = xmltodict.parse(response.content)
            print(tracking_payload)
            tracking_status = {}
            tracking_status['Status'] = tracking_payload['ShipmentData']['Shipment']['Status']
            tracking_status['ExpectedDeliveryDate'] = tracking_payload['ShipmentData']['Shipment']['ExpectedDeliveryDate']
            tracking_status['StatusType'] = tracking_payload['ShipmentData']['Shipment']['StatusType']
            tracking_status['Scans'] = tracking_payload['ShipmentData']['Shipment']['Scans']['ScanDetail']
            return tracking_status
        else:
            return None

bluedartapis = bluedart_apis()
tracking_status = bluedartapis.get_tracking_details(awb = '50914641713')
print(tracking_status['ExpectedDeliveryDate'])
print(tracking_status['Status'])
print(tracking_status['StatusType'])
