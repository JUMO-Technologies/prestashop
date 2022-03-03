==========================
 Quick configuration guide
==========================

|

1. Install the Odoo PrestaShop Connector on your Odoo server – How to install in `Odoo.sh <https://youtu.be/p4KE10FbYk0>`__

|

2. Then follow steps from this video to make an initial configuration of our Odoo PrestaShop connector (`video <https://youtu.be/0Tz3FTiyR50>`__)

|

3. As our connector is using queue_job from OCA, you need to make sure also to properly configure your Odoo instance. Specifically check that you have below in your odoo.conf file:

    3.1. Make sure that number of workers is 2 and higher (e.g. workers = 4)

    3.2. Make sure queue_job module is added to server wide modules (e.g. server_wide_modules = web,queue_job)

    3.3. Add the following lines specific to queue_job to identify amount of channels that will be used for it
        | [queue_job]
        | channels = root:1

|

Change Log
##########

|

* 1.3.4 (2021-10-27)
    - Synchronize tracking only after it is added to the stock picking. Some carrier connectors

* 1.3.3 (2021-10-21)
    - Fix issue with Combinations not exporting properly attribute values

* 1.3.2 (2021-10-19)
    - Fix issues with incorrect categories syncing

* 1.3.1 (2021-10-18)
    - Added synchronization of partner language and partner email (to delivery and shipping address)

* 1.3 (2021-10-02)
    - Automapping of the Countries, Country States, Languages, Payment Methods
    - Added Default Sales Team to Sales Order created via e-Commerce Integration
    - Added synchronization of VAT and Personal Identification Number field
    - In case purchase is done form the company, create Company and Contact inside Odoo

* 1.2.1 (2021-09-21)
    - Fixed regression issue with initial creation of the product with combination not working properly

* 1.2 (2021-09-20)
    - Added possibility to define field mappings and specify if field should be updatable or not
    - Avoid creation of duplicated products under some conditions

* 1.1 (2021-06-28)
    - Add field for Delivery Notes on Sales Order
    - Added configuration to define on Sales Integration which fields should be used on SO and Delivery Order for Delivery Notes
    - Allow to specify which product should be exported to which channel
    - Add separate field that allows to specify Product Name to be sent to e-Commerce site instead of standard name
    - Do not change Minimal Order Quantity on existing Combinations

* 1.0.4 (2021-06-01)
    - Fix variants import if no variants exists

* 1.0.3 (2021-05-28)
    - Replaced client request to new format (fixing payment and delivery methods retrieving)
    - Fixed warnings on Odoo.sh with empty description on new models

* 1.0.2 (2021-04-21)
    - Fixed errors during import external models
    - Fixed images export

* 1.0.1 (2021-04-13)
    - Added PS_TIMEZONE settings field to correctly handle case when PrestaShop is in different timezone
    - Added Check Connection support

* 1.0 (2021-03-23)
    - Odoo integration with PrestaShop

|
