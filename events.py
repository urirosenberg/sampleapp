#!/usr/bin/env python

import cgi
import logging
import oauth2
import urllib2
import urllib
import httplib
from google.appengine.api import urlfetch

from google.appengine.dist import use_library
use_library('django', '1.2')

from models import Event
from models import CompanySubscription
from models import User

from marshall import EventXml

from google.appengine.api.datastore_errors import BadArgumentError
from xml.dom import minidom

consumer_key = ###############
consumer_secret = ##################
service_api_URL= ################
logger_URL='URL'
eventUrlTemplate = "https://www.appdirect.com/rest/api/events/%s";

errorTemplate = """
<result>
   <success>false</success>
   <errorCode>%s</errorCode>
   <message>%s</message>
</result>
"""



successMessage = """<result><success>true</success></result>"""

def FetchEvent(token):
    consumer = oauth2.Consumer(consumer_key, consumer_secret)
    client = oauth2.Client(consumer)
    eventUrl = token
    resp, content = client.request(eventUrl)
    event = Event()
    event.token = token
    event.status = int(resp['status'])

    if event.status == 200:
        xmlDocument = minidom.parseString(content)
        eventXml = EventXml(xmlDocument)
        event.result = cgi.escape(xmlDocument.toprettyxml())
        event.put()
        return HandleEvent(eventXml)
    else:
        message = "HTTP response %d" % event.status
        logging.error(message)
        event.put()
        return errorTemplate % ( "UNKNOWN_ERROR", message)


def omssLogger(logKey,logMessage):
   logging.info("omss logger called")
   o_headers = {"Accept": "text/plain"}
   logMessage = logMessage.replace(" ", "_")
   url2 = logging_UR+logKey+"/"+logMessage
   logging.info(url2)
   response = urlfetch.fetch(url2,payload=None,method=urlfetch.GET,headers={},deadline=10,validate_certificate=None)
   logging.info(response.status_code)


def omssServiceproviders():
   logging.info("serviceproviders api called")
   form_fields = {"identifier":"sp5","name":"Service Provider five"}
   params =  urllib.urlencode(form_fields)
   o_headers = {"Content-type": "application/json","Accept": "application/json"}
   url2 =service_api_URL 
   response = urlfetch.fetch(url = url2,payload=params,method=urlfetch.POST,headers=o_headers)
   logging.info(response.status_code) 
   logging.info(response.content) 



def HandleEvent(eventXml):    
    logMessage = ("Recevied event type %s" % eventXml.eventType)  
    logging.info(logMessage)
    omssLogger("info",logMessage) 
    if eventXml.eventType == "SUBSCRIPTION_ORDER":
        return CreateOrder(eventXml)
    elif eventXml.eventType == "SUBSCRIPTION_CHANGE":
        return ChangeOrder(eventXml)
    elif eventXml.eventType == "SUBSCRIPTION_CANCEL":
        return CancelOrder(eventXml)
    elif eventXml.eventType == "USER_ASSIGNMENT":
        return AssignUser(eventXml)
    elif eventXml.eventType == "USER_UNASSIGNMENT":
        return UnassignUser(eventXml)
    else:
        message = "Event type %s is not configured" % eventXml.eventType
        return errorTemplate % ( "CONFIGURATION_ERROR", message)
    return successMessage

# Datatstore utility methods

def GetSubscription(accountIdentifier):
    subscription = None
    try:
        subscription = CompanySubscription.get_by_id(int(accountIdentifier))
        logging.info("Found subscription: %s", accountIdentifier)
    except ValueError:
        logging.error("Bad account identifier %s" % accountIdentifier)
    except BadArgumentError:
        logging.error("Bad account identifier %s" % accountIdentifier)
    return subscription

def GetUsers(subscription, openid = None):
    userQuery = User.all()
    userQuery.filter('subscription =', subscription)
    if (openid != None):
        userQuery.filter('openid = ', openid)
    return userQuery

# Event handling methods
def CreateOrder(eventXml):
    logging.info("Read %s %s %s" % (eventXml.payload.company.name,\
                                        eventXml.payload.company.website,\
                                        eventXml.payload.order.edition))
    companySubscription = eventXml.payload.CreateSubscription()
    omssServiceproviders()
    companySubscription.put()
    creator = eventXml.creator.CreateUserModel(companySubscription)
    creator.put()
    return_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+("<result><success>true</success><accountIdentifier>%s</accountIdentifier></result>" % companySubscription.key().id())  
    logging.info(return_xml) 
    return "<result><success>true</success><accountIdentifier>%s</accountIdentifier></result>" % companySubscription.key().id() 

def ChangeOrder(eventXml):
    accountId = eventXml.payload.account.accountIdentifier
    subscription = GetSubscription(accountId)

    if subscription == None:
        message = "Account %s not found" % accountIdentifier
        logging.error(message)
        return errorTemplate % ("ACCOUNT_NOT_FOUND", message)

    # Update the edition code
    subscription.edition = eventXml.payload.order.edition
    subscription.put()
    return successMessage

def CancelOrder(eventXml):
    accountId = eventXml.payload.account.accountIdentifier
    subscription = GetSubscription(accountId)

    if subscription == None:
        message = "Account %s not found" % accountId
        logging.error(message)
        return errorTemplate % ("ACCOUNT_NOT_FOUND", message)

    # Delete users associated with this subscription
    userQuery = GetUsers(subscription)
    for user in userQuery:
        logging.info("Removing user: %s " % user.email)
        user.delete()
    subscription.delete()
    return successMessage

def AssignUser(eventXml):
    accountId = eventXml.payload.account.accountIdentifier
    subscription = GetSubscription(accountId)
    if subscription == None:
        message = "Account %s not found" % accountIdentifier
        logging.error(message)
        return errorTemplate % ("ACCOUNT_NOT_FOUND", message)

    user = eventXml.payload.user.CreateUserModel(subscription)
    logging.info("Assigning user %s to account %s" % (user.email, accountId))
    user.put()
    return successMessage

def UnassignUser(eventXml):
    accountId = eventXml.payload.account.accountIdentifier
    subscription = GetSubscription(accountId)
    if subscription == None:
        message = "Account %s not found" % accountIdentifier
        logging.error(message)
        return errorTemplate % ("ACCOUNT_NOT_FOUND", message)

    openid = eventXml.payload.user.openid
    users = GetUsers(subscription, openid)
    if users.count() == 0:
        logging.error("User not found: %s" % openid)
        return errorTemplate % ("USER_NOT_FOUND", openid)
    user = users.get()
    logging.info("Unassigning user %s from account %s" %\
                     (user.email, accountId))
    user.delete()
    return successMessage
