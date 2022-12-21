# Welcome to Hub testing !


The idea is to test multiple cases and monitor if the extensions are working well.

This extension will work together with other Fulfillment automation extension that will be in charge to accept all requests made by this extension (Real time validation, purchase request, suspend request, resume request and cancel request).

The first scenario is going to test that we could use the real time validation and that we could receive the following events:
* asset_purchase_request_processing
* asset_adjustment_request_processing
* asset_change_request_processing
* asset_suspend_request_processing
* asset_resume_request_processing
* asset_cancel_request_processing

In order to make this work we need to have:
* Two accounts (Vendor and Distributor) linked by contract.
* A Hub (Distributor)
* A forked Product (Vendor) with all capabilites and without parameters and listed to the Distributor and with the proper connections created (to the Hub).



## License

**Hub testing** is licensed under the *Apache Software License 2.0* license.
