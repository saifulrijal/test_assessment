from odoo import api, models, fields, _

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    uuid = fields.Char()
    size = fields.Float()
