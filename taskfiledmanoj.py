from flask_restplus import reqparse, Api, Resource, fields

import json
from flask import Flask, request, Response

from datetime import datetime
import requests

app = Flask(__name__)
api = Api(app)

model_400 = api.model('ErrorResponse400', {'message': fields.String,
		                           'errors' :fields.Raw })

model_500 = api.model('ErrorResponse400', {'status': fields.Integer,
                                           'message':fields.String })


def check_positive(value):
    ivalue = float(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is not a positive value" % value)
    return ivalue

def expiration_date(value):
    today_date = datetime.today().strftime("%Y-%m-%d")
    today_date = datetime.strptime(today_date, '%Y-%m-%d')

    expire_date = datetime.strptime(value, '%Y-%m-%d')
    #print(type(today_date),type(expire_date))
    
    if today_date <= expire_date:
        return expire_date


credit_parser = reqparse.RequestParser()
credit_parser.add_argument('CreditCardNumber', help = 'Credit card number', type = str, location='args' , required=True)
credit_parser.add_argument('CardHolder', help = 'Card holder name', type = str, location='args' , required=True)
credit_parser.add_argument('ExpirationDate', help = 'Expiration Date', type = expiration_date, location='args' , required=True)
credit_parser.add_argument('SecurityCode', help = 'Security Code', type = str, location='args' , required=False)
credit_parser.add_argument('Amount', help = 'Amount', type = check_positive, location='args' , required=True)

@api.route('/ProcessPayment' )
@api.expect (credit_parser)
class Pay(Resource):
    @api.response(200, 'Successful')
    @api.response(400, 'Validation Error', model_400)
    @api.response(500, 'Internal Processing Error', model_500)
    def get(self):
        args = credit_parser.parse_args()

        cardnumber = request.args['CreditCardNumber']
        cardholder = request.args['CardHolder']
        expirationdate = request.args['ExpirationDate']

        if 'SecurityCode' not in request.args or len(request.args['SecurityCode'])==0:
            securitycode = "123"
        else:
            securitycode = request.args['SecurityCode']
        amount = request.args['Amount']
        
        return_status = None
        result = {}
        try:
            cheap_url="https://api.cheapgateway.com"
            expensive_url="https://api.expensivegatteway.com"
            premium_url="https://api.premiumgateway.com"

            querystring={'cardnumber':cardnumber, 'cardholder':cardholder, 
                    'expirationdate':expirationdate, 'securitycode':securitycode, 'amount':amount}
            #print(querystring)
            
            def urlcall():
                ret_status = requests.request("POST", url, params=querystring)
                return ret_status

            if amount<20:
                ret_status = urlcall(cheap_url)
                
            elif amount>20 and amount<=500:
                for x in range(0,2):
                    if expensive_url is not None:
                        ret_status = urlcall(expensive_url)
                    if expensive_url is None:
                        ret_status = urlcall(cheap_url)
                    if ret_status==200:
                        break

                    
            elif amount>500:
                ret_status = urlcall(premium_url)
                for x in range(0,3):
                    if ret_status!=200:
                        ret_status = urlcall(premium_url)
                    else:
                        break

            #ret_status=200
                                
            result['status'] = 1
            if ret_status==200:
                result['message'] = "Payment is Processed"
            elif ret_status==400:
                raise ValueError
            elif ret_status==500:
                raise Exception
            return_status = ret_status

        except ValueError as e:
            result = {}
            result['status'] = 0
            return_status = 400
            result['message'] = e.args[0]
        except Exception as e:
            result = {}
            return_status = 500
            result['status'] = 0
            result['message'] = 'Internal Error has occurred while processing the request'
        finally:
            resp = Response(json.dumps(result), status=return_status, mimetype="application/json")
        return resp

if __name__ =='__main__':
  port =  8001  
  app.run(host='0.0.0.0', port=port)
