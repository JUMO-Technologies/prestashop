# See LICENSE file for full copyright and licensing details.

{
    'name': 'PrestaShop Connector PRO',
    'summary': "Export products and your current stock from Odoo,"
               " and get orders from PrestaShop."
               " Update order status and provide tracking numbers to your customers; "
               "all this automatically and instantly!",
    'category': 'Sales',
    'version': '14.0.1.3.4',
    'images': ['static/description/images/image1.gif'],
    'author': 'VentorTech',
    'website': 'http://ventor.tech',
    'support': 'support@ventor.tech',
    'license': 'OPL-1',
    'live_test_url': 'https://odoo.ventor.tech/',
    'price': 224.00,
    'currency': 'EUR',
    'depends': [
        'integration',
    ],
    'data': [
        'data/product_ecommerce_fields.xml',
    ],
    'demo': [
    ],
    'external_dependencies': {
        'python': ['prestapyt'],
    },
    'installable': True,
    'application': True,
}
