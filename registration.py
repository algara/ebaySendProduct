# -*- coding: utf-8 -*-
from ebaysdk.trading import Connection as Trading
from openerp import models, fields, api,exceptions
from queries import get_values
from ebaysdk.exception import ConnectionError, ConnectionResponseError
from requests.exceptions import RequestException
from dateutil import parser
from openerp.exceptions import RedirectWarning


class ebaypasoapaso(models.Model):
    _name = 'registration.objeto'
    
    email= fields.Char(string='Email', required=True,help="eBay Email",translate=True)
    
    user_id=fields.Char(string="UserID",required=True,help="eBay UserID",translate=True)
    
    lists=[[],[],[],[],[]]
    
    lists=get_values()
    
    site=fields.Selection(lists[1],"Site",help="Choose your Site of Sale",translate=True,required=True) 
    
    appid= fields.Char(string='AppID', required=True,help=" 'AppID' of eBay")
    
    devid= fields.Char(string='DEVID',required=True,help="'DEVID' of eBay")
    
    
    certid= fields.Char(string='CertID', required=True,help="'CertID' of eBay")
    
    user_token=fields.Text(string='User Token',readonly=True,help="'User Token' of eBay",translate=True)
    compatibility=fields.Integer(string="Compatibility",default=837,help="Find number of compatibility in http://developer.ebay.com/devzone/guides/ebayfeatures(default=837)",translate=True)
    
    ru_name=fields.Char(string="RuName",required=True,help="RuName of ebay developer")
    
    sandbox=fields.Boolean(string="Sandbox",help="For test user",default=True)    
    
    
    _sql_constraints=[('name_uniq', 'unique(user_id,sandbox)', 'ERROR: There is already a User with this (UserID,Sandbox) ')]
    
    def save(self,cr,uid,ids, context=None):
        obj= self.browse(cr, uid,ids,context)
        self.write(cr, uid, ids, {
                                  "email":obj.email.strip(),
                                  'user_id': obj.user_id.strip(),
                                  'site': obj.site,
                                  'appid': obj.appid.strip(),
                                  'devid':obj.devid.strip(),
                                  'certid':obj.certid.strip(),
                                  #'user_token':obj.user_token.strip(),
                                  'compatibility':obj.compatibility,
                                  'ru_name':obj.ru_name.strip(),
                                  'sandbox':obj.sandbox
                                  }, context=context)
        
        return {
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'res_model': 'registration.objeto',
                }
    
