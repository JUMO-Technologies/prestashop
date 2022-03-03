from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """
    Updates Integration fields for Delivery Note and Products
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    integrations = env['sale.integration'].search([])

    payment_method_mapping_model = env['integration.sale.order.payment.method.mapping']

    for integration in integrations:
        payment_methods = env['integration.sale.order.payment.method.external']\
            .search([('integration_id', '=', integration.id)])
        for payment_method in payment_methods:
            if not payment_method.name:
                payment_method.name = payment_method.code
            existing_mapping = payment_method_mapping_model.\
                search([('external_payment_method_id', '=', payment_method.id)])
            # Step 1: If there is existing full mapping, than we should just fix Odoo object
            if existing_mapping and existing_mapping.payment_method_id:
                odoo_payment_method = existing_mapping.payment_method_id
                odoo_payment_method.integration_id = integration.id
                continue

            # Step 2: We should create new odoo sub status
            odoo_model = env['sale.order.payment.method']
            create_vals = {
                'code': payment_method.external_reference,
                'integration_id': payment_method.integration_id.id,
                'name': payment_method.name,
            }
            odoo_payment_method = odoo_model.create(create_vals)

            # Step 3. If there is mapping with not linked Odoo object - than we just link it
            if existing_mapping:
                existing_mapping.odoo_id = odoo_payment_method.id
                continue
            create_vals = {
                'payment_method_id': odoo_payment_method.id,
                'integration_id': odoo_payment_method.integration_id.id,
                'external_payment_method_id': odoo_payment_method.id,
            }
            payment_method_mapping_model.create(create_vals)
