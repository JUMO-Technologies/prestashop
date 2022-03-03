from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """
    Updates Integration fields for Delivery Note and Products
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    integrations = env['sale.integration'].search([])

    integrations.with_context(write_settings_fields=True).write({
        'so_delivery_note_field':
            env.ref('integration.field_sale_order__integration_delivery_note').id,
        'picking_delivery_note_field':
            env.ref('stock.field_stock_picking__note').id,
    })

    product_templates = env['product.template'].search([])

    product_templates.with_context(skip_product_export=True).write({
        'integration_ids': [(6, 0, integrations.ids)],
    })
