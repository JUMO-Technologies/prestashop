# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class IntegrationProductTemplateMapping(models.Model):
    _name = 'integration.product.template.mapping'
    _inherit = 'integration.mapping.mixin'
    _description = 'Integration Product Template Mapping'
    _mapping_fields = ('template_id', 'external_template_id')

    template_id = fields.Many2one(
        comodel_name='product.template',
        ondelete='cascade',
    )

    external_template_id = fields.Many2one(
        comodel_name='integration.product.template.external',
        required=True,
        ondelete='cascade',
    )

    _sql_constraints = [
        ('uniq', 'unique(integration_id, template_id, external_template_id)', '')
    ]
