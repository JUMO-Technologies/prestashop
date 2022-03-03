# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'integration.model.mixin']

    integration_id = fields.Many2one(
        string='e-Commerce Integration',
        comodel_name='sale.integration',
        readonly=True
    )

    integration_delivery_note = fields.Text(
        string='e-Commerce Delivery Note',
        copy=False,
    )

    sub_status_id = fields.Many2one(
        string='e-Commerce Order Status',
        comodel_name='sale.order.sub.status',
        domain='[("integration_id", "=", integration_id)]',
        ondelete='set null',
        copy=False,
    )

    payment_method_id = fields.Many2one(
        string='e-Commerce Payment method',
        comodel_name='sale.order.payment.method',
        domain='[("integration_id", "=", integration_id)]',
        ondelete='set null',
        copy=False,
    )

    def write(self, vals):
        statuses_before_write = {}

        if vals.get('sub_status_id'):
            for order in self:
                statuses_before_write[order] = order.sub_status_id

        result = super().write(vals)

        if vals.get('sub_status_id'):
            for order in self:
                if statuses_before_write[order] == order.sub_status_id:
                    continue

                integration = order.integration_id
                if not integration:
                    continue

                if not integration.job_enabled('export_sale_order_status'):
                    continue

                key = f'export_sale_order_status_{order.id}'
                integration.with_delay(
                    identity_key=key
                ).export_sale_order_status(order)

        return result
