{
    "name": "POS Session Handover",
    "version": "19.0.1.0.0",
    "category": "Sales/Point of Sale",
    "summary": "Review counted cash for closed POS sessions",
    "depends": ["point_of_sale"],
    "data": [
        "security/pos_session_handover_rules.xml",
        "security/ir.model.access.csv",
        "views/pos_handover_views.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
}
