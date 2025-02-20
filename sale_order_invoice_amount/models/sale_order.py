# Copyright (C) 2021 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    invoiced_amount = fields.Monetary(
        string="Invoiced Amount",
        compute="_compute_invoice_amount",
        store=True,
    )

    uninvoiced_amount = fields.Monetary(
        string="Uninvoiced Amount",
        compute="_compute_invoice_amount",
        store=True,
    )

    @api.depends(
        "state",
        "invoice_ids",
        "invoice_ids.amount_total_signed",
        "amount_total",
        "invoice_ids.state",
    )
    def _compute_invoice_amount(self):
        for rec in self:
            if rec.state != "cancel" and rec.invoice_ids:
                rec.invoiced_amount = 0.0
                for invoice in rec.invoice_ids:
                    if invoice.state != "cancel":
                        if (
                            invoice.currency_id != rec.currency_id
                            and rec.currency_id != invoice.company_currency_id
                        ):
                            rec.invoiced_amount += invoice.currency_id._convert(
                                invoice.amount_total_signed,
                                rec.currency_id,
                                invoice.company_id,
                                invoice.invoice_date or fields.Date.today(),
                            )
                        else:
                            rec.invoiced_amount += invoice.amount_total_signed
                # Uninvoiced amount could not be equal to total - invoiced amount.
                # For example if the amount invoiced does not match with the price unit.
                rec.uninvoiced_amount = max(
                    0,
                    sum(
                        [
                            (line.product_uom_qty - line.qty_invoiced)
                            * (line.price_total / line.product_uom_qty)
                            for line in rec.order_line.filtered(
                                lambda sl: sl.product_uom_qty > 0
                            )
                        ]
                    ),
                )
            else:
                rec.invoiced_amount = 0.0
                if rec.state in ["draft", "sent", "cancel"]:
                    rec.uninvoiced_amount = 0.0
                else:
                    rec.uninvoiced_amount = rec.amount_total
