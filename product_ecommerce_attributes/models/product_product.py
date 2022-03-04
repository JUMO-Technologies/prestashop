# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_variant_image_ids = fields.One2many(
        comodel_name='product.image',
        inverse_name='product_variant_id',
        string='Extra Variant Images',
    )
