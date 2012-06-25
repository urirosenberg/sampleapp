#!/usr/bin/env python

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import db

"""Database models used for the AppDirect sample Python application

  User: Users will belong to a company and can use the application
  Company: Companies will have subscriptions to applications
  Event: Events represent state changes in subscriptions or user assignments
"""

class CompanySubscription(db.Model):
    edition = db.StringProperty()
    name = db.StringProperty()
    website = db.StringProperty()

class User(db.Model):
    email = db.StringProperty()
    first = db.StringProperty()
    last = db.StringProperty()
    openid = db.StringProperty()
    subscription = db.ReferenceProperty(CompanySubscription)
 
class Event(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    token = db.StringProperty()
    status = db.IntegerProperty()
    result = db.TextProperty()
