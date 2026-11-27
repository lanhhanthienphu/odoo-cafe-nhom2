from math import isfinite

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import SQL


class PosSessionHandover(models.Model):
    _name = "pos.session.handover"
    _description = "POS Session Handover"
    _rec_name = "session_id"
    _order = "id desc"

    session_id = fields.Many2one(
        "pos.session", string="POS Session", required=True, ondelete="restrict", copy=False
    )
    company_id = fields.Many2one(
        related="session_id.company_id", store=True, precompute=True
    )
    currency_id = fields.Many2one(
        "res.currency", required=True, readonly=True, ondelete="restrict"
    )
    expected_amount = fields.Monetary(string="Expected Cash", required=True, readonly=True)
    counted_amount = fields.Monetary(string="Counted Cash", required=True)
    difference_amount = fields.Monetary(
        compute="_compute_difference_amount", store=True, precompute=True,
        help="Counted cash minus expected cash.",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("submitted", "Submitted"), ("confirmed", "Confirmed")],
        string="Status",
        default="draft",
        required=True,
        readonly=True,
        copy=False,
    )

    _sql_constraints = [
        ("unique_session", "UNIQUE(session_id)", "This POS session already has a handover."),
    ]

    @api.depends("counted_amount", "expected_amount", "currency_id.rounding")
    def _compute_difference_amount(self):
        for handover in self:
            currency = handover.currency_id
            difference = handover.counted_amount - handover.expected_amount
            handover.difference_amount = currency.round(difference) if currency else 0.0

    def _validate_counted_cash(self, value):
        message = self.env._("Counted cash must be a finite, non-negative amount.")
        try:
            amount = float(value or 0.0)
        except (TypeError, ValueError, OverflowError):
            raise ValidationError(message) from None
        if not isfinite(amount) or amount < 0:
            raise ValidationError(message)

    @api.model_create_multi
    def create(self, vals_list):
        self.check_access("create")
        defaults = self.default_get(["session_id", "counted_amount"])
        handovers = []
        for vals in vals_list:
            if vals.keys() - {"session_id", "counted_amount"}:
                raise AccessError(self.env._(
                    "Only the POS session and counted cash can be set when creating a handover."
                ))
            values = {**defaults, **vals}
            session_id = values.get("session_id")
            if not session_id:
                raise ValidationError(self.env._("Select a POS session."))
            session = self.env["pos.session"].browse(session_id)
            session.check_access("read")
            if session.state != "closed":
                raise ValidationError(self.env._("Close the POS session before creating a handover."))
            if not session.cash_journal_id:
                raise ValidationError(self.env._("The POS session must have a cash payment method."))

            counted_amount = values.get("counted_amount", 0.0)
            self._validate_counted_cash(counted_amount)
            handovers.append({
                "session_id": session.id,
                "currency_id": session.currency_id.id,
                "expected_amount": session.cash_register_balance_end,
                "counted_amount": counted_amount,
                "state": "draft",
            })
        return super().create(handovers)

    def write(self, vals):
        if vals.keys() - {"counted_amount"}:
            raise AccessError(self.env._(
                "Only counted cash can be edited. Use the workflow buttons to change status."
            ))
        if not vals:
            return super().write(vals)
        self._check_state_for_update("draft", self.env._("Only draft handovers can be edited."))
        self._validate_counted_cash(vals["counted_amount"])
        for handovers in self.grouped("currency_id").values():
            super(PosSessionHandover, handovers).write(vals)
        return True

    @api.ondelete(at_uninstall=False)
    def _unlink_only_draft(self):
        self._check_state_for_update(
            "draft", self.env._("Only draft handovers can be deleted."), operation="unlink"
        )

    def _check_state_for_update(self, state, message, operation="write"):
        self.check_access(operation)
        if not self:
            return
        self.flush_recordset(["state"])
        current_states = self.env.execute_query(SQL(
            "SELECT state FROM %s WHERE id IN %s ORDER BY id FOR UPDATE",
            SQL.identifier(self._table),
            tuple(self.ids),
        ))
        if any(current_state != state for (current_state,) in current_states):
            raise UserError(message)

    def action_submit(self):
        self._check_state_for_update("draft", self.env._("Only draft handovers can be submitted."))
        return super().write({"state": "submitted"})

    def action_confirm(self):
        if not self.env.user.has_group("point_of_sale.group_pos_manager"):
            raise AccessError(self.env._("Only a Point of Sale administrator can confirm a handover."))
        self._check_state_for_update("submitted", self.env._("Submit the handover before confirming it."))
        return super().write({"state": "confirmed"})
