# bwh_payments_core

Payment gateway connectors (Stripe, Razorpay, Telr, Tabby) and the payment engine for Frappe apps, as a plain Python package. A host app keeps the doctypes and whitelisted endpoints; this package holds the gateway code they call. It is not a Frappe app and is never installed on a site. Install it from a tag: `bwh-payments-core @ git+https://github.com/bwhtech/bwh_payments_core@v0.1.0`.
