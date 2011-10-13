# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from standard library
from decimal import Decimal as decimal
from os.path import join, dirname
import re
from subprocess import check_output, CalledProcessError
import sys

# Import from itools
from itools.core import freeze, merge_dicts
from itools.datatypes import Boolean, String, Decimal, Enumerate, Email
from itools.datatypes.primitive import enumerate_get_value, enumerate_is_valid
from itools.gettext import MSG
from itools.log import log_debug
from itools.html import HTMLFile
from itools.web import BaseView, BaseForm

# Import from ikaaro
from ikaaro.autoform import ReadOnlyWidget

# Import from itws
from itws.datatypes import StringFixSize

# Import from payments
from payment import Payment
from payment_way import PaymentWay, register_payment_way
from utils import get_payment_way


class PBXState(Enumerate):
    options = [
        {'name': 1,
         'value': MSG(u'Payment done'), 'pbx': 'PBX_EFFECTUE'},
        {'name': 2,
         'value': MSG(u'Payment refused'), 'pbx': 'PBX_REFUSE'},
        {'name': 3,
         'value': MSG(u'Payment error'), 'pbx': 'PBX_ERREUR'},
        {'name': 4,
         'value': MSG(u'Payment cancelled'), 'pbx': 'PBX_ANNULE'}]



class PayboxCGIErrors(Enumerate):
    options = [
        {'name': '-1',
         'value': u'Error in reading the parameters via stdin'},
        {'name': '-2', 'value': u'Error in memory allocation'},
        {'name': '-3', 'value': u'Error in the parameters (Http Error)'},
        {'name': '-4',
         'value': u'One of the PBX_RETOUR variable is too long'},
        {'name': '-5', 'value': u'Error in opening the file'},
        {'name': '-6', 'value': u'Error in file format'},
        {'name': '-7', 'value': u'A mandatory variable is missing.'},
        {'name': '-8',
         'value': u'Numerical variables contains a non-numerical character'},
        {'name': '-9', 'value': u'PBX_SITE value is invalid.'},
        {'name': '-10', 'value': u'PBX_RANG value is invalid'},
        {'name': '-11', 'value': u'PBX_TOTAL value is invalid'},
        {'name': '-12', 'value': u'PBX_LANGUE or PBX_DEVISE is invalid'},
        {'name': '-13', 'value': u'PBX_CMD is empty or invalid'},
        {'name': '-14', 'value': u'Unknow error'},
        {'name': '-15', 'value': u'Unknow error'},
        {'name': '-16', 'value': u'PBX_PORTEUR is invalid'},
        {'name': '-17', 'value': u'Error of coherence'}]



class PayboxAccount(Enumerate):
    options = [
        {'name': 'paybox_system', 'value': u'PAYBOX SYSTEM'},
        {'name': 'paybox_direct', 'value': u'PAYBOX DIRECT'}]



class TypePayment(Enumerate):
    options = [
        {'name': 'carte', 'value': u'Carte'}]



class TypeCarte(Enumerate):
    options = [
        {'name': 'CB', 'value': u'CB'},
        {'name': 'VISA', 'value': u'VISA'},
        {'name': 'EUROCARD_MASTERCARD', 'value': u'EUROCARD_MASTERCARD'},
        {'name': 'E_CARD', 'value': u'E_CARD'},
        {'name': 'AMEX', 'value': u'AMEX'},
        {'name': 'DINERS', 'value': u'DINERS'},
        {'name': 'JCB', 'value': u'JCB'},
        {'name': 'COFINOGA', 'value': u'COFINOGA'},
        {'name': 'SOFINCO', 'value': u'SOFINCO'},
        {'name': 'AURORE', 'value': u'AURORE'},
        {'name': 'CDGP', 'value': u'CDGP'},
        {'name': '24h00', 'value': u'24H00'}]


class ModeAutorisation(Enumerate):
    options = [
        {'name': 'N', 'value': MSG(u'Mode autorisation + télécollecte.')},
        {'name': 'O', 'value': MSG(u'Mode autorisation uniquement.')}]


