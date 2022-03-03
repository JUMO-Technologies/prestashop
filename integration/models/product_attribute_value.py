# See LICENSE file for full copyright and licensing details.

from odoo import models


class ProductAttributeValue(models.Model):
    _name = 'product.attribute.value'
    _inherit = ['product.attribute.value', 'integration.model.mixin']

    def to_export_format(self, integration):
        self.ensure_one()

        return {
            'external_id': self.try_to_external(integration),
            'attribute': self.attribute_id.to_external_or_export(integration),
            'name': integration.convert_translated_field_to_integration_format(
                self, 'name',
            ),
        }

    def export_with_integration(self, integration):
        self.ensure_one()
        return integration.export_attribute_value(self)
