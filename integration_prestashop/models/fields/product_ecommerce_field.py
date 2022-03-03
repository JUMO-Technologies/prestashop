# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class ProductEcommerceField(models.Model):
    _inherit = 'product.ecommerce.field'

    type_api = fields.Selection(
        selection_add=[('prestashop', 'PrestaShop')],
        ondelete={
            'prestashop': 'cascade',
        },
    )
