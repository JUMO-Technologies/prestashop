# See LICENSE file for full copyright and licensing details.

{
    'name': 'Product eCommerce Attributes',
    'category': 'Hidden',
    'version': '14.0.1.0.2',
    'author': 'VentorTech',
    'website': 'http://ventor.tech',
    'support': 'support@ventor.tech',
    'license': 'OPL-1',
    'price': 19.00,
    'currency': 'EUR',
    'depends': [
        'product',
        'sale',
    ],
    'data': [
        'views/product_product.xml',
        'views/product_template.xml',
        'views/product_image.xml',
        'views/product_public_category.xml',
        'security/ir.model.access.csv',
        'data/ir_ui_menu.xml',
    ],
    'installable': True,
}
