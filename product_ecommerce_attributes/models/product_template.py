# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    public_categ_ids = fields.Many2many(
        comodel_name='product.public.category',
        relation='product_public_category_product_template_rel',
        string='Website Product Category',
    )

    product_template_image_ids = fields.One2many(
        comodel_name='product.image',
        inverse_name='product_tmpl_id',
        string='Extra Product Media',
        copy=True,
    )

    website_product_name = fields.Char(
        string='Product Name',
        translate=True,
        help='Sometimes it is required to define separate field with beautiful product name. '
             'And standard field to use for technical name in Odoo WMS (usable for Warehouses). '
             'If current field is not empty it will be used for sending to '
             'e-Commerce System instead of standard field.'
    )

    website_description = fields.Html(
        string='Website Description',
        sanitize=False,
        translate=True,
    )

    website_short_description = fields.Html(
        string='Short Description',
        sanitize=False,
        translate=True,
    )

    website_seo_metatitle = fields.Char(
        string='Meta title',
        translate=True,
    )

    website_seo_description = fields.Char(
        string='Meta description',
        translate=True,
    )
