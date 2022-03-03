# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    default_public_categ_id = fields.Many2one(
        comodel_name='product.public.category',
        string='Default Category',
    )
