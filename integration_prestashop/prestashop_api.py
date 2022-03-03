# See LICENSE file for full copyright and licensing details.

import logging

import prestapyt
from odoo import _
from odoo.addons.integration.api.abstract_apiclient import AbsApiClient
from odoo.exceptions import UserError

from . import presta
from .presta.base_model import BaseModel

_logger = logging.getLogger(__name__)


# TODO: all reading through pagination
class PrestaShopApiClient(AbsApiClient):

    default_receive_orders_filter = (
        '{"filter[current_state]": "[<put state id here>]"'
        ', "filter[date_upd]": ">[%s]" % record.presta_last_receive_orders_datetime}'
    )

    settings_fields = (
        ('url', 'Shop URL', ''),
        ('key', 'Webservice Key', ''),
        ('language_id', 'Language ID', ''),
        (
            'receive_orders_filter',
            'Receive Orders Filter',
            default_receive_orders_filter,
            True,
        ),
        ('map_tax_group_default_tax', 'Tax Group to Default Tax Map', '{}'),
        ('default_stock_location_id', 'Default Stock Import Location', ''),
        ('id_group_shop', 'Shop Group where export products', ''),
        ('shop_ids', 'Shop ids in id_group_shop separated by comma', ''),
        (
            'PS_TIMEZONE',
            (
                'PrestaShop timezone value.'
                ' Will be automatically populated when integration is active'
            ),
            '',
        ),
    )

    def __init__(self, settings):
        super().__init__(settings)

        api_url = self.get_settings_value('url') + '/api'  # TODO: join urls
        api_key = self.get_settings_value('key')

        self._client = presta.Client(
            api_url,
            api_key,
        )

        self._language_id = self.get_settings_value('language_id')

        id_group_shop = self.get_settings_value('id_group_shop')

        shop_ids_str = self.get_settings_value('shop_ids')
        if shop_ids_str:
            shop_ids = shop_ids_str.split(',')
        else:
            shop_ids = []

        self._client.default_language_id = self._language_id
        self._client.id_group_shop = id_group_shop
        self._client.shop_ids = shop_ids

    def check_connection(self):
        resources = self._client.get('')
        connection_ok = bool(resources)
        return connection_ok

    def get_delivery_methods(self):
        delivery_methods = self._client.model('carrier').search_read(
            filters={'deleted': '0'},
            fields=['id', 'name'],
        )

        return delivery_methods

    def get_taxes(self):
        taxes = self._client.model('tax').search_read(
            filters={'deleted': '0'},
            fields=['id', 'name'],
        )

        return taxes

    def get_account_tax_groups(self):
        tax_groups = self._client.model('tax_rule_group').search_read(
            filters={'deleted': '0'},
            fields=['id', 'name'],
        )

        return tax_groups

    def get_countries(self):
        countries = self._client.model('country').search_read(
            filters={},
            fields=['id', 'name', 'iso_code'],
        )

        converted_countries = []
        for external_country in countries:
            converted_countries.append({
                'id': external_country.get('id'),
                'name': external_country.get('name'),
                'external_reference': external_country.get('iso_code'),
            })

        return converted_countries

    def get_states(self):
        countries = self._client.model('country').search_read(
            filters={},
            fields=['id', 'name', 'iso_code'],
        )
        converted_states = []
        for external_country in countries:
            states = self._client.model('state').search_read(
                filters={'id_country': external_country['id']},
                fields=['id', 'name', 'iso_code'],
            )

            for external_state in states:
                state_code = external_state.get('iso_code')
                if '-' in state_code:
                    # In prestashop some states are defined in a strange way like (NL-DE)
                    # We need to have only state code
                    state_code = state_code.split('-')[1]
                state_reference = '{}_{}'.format(
                    external_country.get('iso_code'),
                    state_code
                )

                converted_states.append({
                    'id': external_state.get('id'),
                    'name': external_state.get('name'),
                    'external_reference': state_reference,
                })

        return converted_states

    def _convert_to_settings_language(self, field):  # TODO: maybe delete?
        result = BaseModel._get_translation(field, self._language_id)
        return result

    def get_payment_methods(self):
        payments = set([])

        page = 0
        page_size = 1000
        while True:
            limit = '%d,%d' % (page * page_size, (page + 1) * page_size)
            _logger.debug('processing %s', limit)

            orders = self._client.model('order').search_read(
                filters={},
                fields=['id', 'payment'],
                limit=limit,
            )

            payments.update(x['payment'] for x in orders)

            page += 1

            if len(orders) < page_size:
                return [{'id': x} for x in payments]

    def get_languages(self):  # TODO: not optimal, better to use id_shop: all
        # TODO: if there is only one records presta returns it as simple {} rather than
        #  list of dicts [{}]
        shops = self._client.get('shops')['shops']['shop']
        if not isinstance(shops, list):
            shops = [shops]

        shop_ids = [
            x['attrs']['id'] for x in shops
        ]

        added_language_ids = []
        languages = []
        for shop_id in shop_ids:
            shop_languages = self._client.get(
                'languages',
                options={
                    'filter[active]': '1',
                    'display': '[id,name,language_code]',
                    'id_shop': shop_id,  # TODO: maybe use group
                }
            )['languages']['language']

            if not isinstance(shop_languages, list):
                shop_languages = [shop_languages]

            for shop_language in shop_languages:
                if shop_language['id'] not in added_language_ids:
                    language_code = shop_language.get('language_code', '').replace('-', '_')
                    languages.append({
                        'id': shop_language.get('id'),
                        'name': shop_language.get('name'),
                        # Converting language code to Odoo Format
                        'external_reference': language_code,
                    })
                    added_language_ids.append(shop_language['id'])

        return languages

    def get_attributes(self):
        product_options = self._client.get(
            'product_options', options={'display': '[id,name]'}
        )['product_options']

        if not product_options:
            return []

        attributes = product_options['product_option']
        if not isinstance(attributes, list):
            attributes = [attributes]

        for attribute in attributes:
            attribute['name'] = self._convert_to_settings_language(attribute['name'])

        return attributes

    def get_attribute_values(self):
        product_option_values = self._client.get(
            'product_option_values', options={'display': '[id,name]'}
        )['product_option_values']

        if not product_option_values:
            return []

        product_option_values = product_option_values['product_option_value']
        if not isinstance(product_option_values, list):
            product_option_values = [product_option_values]

        for attribute_value in product_option_values:
            attribute_value['name'] = self._convert_to_settings_language(
                attribute_value['name']
            )

        return product_option_values

    def get_categories(self):
        categories = self._client.model('category').search_read(
            filters={},
            fields=['id', 'name'],
        )

        return categories

    def get_sale_order_statuses(self):
        external_order_states = self._client.model('order_state').search_read(
            filters={},
            fields=['id', 'name', 'template'],
        )

        order_states = []

        for ext_order_state in external_order_states:
            order_states.append({
                'id': ext_order_state.get('id'),
                'name': ext_order_state.get('name'),
                # We cannot add any unique internal reference as in Prestashop it doesn't exist
                'external_reference': False,
            })

        return order_states

    def get_product_templates(self):
        product_templates = self._client.model('product').search_read(
            filters={'active': '1'},
            fields=['id', 'name'],
        )

        return product_templates

    def get_product_variants(self):
        product_variants = self._client.model('combination').search_read(
            filters={},
            fields=['id', 'id_product'],
        )

        for product_variant in product_variants:
            product_variant['id'] = '{product_id}-{combination_id}'.format(**{
                'product_id': product_variant['id_product'],
                'combination_id': product_variant['id'],
            })
            product_variant['name'] = 'Prestashop Combination'

        return product_variants

    def export_category(self, category):
        presta_category = self._client.model('category').create(category)
        return presta_category.id

    def export_template(self, template):
        mappings = []

        presta_product_id = template['external_id']
        product = self._client.model('product').get(presta_product_id)

        self._fill_product(product, template)

        # we save product type here, before save, because it
        # got overridden with incorrect type after save
        presta_product_type = product.type

        product.save()
        mappings.append({
            'model': 'product.template',
            'id': template['id'],
            'external_id': str(product.id),
        })

        if presta_product_type == 'pack':
            stock = self._client.model('stock_available').search({
                'id_product': product.id,
            })
            stock.out_of_stock = '1'
            stock.save()

        # remove redundant combinations
        actual_combination_ids = set([])
        for variant in template['products']:
            combination_id = self._export_product(product.id, variant)
            mappings.append({
                'model': 'product.product',
                'id': variant['id'],
                'external_id': '%s-%s' % (product.id, combination_id),
            })
            if combination_id != '0':
                actual_combination_ids.add(int(combination_id))

        for combination in product.get_combinations():
            if combination.id not in actual_combination_ids:
                combination.delete()

        return mappings

    def _fill_product(self, presta_product, vals):
        presta_product.type = 'simple'
        presta_product.state = '1'
        presta_product.is_virtual = '0'

        if 'name' in vals:
            self._fill_translated_field(
                presta_product, 'name', vals['name']
            )
        if 'description' in vals:
            self._fill_translated_field(
                presta_product, 'description', vals['description']
            )
        if 'description_short' in vals:
            self._fill_translated_field(
                presta_product, 'description_short', vals['description_short']
            )

        if 'meta_title' in vals:
            self._fill_translated_field(
                presta_product, 'meta_title', vals['meta_title']
            )
        if 'meta_description' in vals:
            self._fill_translated_field(
                presta_product, 'meta_description', vals['meta_description']
            )

        if 'price' in vals:
            presta_product.price = vals['price']
            presta_product.show_price = '1'

        if 'available_for_order' in vals:
            presta_product.available_for_order = '1' if vals['available_for_order'] else '0'
        if 'active' in vals:
            presta_product.active = '1' if vals['active'] else '0'

        if vals['type'] == 'service':
            presta_product.type = 'virtual'
            presta_product.is_virtual = '1'

        if vals['kits'] and len(vals['products']) <= 1:
            presta_product.type = 'pack'
            kit = vals['kits'][0]
            bundle_products = []
            for component in kit['components']:
                bundle_products.append({
                    'id': component['product_id'],
                    'quantity': component['qty'],
                })

            presta_product.product_bundle = bundle_products

        if 'id_category_default' in vals:
            # Setting to the root (Home) category if no category specified
            default_category = vals['id_category_default'] or '0'
            presta_product.id_category_default = default_category

        if 'categories' in vals:
            categories_list = vals['categories']
            if vals.get('id_category_default'):
                categories_list.append(vals['id_category_default'])
            category_ids = [
                x for x in set(categories_list) if x != '0'
            ]
            categories = self._client.model('category').get(category_ids)
            presta_product.categories = categories

        if 'id_tax_rules_group' in vals:
            if vals['id_tax_rules_group']:
                presta_product.id_tax_rules_group = vals['id_tax_rules_group'][0]['tax_group_id']
            else:
                presta_product.id_tax_rules_group = '0'

        # process bare/standard product
        if len(vals['products']) > 1:
            presta_product.weight = 0
        elif vals['products']:
            odoo_product = vals['products'][0]
            if 'weight' in odoo_product:
                presta_product.weight = odoo_product['weight']
            if 'reference' in odoo_product:
                presta_product.reference = odoo_product['reference'] or ''
            if 'ean13' in odoo_product:
                presta_product.ean13 = odoo_product['ean13'] or ''

    def _fill_translated_field(self, model, field, value):
        for lang_id, translation in value.items():
            setattr(model.lang(lang_id), field, translation or '')

    def _export_product(self, presta_product_id, product):
        if product['external_id']:
            product_id, combination_id = product['external_id'].split('-')
            if combination_id == '0':
                combination_id = None
        else:
            product_id, combination_id = presta_product_id, None  # TODO: refactor

        if combination_id:
            combination = self._client.model('combination').get(combination_id)
            self._fill_combination(combination, product, product_id)
            combination.save()
        else:
            combination = self._client.model('combination')
            prestashop_product = self._client.model('product').get(product_id)
            if product['attribute_values']:
                self._fill_combination(combination, product, product_id)
                combination = prestashop_product.add_combination(combination)
            else:
                combination.id = '0'  # todo: clarify
                pass  # update template with some values

        return combination.id

    def _fill_combination(self, combination, vals, product_id):
        combination.id_product = product_id

        if 'reference' in vals:
            combination.reference = vals['reference'] or ''

        if 'price' in vals:
            price = round(vals['price'], combination.PRESTASHOP_PRECISION)
            combination.price = price

        if 'weight' in vals:
            combination.weight = vals['weight']

        if 'ean13' in vals:
            combination.ean13 = vals['ean13'] or ''

        if not combination.minimal_quantity:
            combination.minimal_quantity = 1

        if vals['attribute_values']:
            attribute_value_ids = [x['external_id'] for x in vals['attribute_values']]
            product_option_values = self._client.model('product_option_value').get(
                attribute_value_ids,
            )
            combination.product_option_values = product_option_values

    def export_images(self, images):  # todo: naming
        product_id = images['template']['id']
        presta_product = self._client.model('product').get(product_id)

        presta_images = presta_product.get_images()
        for image in presta_images:
            image.delete()

        template_default_image = images['template']['default']
        if template_default_image:
            default_image = template_default_image['data']
            presta_product.add_image(default_image)

        for extra_image in images['template']['extra']:
            extra_image_data = extra_image['data']
            presta_product.add_image(extra_image_data)

        for product in images['products']:
            product_default_image = product['default']
            if product_default_image:
                product_image = product_default_image['data']
                presta_product.add_image(product_image)

            for product_extra_image in product['extra']:
                product_extra_image_data = product_extra_image['data']
                presta_product.add_image(product_extra_image_data)

    def export_attribute(self, attribute):
        product_option = self._client.model('product_option')

        self._fill_translated_field(
            product_option,
            'name',
            attribute['name'],
        )

        self._fill_translated_field(
            product_option,
            'public_name',
            attribute['name'],
        )

        product_option.group_type = 'select'
        product_option.save()

        return product_option.id

    def export_attribute_value(self, attribute_value):
        product_option_value = self._client.model('product_option_value')

        self._fill_translated_field(
            product_option_value,
            'name',
            attribute_value['name'],
        )

        product_option_value.id_attribute_group = attribute_value['attribute']
        product_option_value.save()

        return product_option_value.id

    def receive_orders(self):
        options = {
            'date': '1',
        }

        filters = self.get_settings_value('receive_orders_filter')
        evl = self._settings['fields']['receive_orders_filter']['eval']
        if evl and type(filters) is not dict:
            raise UserError(
                _('The receive_orders_filter of sale_integration must contain dict()')
            )

        if evl:
            options.update(
                filters
            )

        orders = self._client.get('orders', options=options)['orders']
        if orders:
            orders = orders['order']
        else:
            orders = []

        if not isinstance(orders, list):
            orders = [orders]

        input_files = []
        for order in orders:
            order_id = order['attrs']['id']
            data = self._get_input_file_data(order_id)
            input_file = {
                'id': order['attrs']['id'],
                'data': data,
            }
            input_files.append(input_file)

        return input_files

    def _get_messages_list(self, order_id):
        options = {
            'filter[id_order]': order_id,
        }
        messages = self._client.get('messages', options=options)['messages']
        if messages:
            messages = messages['message']
        else:
            messages = []

        if not isinstance(messages, list):
            messages = [messages]

        message_list = []
        for message in messages:
            message_id = message['attrs']['id']
            message_data = self._client.get(
                'messages', message_id
            )['message']
            message_list.append(message_data)

        return message_list

    def _get_input_file_data(self, order_id):
        order = self._client.get('orders', order_id)['order']

        customer = self._client.get(
            'customers', order['id_customer']
        )['customer']

        delivery_address = self._client.get(
            'addresses', order['id_address_delivery']
        )['address']

        invoice_address = self._client.get(
            'addresses', order['id_address_invoice']
        )['address']

        input_file_data = {
            'order': order,
            'customer': customer,
            'delivery_address': delivery_address,
            'invoice_address': invoice_address,
            'messages': self._get_messages_list(order_id),
        }
        return input_file_data

    def parse_order(self, input_file):
        order = input_file['order']
        customer = input_file['customer']
        delivery_address = input_file['delivery_address']
        invoice_address = input_file['invoice_address']
        messages = input_file['messages']

        delivery_notes = False

        if messages:
            delivery_notes_list = \
                [msg.get('message') for msg in messages if msg.get('private') == '0']
            delivery_notes = '\n'.join(delivery_notes_list)

        order_rows = order['associations']['order_rows']['order_row']
        if not isinstance(order_rows, list):
            order_rows = [order_rows]

        parsed_order = {
            'id': order['id'],
            'ref': order['reference'],
            'customer': {
                'id': customer['id'],
                'person_name': ' '.join([customer['firstname'], customer['lastname']]),
                'email': customer['email'],
                'language': customer['id_lang'],
            },
            'shipping': self._parse_address(customer, delivery_address),
            'billing': self._parse_address(customer, invoice_address),
            'lines': [self._parse_order_row(order['id'], x) for x in order_rows],
            'payment_method': order['payment'],
            'carrier': order['id_carrier'],
            'shipping_cost': float(order['total_shipping']),
            'delivery_notes': delivery_notes,
        }

        return parsed_order

    def _parse_address(self, customer, address):
        """
        we add customer id to address id to distinguish them from each other
        """

        return {
            'id': '%s-%s' % (customer['id'], address['id']),
            'person_name': ' '.join([address['firstname'], address['lastname']]),
            'email': customer['email'],
            'language': customer['id_lang'],
            'person_id_number': address['dni'],
            'company_name': address['company'],
            'company_reg_number': address['vat_number'],
            'street': address['address1'],
            'street2': address['address2'],
            'city': address['city'],
            'country': address['id_country'],
            'state': address['id_state'] if address['id_state'] != '0' else '',
            'zip': address['postcode'],
            'phone': address['phone'],
            'mobile': address['phone_mobile'],
        }

    def _parse_order_row(self, order_id, row):
        details_ids = self._client.search(
            'order_details', options={
                'filter[id_order]': '[%s]' % order_id,
                'filter[product_id]': '[%s]' % row['product_id'],
                'filter[product_attribute_id]': '[%s]' % row['product_attribute_id'],
            }
        )
        assert len(details_ids) == 1

        taxes = []
        details = self._client.get('order_details', details_ids[0])
        tax = details['order_detail']['associations']['taxes'].get('tax')
        if tax:
            taxes.append(tax['id'])

        return {
            'id': row['id'],
            'product_id': '%s-%s' % (row['product_id'], row['product_attribute_id']),
            'product_uom_qty': int(row['product_quantity']),
            'price_unit': float(row['unit_price_tax_excl']),
            'taxes': taxes,
        }

    def _get_state_code_or_empty(self, id_state):
        try:
            state = self._client.get('states', id_state)['state']
            return state['iso_code']
        except prestapyt.PrestaShopWebServiceError:
            return ''

    def export_inventory(self, inventory):
        for product_combination_id, inventory_item in inventory.items():
            product_id, combination_id = product_combination_id.split('-')

            # find stock for combination
            stock = self._client.model('stock_available').search({
                'id_product': product_id,
                'id_product_attribute': combination_id,
            })

            stock.quantity = int(inventory_item['qty'])
            stock.save()

    def export_tracking(self, tracking_data):
        order_id = tracking_data['sale_order_id']
        tracking = tracking_data['tracking']

        order_carrier = self._client.model('order_carrier').search({
            'id_order': order_id,
        })

        # TODO: check with integrational test

        order_carrier.tracking_number = tracking
        order_carrier.save()

    def export_sale_order_status(self, order_id, status):
        order = self._client.model('order').get(order_id)
        order.current_state = status
        order.save()