class PayboxStatus(Enumerate):
    options = [
        # Our states
        {'name': 'ip_not_authorized',
         'value': MSG(u"Paybox IP address invalid")},
        {'name': 'amount_invalid', 'value': MSG(u"Invalid payment amount")},
        # Paybox states
        {'name': '00000', 'value': MSG(u"Operation successful")},
        {'name': '00001',
         'value': MSG(u"The connection to the authorization centre failed")},
        {'name': '00003', 'value': MSG(u"Paybox error")},
        {'name': '00004',
         'value': MSG(u"Cardholder's number or visual cryptogram invalid")},
        {'name': '00006',
         'value': MSG(u"Access refused or site/rank/identifier incorrect")},
        {'name': '00008', 'value': MSG(u"Expiry date incorrect")},
        {'name': '00009',
         'value': MSG(u"Error during the creation of the subscription")},
        {'name': '00010', 'value': MSG(u"Currency unknown")},
        {'name': '00011', 'value': MSG(u"Amount incorrect")},
        {'name': '00015', 'value': MSG(u"Payment already made.")},
        {'name': '00016', 'value': MSG(u"Subscriber already exists")},
        {'name': '00021', 'value': MSG(u"Not authorized bin card")},
        {'name': '00029',
         'value': MSG(u"Not the same card used for the first payment")},
        {'name': '00030',
         'value': MSG(u"Time-out > 15 mn before validation by the buyer")},
        {'name': '00031', 'value': MSG(u"Reserved")},
        # Paybox error states: Payment refused by the authorization center
        {'name': '00100',
         'value': MSG(u"Transaction approved or successfully processed.")},
        {'name': '00102', 'value': MSG(u"Contact the card issuer")},
        {'name': '00103', 'value': MSG(u"Invalid retailer")},
        {'name': '00104', 'value': MSG(u"Keep the card")},
        {'name': '00105', 'value': MSG(u"Do not honour")},
        {'name': '00107',
         'value': MSG(u"Keep the card, special conditions.")},
        {'name': '00108',
         'value': MSG(u"Approve after holder identification")},
        {'name': '00112', 'value': MSG(u"Invalid transaction")},
        {'name': '00113', 'value': MSG(u"Invalid amount")},
        {'name': '00114', 'value': MSG(u"Invalid holder number")},
        {'name': '00115', 'value': MSG(u"Card issuer unknown")},
        {'name': '00117', 'value': MSG(u"Client cancellation")},
        {'name': '00119', 'value': MSG(u"Repeat the transaction later")},
        {'name': '00120',
         'value': MSG(u"Error in reply (error in ther server's domain)")},
        {'name': '00124', 'value': MSG(u"File update not withstood")},
        {'name': '00125',
         'value': MSG(u"Impossible to situate the record in the file")},
        {'name': '00126',
         'value': MSG(u"Record duplicated, former record replaced")},
        {'name': '00127',
         'value': MSG(u"Error in 'edit' in file up-date field")},
        {'name': '00128', 'value': MSG(u"Access to file denied")},
        {'name': '00129', 'value': MSG(u"File up-date impossible")},
        {'name': '00130', 'value': MSG(u"Error in format")},
        {'name': '00131',
         'value': MSG(u"Identifier of purchasing body unknown")},
        {'name': '00133', 'value': MSG(u"Expired card")},
        {'name': '00134', 'value': MSG(u"Suspicion of fraud")},
        {'name': '00138', 'value': MSG(u"Too many attemps at secret code")},
        {'name': '00141', 'value': MSG(u"Lost card")},
        {'name': '00143', 'value': MSG(u"Stolen card")},
        {'name': '00151',
         'value': MSG(u"Insufficient funds or over credit limit")},
        {'name': '00154', 'value': MSG(u"Expiry date of the card passed")},
        {'name': '00155', 'value': MSG(u"Error in secret code")},
        {'name': '00156', 'value': MSG(u"Card absent from file")},
        {'name': '00157',
         'value': MSG(u"Transaction not permitted for this holder")},
        {'name': '00158',
         'value': MSG(u"Transaction forbidden at this terminal")},
        {'name': '00159', 'value': MSG(u"Suspicion of fraud")},
        {'name': '00160',
         'value': MSG(u"Card accepter must contact purchaser")},
        {'name': '00161',
         'value': MSG(u"Amount of withdrawal past the limit")},
        {'name': '00163',
         'value': MSG(u"Security regulations not respected")},
        {'name': '00168',
         'value': MSG(u"Reply not forthcoming or received too late")},
        {'name': '00175', 'value': MSG(u"Too many attempts at secret card")},
        {'name': '00176',
         'value': MSG(u"Holder already on stop, former record kept")},
        {'name': '00190', 'value': MSG(u"Temporary halt of the system")},
        {'name': '00191', 'value': MSG(u"Card issuer not accessible")},
        {'name': '00194', 'value': MSG(u"Request duplicated")},
        {'name': '00196', 'value': MSG(u"System malfunctioning")},
        {'name': '00197',
         'value': MSG(u"Time of global surveillance has expired")},
        {'name': '00198',
         'value': MSG(u"Server inaccessible (set by the server)")},
        {'name': '00199',
         'value': MSG(u"Incident in the initiating domain")}]


    @classmethod
    def get_value(cls, name, default=None):
        if name is None:
            return MSG(u'Statut inconnu.')
        options = cls.get_options()
        value = enumerate_get_value(options, name, default)
        if value:
            return value
        if (value is None) and name.startswith('0001'):
            return MSG(u'Paiement Refusé (code %s)' % name)
        return MSG(u'Erreur inconnue (code %s)' % name)


    @classmethod
    def is_valid(cls, name):
        if name.startswith('001'):
            return True
        options = cls.get_options()
        return enumerate_is_valid(options, name)



