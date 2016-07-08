# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    published = fields.Boolean(string="Published")
