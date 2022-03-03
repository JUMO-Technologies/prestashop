Integration
===========

Changelog
---------

1.3.2 (2021-10-27)
***********************

* Synchronize tracking only after it is added to the stock picking. Some carrier connectors

1.3.1 (2021-10-18)
***********************

* Added synchronization of partner language and partner email (to delivery and shipping address)

1.3 (2021-10-02)
***********************

* Automapping of the Countries, Country States, Languages, Payment Methods
* Added Default Sales Team to Sales Order created via e-Commerce Integration
* Added synchronization of VAT and Personal Identification Number field
* In case purchase is done form the company, create Company and Contact inside Odoo

1.2 (2021-09-20)
***********************

* Added possibility to define field mappings and specify if field should be updatable or not
* Avoid creation of duplicated products under some conditions

1.1 (2021-06-28)
***********************

* Add field for Delivery Notes on Sales Order
* Added configuration to define on Sales Integration which fields should be used on SO and Delivery Order for Delivery Notes
* Allow to specify which product should be exported to which channel
* If e-Commerce Product Name is not empty, send it instead of standard Product Name

1.0.5 (2021-06-25)
***********************

* Fixed a bug of creating duplicate sale orders

1.0.4 (2021-06-01)
***********************

* FIX: Prestashop should send name of the product, not display_name

1.0.3 (2021-05-28)
***********************

* Fixed warnings on Odoo.sh with empty description on new models

1.0.2 (2021-04-21)
***********************

* Added statistics widget
* Create missing mappings on receiving of orders
* Requeue needed jobs when mappings are fixed

1.0.1 (2021-04-13)
***********************

* Added Check Connection
