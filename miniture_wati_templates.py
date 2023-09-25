import os
import json

usermanual_skus_without_video = {'YK-PZ-007 - BLUE', 'YK-PZ-007 - PINK', 'YK-PZ-007 - WHITE','YK-KW-080',
                                 'YK-KW-012'}


def usermanual_whatsapp(sku, product_name, product_manual, name,phone_num, wati):
    status = 'Failure'
    if sku in usermanual_skus_without_video:
        wati_template = 'miniture_usermanual_5'
    else:
        wati_template = 'miniture_usermanual_5'
    custom_params = [{'name': 'product_name', 'value': str(product_name)},
                     {'name': 'media_url', 'value': str(product_manual)}]
    wati_status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                        template_name=wati_template,
                                        custom_params=custom_params)
    if wati_status:
        status = 'Success'
    else:
        status = 'Failure'
    return status

def awb_whatsapp(awb,name, phone_num, wati):
    # awb = str(int(float(row['awb'])))
    custom_params = [{'name': 'awb_number', 'value': awb}]
    wati_status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                        template_name='order_dispatched_with_awb2',
                                        custom_params=custom_params)
    if wati_status:
        status = 'Success'
    else:
        status = 'Failure'
    return status
