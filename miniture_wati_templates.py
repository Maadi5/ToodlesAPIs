import os
import json
import pandas as pd
from config import miniture_marketing_team, ops_automation_alarm_contacts

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


def review_prompt(name, phone_num, product_name, sku, sku_review_url, cashback_amount, wati):
    review_csv = pd.read_csv(r'Product_review_links-2.csv')
    status = 'Failure'
    try:
        url_dynamic_component = sku_review_url.split('miniture.in/')[1]
        if cashback_amount != 0:
            custom_params = [{'name': 'review_url', 'value': url_dynamic_component},
                             {'name': 'product_name', 'value': product_name},
                             {'name': 'amount', 'value': cashback_amount}]
            wati_status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                                template_name='cashback_review_template4',
                                                custom_params=custom_params)
        else:
            custom_params = [{'name': 'review_url', 'value': url_dynamic_component},
                             {'name': 'product_name', 'value': product_name}]
            wati_status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                                template_name='miniture_capture_review',
                                                custom_params=custom_params)

        # wati_status = True
        if wati_status:
            status = 'Success'
        else:
            status = 'Failure'
    except:
        status = 'Failure'

    return status

def post_purchase(name, phone_num, sku, wati):
    status = 'Failure'
    # phone_num = '919176270768'
    try:
        if sku == 'YK-KW-006':

            wati_status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                                template_name='flexdeskfold_w_namespace',
                                                custom_params=None)
            if wati_status:
                status = 'Success'
            else:
                status = 'Failure'
        else:
            status = 'NA'
    except:
        status = 'Failure'

    return status

def usermanual_delivery_whatsapp(sku, product_name, product_manual, name,phone_num, wati):
    status = 'Failure'
    if sku in usermanual_skus_without_video:
        wati_template = 'miniture_product_received'
    else:
        wati_template = 'miniture_product_received'

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
    custom_params = [{'name': 'products', 'value': products},
                     {'name': 'est_delivery_date', 'value': delivery_date}]
    wati_status = wati.send_template_message(contact_name=name, contact_number=phone_num,
                                        template_name='delivery_reminder',
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

    for k,v in ops_automation_alarm_contacts.items():
        custom_params = [{'name': 'products', 'value': products}]
        ops_message_status = wati.send_template_message(contact_name=name, contact_number=v,
                                                 template_name='delivery_delay_message',
                                                 custom_params=custom_params)

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


ignore2 = ['919971997642','919835586429','919952845817','918787856737',
                                                 '919435019176','919884877777','919825018314','919160622316',
                                                 '918299565721','919900960315','917020803637','917007696573','919167191916',
                                                 '919884891983','918414881488','917721014349','917760107444','919663088339',
                                                 '919884323118','919673799555','919620120888','919744233302','919148384737',
                                                 '919686800333','919427805905','919811445268','919990162300','918438160249',
                                                 ]


def marketing_campaign_wati(template, wati, number_lists, skus = None):
    customers = pd.read_csv(r'shopify_woocommerce_noduplicates_orders.csv')
    total_number_of_customers = customers.shape[0]
    number_of_applicable_customers = 0
    customers.fillna('', inplace = True)
    status_of_each_message = []
    numbers_sent_to = set()
    avoid = False
    use = False
    avoid_list = []
    use_list = []
    if 'non-community' in skus:
        avoid = True
        avoid_list.extend(number_lists['community_members'])
        skus.pop(skus.index('non-community'))


    if skus == []:
        skus = None

    for idx, row in customers.iterrows():
        try:
            valid = False
            customer_name = row['Name']
            customer_phone_number = row['Phone'] ##'919176270768' #
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
                if avoid == True and customer_phone_number not in avoid_list:
                    wati_status = wati.send_template_message(contact_name=customer_name, contact_number=customer_phone_number,
                                                        template_name=template)
                    if wati_status:
                        status = 1
                        numbers_sent_to.add(customer_phone_number)
                    else:
                        status = 0
                else:
                    status = 0
            else:
                status = 0
        except:
            status = 0

        status_of_each_message.append(status)
        # if idx>1:
        #     break
    for customer_name, customer_phone_number in miniture_marketing_team.items():
        if customer_phone_number not in numbers_sent_to:
            wati_status = wati.send_template_message(contact_name=customer_name, contact_number=customer_phone_number,
                                                 template_name=template)
    total_success_count = sum(status_of_each_message)

    return  str(total_success_count) + ' out of ' + str(number_of_applicable_customers) + ' succeeded'
