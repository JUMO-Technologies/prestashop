# See LICENSE file for full copyright and licensing details.

import base64
import json
from odoo import fields, models, api

TYPE_INPUT_FILE_SELECTION = [
    ('input_order', 'Input Order'),
    ('input_cancel_order', 'Input Cancel Order'),
    ('acknowledgement', 'Acknowledgement'),
    ('info', 'Info'),
    ('unknown', 'Unknown'),
]

TYPE_OUTPUT_FILE_SELECTION = [
    ('inventory', 'Inventory'),
    ('acknowledgement', 'Acknowledgement'),
    ('functional_acknowledgement', 'Functional Acknowledgement'),
    ('confirm_shipment', 'Confirm Shipment'),
    ('invoice', 'Invoice'),
    ('unknown', 'Unknown'),
]


class SaleIntegrationFile(models.Model):
    _name = 'sale.integration.file'
    _description = 'Sale Integration File'

    name = fields.Char(
        string='Name',
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
            ('skipped', 'Skipped'),
            ('unknown', 'Unknown'),
        ],
        string='State',
        default='draft',
        readonly=True,
        copy=False,
    )
    si_id = fields.Many2one(
        'sale.integration',
        string='Service',
        required=True,
        ondelete='cascade',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    file = fields.Binary(
        string='File',
        required=True,
    )

    _order = 'create_date desc'

    _sql_constraints = [
        (
            'name_uniq', 'unique(si_id, name)',
            'Order name must be unique by partner!'
        )
    ]

    def action_cancel(self):
        orders = self.filtered(lambda s: s.state in ['draft', 'unknown'])
        return orders.write(
            {
                'state': 'cancelled',
            }
        )

    def action_draft(self):
        orders = self.filtered(lambda s: s.state == 'cancelled')
        return orders.write(
            {
                'state': 'draft',
            }
        )


class SaleIntegrationInputFile(models.Model):
    _name = 'sale.integration.input.file'
    _inherit = 'sale.integration.file'
    _description = 'Sale Integration Input File'

    @api.model
    def create(self, vals_list):
        input_files = super(SaleIntegrationInputFile, self).create(vals_list)

        for input_file in input_files:
            input_file.with_delay().process()

        return input_files

    def process(self):
        self.ensure_one()
        job = self.env['sale.integration'].trigger_create_order(self)

        integration = self.si_id
        order_data = integration.parse_order(self)
        factory = self.env['integration.sale.order.factory']
        not_mapped = factory.get_not_mapped(
            integration,
            order_data,
        )

        if not_mapped:
            created_mappings = []
            for not_mapped_value in not_mapped:
                model_name = not_mapped_value.model_name
                external_code = not_mapped_value.external_code
                mapping = self.env[model_name].create_mapping(
                    integration,
                    external_code,
                )
                mapping.failed_job_ids |= job
                created_mappings.append(mapping)

    def to_dict(self):
        self.ensure_one()
        json_str = base64.b64decode(self.file)
        result = json.loads(json_str)
        return result
