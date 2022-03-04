# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductPublicCategory(models.Model):
    _name = 'product.public.category'
    _inherit = ['image.mixin']
    _description = 'Website Product Category'
    _parent_store = True
    _order = 'sequence, name'

    name = fields.Char(
        required=True,
        translate=True,
    )

    parent_id = fields.Many2one(
        comodel_name='product.public.category',
        string='Parent Category',
        index=True,
    )

    parent_path = fields.Char(
        index=True,
    )

    sequence = fields.Integer(
        index=True,
    )