###########
# Payment #
###########

class PayboxPayment_PaymentForm(BaseView):

    access = 'is_allowed_to_view'
    title = MSG(u'Pay')

    def GET(self, resource, context):
        """This view load the paybox cgi. That script redirect on paybox
        server to show the payment form.
        """
        # We get the paybox CGI path on server
        cgi_path = join(dirname(sys.executable), 'paybox.cgi')
        # Configuration
        kw = {}
        order = resource.parent
        kw['PBX_CMD'] = order.name
        kw['PBX_TOTAL'] = int(resource.get_property('amount') * 100)
        # Basic configuration
        kw['PBX_MODE'] = '4'
        kw['PBX_LANGUE'] = 'FRA'
        kw['PBX_TYPEPAIEMENT'] = 'CARTE'
        kw['PBX_WAIT'] = '0'
        kw['PBX_RUF1'] = 'POST'
        kw['PBX_RETOUR'] = "transaction:T;autorisation:A;amount:M;advanced_state:E;payment:P;carte:C;sign:K"
        # PBX Retour uri
        base_uri = context.uri.resolve(context.get_link(resource))
        for option in PBXState.get_options():
            key = option['pbx']
            status = option['name']
            uri = '%s/;end?status=%s' % (base_uri, status)
            kw[key] = '%s' % uri
        # PBX_REPONDRE_A (Url to call to set payment status)
        kw['PBX_REPONDRE_A'] = '%s/;callback' % base_uri
        # Configuration
        payment_way = get_payment_way(resource, 'paybox')
        for key in ['PBX_SITE', 'PBX_IDENTIFIANT',
                    'PBX_RANG', 'PBX_DIFF', 'PBX_AUTOSEULE']:
            kw[key] = payment_way.get_property(key)
        # Devise
        kw['PBX_DEVISE'] = resource.get_property('devise')
        # PBX_PORTEUR
        # XXX Allow to overide PBX_PORTEUR
        # (If someone call and give his card number ?)
        email = context.user.get_property('email')
        if Email.is_valid(email) is False:
            raise ValueError, 'PBX_PORTEUR should be a valid Email address'
        kw['PBX_PORTEUR'] = email
        # En mode test:
        if not payment_way.get_property('real_mode'):
            kw.update(payment_way.test_configuration)
        # Build cmd
        cmd = [cgi_path] + ['%s=%s' % (x[0], x[1]) for x in kw.iteritems()]
        log_debug("Calling Paybox: {0!r}".format(cmd))
        # Call the CGI
        try:
            result = check_output(cmd)
            # Check if all is ok
            html = re.match ('.*?<HEAD>(.*?)</HTML>', result, re.DOTALL)
            if html is None:
                raise CalledProcessError
        except CalledProcessError, e:
            # Try do get error number
            num_error = re.match ('.*?NUMERR=(.*?)"', e.output, re.DOTALL)
            if num_error:
                num_error = num_error.group(1)
                error = PayboxCGIErrors.get_value(num_error)
            else:
                error = "Unknow reason"
            error = u"Error: payment module can't be loaded. (%s)" % error
            raise ValueError, error
        # We return the payment widget
        html = html.group(1)
        ## Encapsulate in pay view
        #view = payments.pay_view(body=HTMLFile(string=html).events)
        #return view.GET(self, context)
        return HTMLFile(string=html).events



