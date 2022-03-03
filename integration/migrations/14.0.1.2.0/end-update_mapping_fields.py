from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """
    Updates Integration fields for Delivery Note and Products
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    integrations = env['sale.integration'].search([])

    for integration in integrations:
        ecommerce_fields = env['product.ecommerce.field']\
            .search([('type_api', '=', integration.type_api)])
        for field in ecommerce_fields:
            create_vals = {
                'ecommerce_field_id' : field.id,
                'integration_id': integration.id,
                'send_on_update': field.default_for_update,
            }
            env['product.ecommerce.field.mapping'].create(create_vals)
