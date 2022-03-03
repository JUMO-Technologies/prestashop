# See LICENSE file for full copyright and licensing details.

from odoo import models, api


class IntegrationSaleSubStatusExternal(models.Model):
    _name = 'integration.sale.order.sub.status.external'
    _inherit = 'integration.external.mixin'
    _description = 'Integration Sale Sub Status External'

    def unlink(self):
        # Delete all odoo statuses also
        if not self.env.context.get('skip_other_delete', False):
            sub_status_mapping_model = self.env['integration.sale.order.sub.status.mapping']
            for external_status in self:
                sub_statuses_mappings = sub_status_mapping_model.search([
                    ('external_id', '=', external_status.id)
                ])
                for mapping in sub_statuses_mappings:
                    mapping.odoo_id.with_context(skip_other_delete=True).unlink()
        return super(IntegrationSaleSubStatusExternal, self).unlink()

    @api.model
    def fix_unmapped(self, integration):
        # Payment methods should be pre-created automatically in Odoo
        sub_status_mapping_model = self.env['integration.sale.order.sub.status.mapping']
        unmapped_sub_statuses = sub_status_mapping_model.search([
            ('integration_id', '=', integration.id),
            ('odoo_id', '=', False),
        ])

        odoo_sub_status_model = self.env['sale.order.sub.status']

        for mapping in unmapped_sub_statuses:
            create_vals = {
                'code': mapping.external_id.external_reference,
                'integration_id': mapping.external_id.integration_id.id,
                'name': mapping.external_id.name,
            }
            odoo_sub_status = odoo_sub_status_model.create(create_vals)
            mapping.odoo_id = odoo_sub_status.id
