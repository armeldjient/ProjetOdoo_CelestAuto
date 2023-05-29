from odoo import fields, models


class AccountMove(models.Model):
	_inherit = "account.move"

	def _amount_in_word (self):
	    for rec in self:
	        rec.word_amount_total = str(rec.currency_id.amount_to_text(rec.amount_total))

	word_amount_total = fields.Char(
		string="Amount Total In Word",
		compute='_amount_in_word'
	)
