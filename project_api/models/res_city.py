from odoo import api, models, fields, _

class ResCity(models.Model):
    _name = 'res.city'
    _description = "res.city"
    
    name = fields.Char(required=True)
    state_id = fields.Many2one('res.country.state', required=True)