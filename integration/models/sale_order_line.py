# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'integration.model.mixin']

    integration_external_id = fields.Char()

    def to_external(self, integration):
        self.ensure_one()
        assert self.order_id.integration_id == integration
        return self.integration_external_id
