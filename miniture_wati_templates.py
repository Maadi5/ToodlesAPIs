import os
import json
import pandas as pd

usermanual_skus_without_video = {'YK-PZ-007 - BLUE', 'YK-PZ-007 - PINK', 'YK-PZ-007 - WHITE','YK-KW-080',
                                 'YK-KW-012'}


def chat_revive_message(wati, name, phone_num, wati_template='miniture_message_reply_plain'):
    wati_status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                        template_name=wati_template)

    if wati_status:
        status = 'Success'
    else:
        status = 'Failure'

    return status

def delivery_delay_alarm_message(wati, name, phone_num,wati_template='delivery_delay_opsmessage'):
    wati_status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                        template_name=wati_template)

    if wati_status:
        status = 'Success'
    else:
        status = 'Failure'

    return status

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


def usermanual_delivery_whatsapp(sku, product_name, product_manual, name,phone_num, wati):
    status = 'Failure'
    if sku in usermanual_skus_without_video:
        wati_template = 'miniture_usermanual2_push'
    else:
        wati_template = 'miniture_usermanual2_push'

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

def delivery_reminder_whatsapp(name, phone_num, products, delivery_date, wati):
    status = False
    custom_params = [{'name': 'products', 'value': products,
                      'name': 'est_delivery_date', 'value': delivery_date}]
    wati_status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                        template_name='order_dispatched_with_awb2',
                                        custom_params=custom_params)
    if wati_status:
        status = 'Success'
    else:
        status = 'Failure'

    return status

def delivery_delay_whatsapp(name, phone_num, products, wati):
    status = False
    custom_params = [{'name': 'products', 'value': products}]
    wati_status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                        template_name='delivery_delay_message',
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


def marketing_campaign_wati(template, wati):
    customers = pd.read_csv(r'woocommerce_contacts_w_names2.csv')
    total_number_of_customers = customers.shape[0]

    status_of_each_message = []
    for idx, row in customers.iterrows():
        try:
            customer_name = row['Name']
            customer_phone_number = row['Phone'] #'919176270768' #
            wati_status = wati.send_template_message(contact_name=customer_name, contact_number=customer_phone_number,
                                                template_name=template)
            if wati_status:
                status = 1
            else:
                status = 0
        except:
            status = 0

        status_of_each_message.append(status)
        # if idx>1:
        #     break
    total_success_count = sum(status_of_each_message)

    return  str(total_success_count) + ' out of ' + str(total_number_of_customers) + ' succeeded'


def marketing_campaign_wati(template, wati, skus = None):
    customers = pd.read_csv(r'woocommerce_customers_w_orders4.csv')
    total_number_of_customers = customers.shape[0]
    number_of_applicable_customers = 0
    customers.fillna('', inplace = True)
    status_of_each_message = []
    valid = False
    for idx, row in customers.iterrows():
        try:
            customer_name = row['Name']
            customer_phone_number = row['Phone'] #9176270768 #
            order_skus = str(row['order skus'])

            if skus == None:
                valid = True
                number_of_applicable_customers += 1
            else:
                for sku in skus:
                    if sku in order_skus:
                        valid = True
                        number_of_applicable_customers += 1
                        break

            if valid == True:
                wati_status = wati.send_template_message(contact_name=customer_name, contact_number=customer_phone_number,
                                                    template_name=template)
                if wati_status:
                    status = 1
                else:
                    status = 0
            else:
                status = 0
        except:
            status = 0

        status_of_each_message.append(status)
        # if idx>1:
        #     break
    total_success_count = sum(status_of_each_message)

    return  str(total_success_count) + ' out of ' + str(number_of_applicable_customers) + ' succeeded'
