# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    tracking_exported = fields.Boolean(
        string='Is Tracking Exported?',
        default=False,
        help='This flag allows us to define if tracking code for this picking was exported '
             'for external integration. It helps to avoid sending same tracking number twice. '
             'Basically we need this flag, cause different carriers have different type of '
             'integration. And sometimes tracking reference is added to stock picking after it '
             'is validated and not at the same moment.',
    )

    def to_export_format(self, integration):
        self.ensure_one()

        lines = []
        for move_line in self.move_lines:
            sale_line = move_line.sale_line_id
            line = {
                'id': sale_line.to_external(integration),
                'qty': move_line.quantity_done,
            }
            lines.append(line)

        result = {
            'sale_order_id': self.sale_id.to_external(integration),
            'carrier': self.carrier_id.to_external(integration),
            'tracking': self.carrier_tracking_ref,
            'lines': lines,
        }

        return result

    def write(self, vals):
        res = super(StockPicking, self).write(vals)

        if res:
            done_pickings_with_tracking = (
                self
                .filtered(lambda x: x.state == 'done' and not x.tracking_exported)
                .filtered('carrier_tracking_ref')
            )

            for picking in done_pickings_with_tracking:
                integration = picking.sale_id.integration_id
                if not integration:
                    continue

                if not integration.job_enabled('export_tracking'):
                    continue

                key = f'export_tracking_{picking.id}'
                integration.with_delay(identity_key=key).export_tracking(picking)

        return res
