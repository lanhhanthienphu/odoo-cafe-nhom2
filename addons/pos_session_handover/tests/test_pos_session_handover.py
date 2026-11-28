from psycopg2.errors import UniqueViolation

from odoo.addons.point_of_sale.tests.common import TestPointOfSaleCommon
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form
from odoo.tests.common import new_test_user


class TestPosSessionHandover(TestPointOfSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cashier = new_test_user(
            cls.env, login="handover_cashier",
            groups="base.group_user,point_of_sale.group_pos_user",
            company_id=cls.pos_config.company_id.id,
        )
        cls.manager = new_test_user(
            cls.env, login="handover_manager",
            groups="base.group_user,point_of_sale.group_pos_manager",
            company_id=cls.pos_config.company_id.id,
        )
        cls.session = cls.env["pos.session"].create({
            "config_id": cls.pos_config.id,
            "cash_register_balance_start": 500.0,
            "state": "closed",
        })
        cls.handovers = cls.env["pos.session.handover"].with_user(cls.cashier)

    def _create_handover(self, counted_amount=480.0):
        return self.handovers.create({
            "session_id": self.session.id,
            "counted_amount": counted_amount,
        })

    def test_create_from_cashier_form(self):
        form_view = "pos_session_handover.view_pos_session_handover_form"
        form = Form(self.handovers, view=form_view)
        form.session_id = self.session.with_user(self.cashier)
        form.counted_amount = 480.0
        handover = form.save()
        self.assertEqual(handover.expected_amount, 500.0)
        self.assertEqual(handover.difference_amount, -20.0)
        with Form(handover, view=form_view) as edit_form:
            edit_form.counted_amount = 510.0
        self.assertEqual(handover.difference_amount, 10.0)

    def test_cash_difference_and_workflow(self):
        handover = self._create_handover()
        self.assertEqual(handover.expected_amount, 500.0)
        self.assertEqual(handover.difference_amount, -20.0)
        handover.counted_amount = 520.0
        self.assertEqual(handover.difference_amount, 20.0)
        handover.counted_amount = 500.0
        self.assertEqual(handover.difference_amount, 0.0)

        manager_handover = handover.with_user(self.manager)
        with self.assertRaises(UserError):
            manager_handover.action_confirm()
        handover.action_submit()
        self.assertEqual(handover.state, "submitted")
        with self.assertRaises(UserError):
            handover.write({"counted_amount": 490.0})
        with self.assertRaises(AccessError):
            handover.action_confirm()
        manager_handover.action_confirm()
        self.assertEqual(handover.state, "confirmed")
        with self.assertRaises(UserError):
            manager_handover.write({"counted_amount": 450.0})
        with self.assertRaises(UserError):
            manager_handover.unlink()

    def test_cannot_set_server_fields_directly(self):
        with self.assertRaises(AccessError):
            self.handovers.create({
                "session_id": self.session.id, "counted_amount": 480.0, "state": "confirmed",
            })
        handover = self.handovers.with_context(
            default_state="confirmed", default_difference_amount=123.0, default_expected_amount=123.0
        ).create({"session_id": self.session.id, "counted_amount": 480.0})
        self.assertEqual(handover.state, "draft")
        self.assertEqual(handover.expected_amount, 500.0)
        self.assertEqual(handover.difference_amount, -20.0)
        with self.assertRaises(AccessError):
            handover.write({"state": "confirmed"})

    def test_duplicate_session_rejected(self):
        self._create_handover()
        with self.assertRaises(UniqueViolation), self.env.cr.savepoint():
            self._create_handover()

    def test_invalid_cash_rejected(self):
        with self.assertRaises(ValidationError):
            self._create_handover(counted_amount=-1.0)
        handover = self._create_handover()
        with self.assertRaises(ValidationError):
            handover.write({"counted_amount": float("inf")})

    def test_open_session_rejected(self):
        self.session.state = "opened"
        with self.assertRaises(ValidationError):
            self._create_handover()
