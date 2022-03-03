# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class IntegrationAccountTaxMapping(models.Model):
    _name = 'integration.account.tax.mapping'
    _inherit = 'integration.mapping.mixin'
    _description = 'Integration Account Tax Mapping'
    _mapping_fields = ('tax_id', 'external_tax_id')

    tax_id = fields.Many2one(
        comodel_name='account.tax',
        ondelete='cascade',
    )

    external_tax_id = fields.Many2one(
        comodel_name='integration.account.tax.external',
        required=True,
        ondelete='cascade',
    )

    # TODO: add constain
