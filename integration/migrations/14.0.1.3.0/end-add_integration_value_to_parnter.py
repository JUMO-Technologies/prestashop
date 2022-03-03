from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """
    Updates Integration fields for Delivery Note and Products
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    partner_mappings = env['integration.res.partner.mapping'].search([('partner_id', '!=', False)])

    for mapping in partner_mappings:
        mapping.partner_id.commercial_partner_id.integration_id = mapping.integration_id.id
