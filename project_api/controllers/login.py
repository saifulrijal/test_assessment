import json
import logging
import functools
import werkzeug.wrappers

from odoo import http
from odoo.addons.project_api.models.common import invalid_response, valid_response
from odoo.exceptions import AccessDenied, AccessError
from odoo.http import request
from datetime import datetime

_logger = logging.getLogger(__name__)


def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        access_token_data = request.env["api.access_token"].sudo().search([("token", "=", access_token)],
                                                                          order="id DESC", limit=1)

        if access_token_data.find_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap


class AccessToken(http.Controller):
    @http.route("/api/login", methods=["GET"], type="http", auth="none", csrf=False)
    def api_login(self, **post):
        """The token URL to be used for getting the access_token:

        Args:
            **post must contain login and password.
        Returns:

            returns https response code 404 if failed error message in the body in json format
            and status code 202 if successful with the access_token.
        """
        params = ["db", "login", "password"]
        params = {key: post.get(key) for key in params if post.get(key)}
        db, username, password = (
            params.get("db"),
            post.get("login"),
            post.get("password"),
        )
        _credentials_includes_in_body = all([db, username, password])
        if not _credentials_includes_in_body:
            # The request post body is empty the credetials maybe passed via the headers.
            headers = request.httprequest.headers
            db = headers.get("db")
            username = headers.get("login")
            password = headers.get("password")
            _credentials_includes_in_headers = all([db, username, password])
            if not _credentials_includes_in_headers:
                # Empty 'db' or 'username' or 'password:
                return invalid_response(
                    "missing error", "either of the following are missing [db, username,password]", 403,
                )
        # Login in odoo database:
        try:
            request.session.authenticate(db, username, password)
        except AccessError as aee:
            return invalid_response("Access error", "Error: %s" % aee.name)
        except AccessDenied as ade:
            return invalid_response("Access denied", "Login, password or db invalid")
        except Exception as e:
            # Invalid database:
            info = "The database name is not valid {}".format((e))
            error = "invalid_database"
            _logger.error(info)
            return invalid_response("wrong database name", error, 403)

        uid = request.session.uid
        # odoo login failed:
        if not uid:
            info = "authentication failed"
            error = "authentication failed"
            _logger.error(info)
            return invalid_response(401, error, info)

        # Generate tokens
        access_token = request.env["api.access_token"].find_or_create_token(user_id=uid, create=True)
        # Successful response:
        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "uid": uid,
                    "user_context": request.session.get_context() if uid else {},
                    "company_id": request.env.user.company_id.id if uid else None,
                    "company_ids": request.env.user.company_ids.ids if uid else None,
                    "partner_id": request.env.user.partner_id.id,
                    "access_token": access_token,
                    "company_name": request.env.user.company_name,
                    "country": request.env.user.country_id.name,
                    "contact_address": request.env.user.contact_address,
                }
            ),
        )


    @validate_token
    @http.route("/api/create/order", methods=["POST"], type="http", auth="none", csrf=False)
    def create_project(self, **post):
        data = request.httprequest.data.decode()
        try:
            data = eval(data)
            partner = data.get('partner_id')
            if not partner and not partner.get('uuid'):
                info = "Value partnerid still empty"
                error = "Invalid Partner"
                _logger.error(info)
                return invalid_response(error, info, 401)
            partner_id = self.check_or_create_partner(partner)
            lines = data.get('order_line')
            line_ids = self.prepare_orderlines(lines)
            if not isinstance(line_ids, list):
                return line_ids
        except Exception as e:
            # Invalid database:
            info = "Value is not valid {}".format((e))
            error = info
            _logger.error(info)
            return invalid_response("Internal Server Error", info, 403)
        value = {
            'partner_id': partner_id.id,
            'order_line': line_ids
        }
        order_id = request.env['sale.order'].create(value)
        order_id.action_confirm()
        self.prepare_create_invoice(order_id)
        result = werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "order_id": order_id.id,
                    "lines": [
                        {
                            'uuid': rec.product_id.uuid, 
                            'qty': rec.product_uom_qty, 
                            'price':rec.price_unit, 
                            'subtotal': rec.price_subtotal
                        } 
                        for rec in order_id.order_line],
                    "total": order_id.amount_total
                }
            ),
        )
        return result

    @validate_token
    @http.route("/api/read/order", methods=["POST"], type="http", auth="none", csrf=False)
    def read_order(self, **post):
        user_id = request.uid
    
    def check_or_create_partner(self, partner):
        partners = request.env['res.partner'].sudo()
        domain = [
            ('uuid', '=', partner.get('uuid'))
        ]
        partner_id = partners.search(domain)
        if not partner_id:
            partner_id = partners.create(partner)
        return partner_id
    
    def check_or_create_city(self, city, state_id):
        res_city = request.env['res.city'].sudo()
        domain = [
            ('name', 'ilike', city),
            ('state_id', '=', state_id)
        ]
        city_id = res_city.search(domain)
        if not res_city:
            value = {'name': city, 'state_id': state_id}
            city_id = res_city.create(value)
        return city_id
    
    def check_state(self, state):
        res_state = request.env['res.country.state'].sudo()
        domain = [
            ('name', 'ilike', state)
        ]
        state_id = res_state.search(domain)
        if not state_id:
            info = "Provinsi Not found"
            error = "Invalid area provinsi"
            _logger.error(info)
            return invalid_response(error, info, 401)
        return state_id.id
    
    def check_or_create_product(self, line):
        error = False
        product_id = line.get('product_id')
        if not product_id:
            info = "Value product still empty"
            error = "Invalid product"
            _logger.error(info)
            error = invalid_response(error, info, 401)
        state = product_id.get('area_provinsi')
        if not state:
            info = "Value partnerid still empty"
            error = "Invalid Partner"
            _logger.error(info)
            error = invalid_response(error, info, 401)
        else:
            state = self.check_state(state)
            if not isinstance(state, int):
                error = state
        city_id = False
        if product_id.get('area_kota'):
            city_id = self.check_or_create_city(product_id.get('area_kota'), state)
        produt_product = request.env['product.product'].sudo()
        domain = [
            ('uuid', '=', product_id.get('uuid'))
        ]
        error = produt_product.search(domain)
        if not error:
            value = {
                'name': product_id.get('komoditas'),
                'uuid':product_id.get('uuid'),
                'list_price':line.get('price'),
                'standard_price':line.get('price'),
                'lst_price':line.get('price'),
                'size':line.get('size'),
                'invoice_policy': 'order',            
            }
            error = produt_product.create(value).id
        else:
            error = error.id
        return error
    
    def prepare_orderlines(self, lines):
        error = False
        data = []
        for line in lines:
            product_id = self.check_or_create_product(line)
            if not isinstance(product_id, int):
                error = product_id
                break
            product_id = request.env['product.product'].browse(product_id)
            qty = line.get('qty')
            price_unit = line.get('price_unit')
            value = {'product_id': product_id.id, 'product_uom_qty': qty, 'price_unit': price_unit}
            data.append((0,0, value))
        if error:
            return error
        return data
    
    def prepare_create_invoice(self, order_id):
        create_invoices = request.env['sale.advance.payment.inv'].sudo()
        value = {
            'advance_payment_method': 'delivered'
        }
        request.env
        sale_advance_id = create_invoices.with_context({'active_ids': order_id.ids}).create(value)
        sale_advance_id.create_invoices()
        invoices = order_id.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
        invoices.action_post()
        invoices.action_register_payment()
        self.action_create_register_payment(invoices)
        
    def action_create_register_payment(self, move_id):
        context = {
            'active_model': 'account.move',
            'active_ids': move_id.ids,
        }
        acc_register = request.env['account.payment.register'].sudo()
        journal_id = request.env['account.journal'].search([
                    ('type', 'in', ('bank', 'cash')),
                    ('company_id', '=', move_id.company_id.id),
                ], limit=1)
        value = {
            'journal_id': journal_id.id,
            'payment_date': datetime.now().date(),
            'amount': move_id.amount_residual,
            'communication': move_id.display_name,
        }
        reg_pay = acc_register.with_context(context).create(value)
        reg_pay._compute_payment_method_id()
        reg_pay.action_create_payments()
