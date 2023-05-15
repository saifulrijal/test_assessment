from odoo import api, models, fields, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    uuid = fields.Char()
    
    @api.constrains('uuid')
    def _check_company_consistency(self):
        if not self.uuid or not self:
            return
        datas = self.search([('uuid', '=', self.uuid)])
        if len(datas) > 1:
            raise UserError(_("Uuid Already Use."))
