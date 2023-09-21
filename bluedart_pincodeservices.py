
from zeep import Client

# Define the WSDL URL
wsdl_url = "https://netconnect.bluedart.com/Ver1.10/ShippingAPI/Finder/ServiceFinderQuery.svc?wsdl"

# Define the method name
method_name = "GetDomesticTransitTimeForPinCodeandProduct"

# Define the input parameters
pincode = "600020"  # Replace with the desired pincode
pincode_to = "600020"
profile = {
    'LoginID': 'MAA10825',
    'LicenceKey': 'tfejtqvulkohuofsqljpjm0hgf1kteml',
    'Api_type': 's',
    'Area': 'MAA'}


# Create a SOAP client
client = Client(wsdl=wsdl_url)

# Call the SOAP method
# result = client.service.GetDomesticTransitTimeForPinCodeandProduct(pPinCodeFrom=pincode, pPinCodeTo=pincode_to,
#                                                                    pProductCode=,pSubProductCode=,pPudate=,pPickupTime=,
#                                                                    profile=profile)
result = client.service.GetServicesforPincode(pinCode=pincode,profile=profile)

print(result)
# # Process the result
# service_details = result.ServiceCenterDetailsReference
#
# # Print the available services
for service in result:
    print("Service Name:", service.ServiceName)
    print("Service Code:", service.ServiceCode)
    print("Transit Days:", service.TransitDays)
    print("===================================")