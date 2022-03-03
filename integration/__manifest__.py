# See LICENSE file for full copyright and licensing details.

{
    'name': 'Integration',
    'version': '14.0.1.3.2',
    'category': 'Hidden',
    'author': 'VentorTech',
    'website': 'https://ventor.tech',
    'support': 'support@ventor.tech',
    'license': 'OPL-1',
    'price': 275.00,
    'currency': 'EUR',
    'images': ['static/description/icon.png'],
    'summary': 'Sale Integration with External Services',
    'depends': [
        'sale',
        'delivery',
        'mrp',
        'queue_job',
    ],
    'data': [
        # Security
        'security/integration_security.xml',
        'security/ir.model.access.csv',

        # data
        'data/queue_job_channel_data.xml',
        'data/queue_job_function_data.xml',

        # Views
        'views/assets.xml',
        'views/sale_integration.xml',
        'views/sale_integration_api_fields.xml',
        'views/sale_integration_input_file.xml',
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
        'views/sale_order_sub_status.xml',
        'views/sale_order_payment_method_views.xml',
        'views/product_public_category_views.xml',
        'views/product_image_views.xml',
        'views/product_product_views.xml',

        # external
        'views/external/integration_account_tax_group_external_views.xml',
        'views/external/integration_account_tax_external_views.xml',
        'views/external/integration_product_attribute_external_views.xml',
        'views/external/integration_product_attribute_value_external_views.xml',
        'views/external/integration_delivery_carrier_external_views.xml',
        'views/external/integration_product_template_external_views.xml',
        'views/external/integration_product_product_external_views.xml',
        'views/external/integration_res_country_external_views.xml',
        'views/external/integration_res_country_state_external_views.xml',
        'views/external/integration_res_lang_external_views.xml',
        'views/external/integration_sale_order_payment_method_external_views.xml',
        'views/external/integration_product_public_category_external_views.xml',
        'views/external/integration_res_partner_external_views.xml',
        'views/external/integration_sale_order_external_views.xml',
        'views/external/integration_sale_order_sub_status_external_views.xml',
        # mappings
        'views/mappings/integration_account_tax_group_mapping_views.xml',
        'views/mappings/integration_account_tax_mapping_views.xml',
        'views/mappings/integration_product_attribute_mapping_views.xml',
        'views/mappings/integration_product_attribute_value_mapping_views.xml',
        'views/mappings/integration_delivery_carrier_mapping_views.xml',
        'views/mappings/integration_product_template_mapping_views.xml',
        'views/mappings/integration_product_product_mapping_views.xml',
        'views/mappings/integration_res_country_mapping_views.xml',
        'views/mappings/integration_res_country_state_mapping_views.xml',
        'views/mappings/integration_res_lang_mapping_views.xml',
        'views/mappings/integration_sale_order_payment_method_mapping_views.xml',
        'views/mappings/integration_product_public_category_mapping_views.xml',
        'views/mappings/integration_res_partner_mapping_views.xml',
        'views/mappings/integration_sale_order_mapping_views.xml',
        'views/mappings/integration_sale_order_sub_status_mapping_views.xml',

        # Product fields
        'views/fields/product_ecommerce_field.xml',
        'views/fields/product_ecommerce_field_mapping.xml',

        # Menu items
        'views/sale_integration_menu.xml',
        'views/external/menu.xml',
        'views/mappings/menu.xml',
        'views/fields/menu.xml',
    ],
    'qweb': [
        'static/src/xml/status_menu_views.xml',
    ],
    'demo': [
    ],
    'external_dependencies': {
        'python': ['cerberus'],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
