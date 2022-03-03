# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductPublicCategory(models.Model):
    _name = 'product.public.category'
    _inherit = ['image.mixin', 'integration.model.mixin']
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

    def export_with_integration(self, integration):
        self.ensure_one()
        return integration.export_category(self)

    def to_export_format(self, integration):
        self.ensure_one()

        if self.parent_id:
            parent_id = self.parent_id.to_external_or_export(integration)
        else:
            parent_id = None

        return {
            'name': integration.convert_translated_field_to_integration_format(
                self, 'name'
            ),
            'parent_id': parent_id,
        }