class PayboxPayment_Callback(BaseForm):
    """The paybox server send a POST request to say if the payment was done
    """
    access = True
    schema = freeze({
        'transaction': String,
        'autorisation': String,
        'amount': Decimal,
        'advanced_state': PayboxStatus})
    authorized_ip = freeze(['195.101.99.76', '194.2.122.158'])


    def POST(self, resource, context):
        # XXX TODO Check signature
        form = self._get_form(resource, context)
        # Set payment as paid
        if form['autorisation']:
            resource.update_payment_state(context, paid=True)
        else:
            resource.update_payment_state(context, paid=False)
        for key in ['transaction', 'autorisation', 'advanced_state']:
            resource.set_property(key, form[key])
        # We check amount
        amount = form['amount'] / decimal('100')
        if resource.get_property('amount') != amount:
            raise ValueError, 'invalid payment amount'
        # We ensure that remote ip address belongs to Paybox
        authorized_ip = self.authorized_ip
        payment_way = get_payment_way(resource, 'paybox')
        if not payment_way.get_property('real_mode'):
            authorized_ip = authorized_ip + [None]
        if context.get_remote_ip() not in authorized_ip:
            resource.set_property('advanced_state', 'ip_not_authorized')
        # Return a blank page to payment
        context.set_content_type('text/plain')


class PayboxPayment(Payment):
    class_id = 'paybox-payment'
    class_title = MSG(u'Paybox Payment')

    payment_way_class_id = 'paybox'

    payment_schema = freeze(merge_dicts(
        Payment.payment_schema,
        transaction=String(source='metadata', title=MSG(u'Id transaction'),
                           widget=ReadOnlyWidget),
        autorisation=String(source='metadata',
            title=MSG(u'Id Autorisation'), widget=ReadOnlyWidget),
        advanced_state=PayboxStatus(source='metadata', widget=ReadOnlyWidget,
            title=MSG(u'Advanced State'))))

    payment_fields = ['transaction', 'autorisation', 'advanced_state']

    class_schema = freeze(merge_dicts(
        Payment.class_schema,
        payment_schema))

    # Views
    payment_form = PayboxPayment_PaymentForm()

    callback = PayboxPayment_Callback()



###############
# Payment Way #
###############

class Paybox(PaymentWay):

    class_id = 'paybox'
    class_title = MSG(u'Paybox')
    class_description = MSG(u'Secured payment paybox')
    class_logo = '/ui/shop/images/secu_en_fondclair.png'

    payment_class = PayboxPayment

    # Views
    class_views = ['configure']

    # Schema
    base_schema = freeze({
        'PBX_SITE': StringFixSize(source='metadata', size=7,
                                  title=MSG(u'Paybox Site')),
        'PBX_RANG': StringFixSize(source='metadata', size=2,
                                  title=MSG(u'Paybox Rang')),
        'PBX_IDENTIFIANT': String(source='metadata',
                                  title=MSG(u'Paybox Identifiant')),
        'PBX_DIFF': StringFixSize(source='metadata', size=2,
                        title=MSG(u'Diff days (On two digits ex: 04)')),
        # XXX StringFixSize?
        'PBX_AUTOSEULE': String(source='metadata'),
        'real_mode': Boolean(source='metadata', default=False,
                             title=MSG(u'Payments in real mode'))})

    class_schema = freeze(merge_dicts(
        PaymentWay.class_schema,
        # Paybox account configuration
        base_schema))

    test_configuration = freeze({
        'PBX_SITE': 1999888,
        'PBX_RANG': 99,
        'PBX_PAYBOX': 'https://preprod-tpeweb.paybox.com/cgi/MYchoix_pagepaiement.cgi',
        'PBX_IDENTIFIANT': 2})

    payment_way_edit_fields = ['PBX_SITE', 'PBX_RANG', 'PBX_IDENTIFIANT',
                               'PBX_DIFF', 'real_mode']



register_payment_way(Paybox)