class registration_sign(models.TransientModel):   
    
    _name="registration_sign.objeto"
    
    
    #From get token
    eBay_Token= fields.Char(string='eBayAuthToken',readonly=True)
    site_id=fields.Integer(string="SiteID",readonly=True)
    user_id=fields.Char(String="UserID",required=True)
    id_session=fields.Char(string='SessionID', readonly=True)
    hour_session=fields.Integer(string="Hour of Session",readonly=True)
    sign_url= fields.Char(string='SignInUrl', readonly=True)
    actual_state=fields.Selection([('confirm', 'confirm'),('inside', 'inside')],string="Actual State",default="confirm")
    
    _sql_constraints=[('name_unique', 'unique(user_id)', 'ERROR: There is already a User with this (UserID), eliminate your session and come back to create it ')]
    
    
    def session_id(self,cr, uid, ids, context=None):
        
        if context is None:
            context = {}
        
        user = self.pool.get('registration.objeto').search_read(cr,uid)#List of users read[]
        
        #If there is not user registered  
        if len(user)==0:
            action_id=self.pool['ir.model.data'].get_object_reference(cr,uid,'ebaypasoapaso','join_authorize')
            raise RedirectWarning("There is not anyone user register",action_id[1],"Go to create it")
            
        num_user=0
        api = Trading(domain='api.sandbox.ebay.com')
        for i in user:
            obj= self.browse(cr, uid,ids,context)
            num_user+=1
            
            if i["user_id"]==obj.user_id.strip():
                
                site=i["site"]
                appid=i["appid"]
                devid=i["devid"]
                certid=i["certid"]
                ru_name=i["ru_name"]
               
                if  appid and devid and certid:
                    api.config.set('siteid', site, force=True)
                    api.config.set('appid', appid, force=True)
                    api.config.set('devid', devid, force=True)
                    api.config.set('certid', certid, force=True)
                    
                    try:
                        response=api.execute('GetSessionID',{"RuName":ru_name})
                    except ConnectionError as e:
                        print(e)
                        print(e.response.dict())
                        raise RedirectWarning("Error to get session on eBay, Try it again.\nERROR:%s"%e.message)
                    except ConnectionResponseError as e:
                            raise RedirectWarning("Error response getting session token to eBay.\n %s"%e.message)
                    else:
                        #For invalidate the session
                        timestamp=parser.parse((response.dict().get("Timestamp")))
                        timestamp_int=int(timestamp.strftime('%s'))
                        
                        
                        sesion=response.dict().get("SessionID")
                        
                        url="https://signin.sandbox.ebay.com/ws/eBayISAPI.dll?SignIn&runame=%s&SessID=%s"%(ru_name,sesion)
                        
                        self.write(cr, uid, ids, {
                                                  "site_id":site,
                                                  "hour_session":timestamp_int,
                                                  "user_id":obj.user_id.strip(),
                                                  'id_session': sesion.strip(),
                                                  'sign_url': url.strip(),
                                                  'actual_state': 'inside'}, context=context)
                        break;
            elif num_user==len(user):
                print num_user
                print len(user)
                print "NO EXISTE NINGUNA CUENTA CON ESE USERID DEBE DARSE DE ALTA"
                
                action_id=self.pool['ir.model.data'].get_object_reference(cr,uid,'ebaypasoapaso','join_authorize')
                raise RedirectWarning("You have not got account user ",action_id[1],"Go to create it")
                
            
        
    def get_token(self,cr,uid,ids,context=None):
        if context is None:
            context = {}
        user = self.pool.get('registration.objeto').search_read(cr,uid)#List of users read[]
        obj= self.browse(cr, uid,ids,context)
        if obj.user_id and obj.id_session:
            api = Trading(domain='api.sandbox.ebay.com')
            for i in user:
                if i["user_id"]==obj.user_id:
                    site=i["site"]
                    appid=i["appid"]
                    devid=i["devid"]
                    certid=i["certid"]
                
                    if  site and appid and devid and certid:
                        api.config.set('siteid', site, force=True)
                        api.config.set('appid', appid, force=True)
                        api.config.set('devid', devid, force=True)
                        api.config.set('certid', certid, force=True) 
                        
                        
                        try:
                            response=api.execute("FetchToken",{"SessionID":obj.id_session})
                        except ConnectionError as e:
                            print(e)
                            raise RedirectWarning("Error  obtaning token on eBay, Try it again.\nERROR:%s"%e.message)
                        except ConnectionResponseError as e:
                            raise RedirectWarning("Error response obtaning token to eBay.\n %s"%e.message)
                        else:
                            dic_response=response.dict()
                            ebay_token=dic_response.get("eBayAuthToken")
                        
                        try:
                            response=api.execute('GetTokenStatus')
                        except ConnectionError as e:
                            print(e)
                            print(e.response.dict())
                            raise RedirectWarning("Error to get token status, Try it again.\nERROR:%s"%e.message)
                        except ConnectionResponseError as e:
                            raise RedirectWarning("Error response get token to eBay.\n %s"%e.message)
                        else:
                            status_token= response.dict().get("TokenStatus").get("Status")
                        
                            if status_token=="Active":
                                self.write(cr,uid,ids,{"eBay_Token":ebay_token})
                                this = self.browse(cr, uid, ids)[0]
                                
                                return {'type': 'ir.actions.act_window',
                                    'view_mode': 'tree,form',
                                    'view_type': 'form',
                                    'res_model': 'registration_sign.objeto',
                                    }
                            else:
                                
                                raise RedirectWarning("eBay`s token is incorrect, sign in eBay and create another one new")
                                
                                print "EL TOKEN DEL USUARIO NO ES VALIDO TIENE QUE CAMBIAR DE TOKEN, METASE EN EBAY CREE UNO NUEVO Y VUELVA A INTENTARLO"
            
        else:
            print "GETTOKEN: El Usuario a auntenticar no es el que ha metido no hay obj.user_id o obj.session"
        
    
    
    
    
    
