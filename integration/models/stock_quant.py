# See LICENSE file for full copyright and licensing details.

from odoo import api, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def create(self, vals_list):
        quants = super(StockQuant, self).create(vals_list)
        quants.trigger_export()
        return quants

    def write(self, vals):
        result = super(StockQuant, self).write(vals)
        self.trigger_export()
        return result

    def trigger_export(self):
        templates = self._get_templates_to_export_inventory()

        for template in templates:
            integrations = self.env['sale.integration'].get_integrations(
                'export_inventory',
                template.company_id,
            )
            for integration in integrations:
                key = 'export_inventory_%s_%s' % (integration.id, template.id)
                integration.with_delay(identity_key=key).export_inventory(template)

    def _get_templates_to_export_inventory(self):
        return (
            self.product_id.product_tmpl_id
            + self.product_id.get_used_in_kits_recursively()
        )
