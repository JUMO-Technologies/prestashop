# See LICENSE file for full copyright and licensing details.

import logging
from odoo import fields, models, api
from ..exceptions import NotMapped

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = ['product.product', 'integration.model.mixin']

    product_variant_image_ids = fields.One2many(
        comodel_name='product.image',
        inverse_name='product_variant_id',
        string='Extra Variant Images',
    )

    @api.model
    def create(self, vals_list):
        # We need to avoid calling export separately
        # from product.template and product.product
        ctx = dict(self.env.context, from_product_product=True, from_product_create=True)
        from_product_template = ctx.pop('from_product_template', False)

        products = super(ProductProduct, self.with_context(ctx)).create(vals_list)

        if not from_product_template:
            products.mapped('product_tmpl_id').trigger_export(
                export_images=self._need_export_images(vals_list),
            )

        return products

    def write(self, vals):
        # We need to avoid calling export separately
        # from product.template and product.product
        ctx = dict(self.env.context, from_product_product=True)
        from_product_template = ctx.pop('from_product_template', False)

        result = super(ProductProduct, self.with_context(ctx)).write(vals)

        if not from_product_template:
            self.mapped('product_tmpl_id').trigger_export(
                export_images=self._need_export_images(vals),
            )

        return result

    @api.model
    def _need_export_images(self, vals_list):
        return self._check_fields_changed(
            [
                'image_1920',
                'product_variant_image_ids',
            ],
            vals_list
        )

    def to_export_format(self, integration):
        self.ensure_one()

        try:
            product_external_code = self.to_external(integration)
        except NotMapped:
            product_external_code = None

        # attributes
        attribute_values = []
        for attribute_value in self.product_template_attribute_value_ids:
            attribute_values.append(
                attribute_value
                .product_attribute_value_id
                .to_export_format_or_export(integration)
            )

        result = {
            'id': self.id,
            'external_id': product_external_code,
            'attribute_values': attribute_values,
        }

        search_domain = [
            ('odoo_model_id', '=', self.env.ref('product.model_product_product').id),
            ('integration_id', '=', integration.id),
        ]
        if product_external_code:
            search_domain += [('send_on_update', '=', True)]
        for field in self.env['product.ecommerce.field.mapping'].\
                search(search_domain).mapped('ecommerce_field_id'):
            result[field.technical_name] = integration.calculate_field_value(self, field)

        return result

    def get_used_in_kits_recursively(self):
        kits = self.env['mrp.bom'].search([
            ('bom_line_ids.product_id', 'in', self.ids),
            ('type', '=', 'phantom'),
        ])

        if not kits:
            return self.env['product.template'].browse()

        return (
            kits.product_tmpl_id
            + kits.product_tmpl_id.product_variant_ids.get_used_in_kits_recursively()
        )
