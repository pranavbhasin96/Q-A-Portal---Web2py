# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

## app configuration made easy. Look inside private/appconfig.ini
from gluon.contrib.appconfig import AppConfig
## once in production, remove reload=True to gain full speed
myconf = AppConfig(reload=True)


if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL(myconf.take('db.uri'), pool_size=myconf.take('db.pool_size', cast=int), check_reserved=['all'])
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore+ndb')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## choose a style for forms
response.formstyle = myconf.take('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.take('forms.separator')


## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'
#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Service, PluginManager, prettydate

auth = Auth(db)
service = Service()
plugins = PluginManager()

db.define_table(
	auth.settings.table_user_name,
	Field('first_name', length=128,default=''),
	Field('last_name',length=128,default=''),
	Field('username',length=128, unique=True),
	Field('email',length=128,default='',unique=True),
	Field('password','password',length=512,readable=False,label='Password'),
	Field('phone'),
	Field('about_yourself','text',default=''),
	Field('batch','string',default='',
		requires=IS_NOT_EMPTY()),
	Field('profile_picture','upload',default='./default.jpg'),
	Field('subscribed','list:string',default=[]),
	Field('category','string',default="Newbie"
		,readable=False, writable=False),
	Field('starred','list:string',default=[]),
	Field('totalupvotes','integer',
		writable=False, readable=False, default=0),
	Field('registration_key', length=512,                # required
		writable=False, readable=False, default=''),
	Field('reset_password_key', length=512,              # required
		writable=False, readable=False, default=''),
	Field('registration_id', length=512,                 # required
		writable=False, readable=False, default=''),
	)

custom_auth_table = db[auth.settings.table_user_name] # get the custom_auth_table
custom_auth_table.first_name.requires =   IS_NOT_EMPTY(error_message=auth.messages.is_empty)
custom_auth_table.last_name.requires =   IS_NOT_EMPTY(error_message=auth.messages.is_empty)
custom_auth_table.username.requires = IS_NOT_EMPTY(error_message=auth.messages.is_empty)
custom_auth_table.password.requires = [IS_STRONG(min=8, special=1, upper=1), CRYPT()]
custom_auth_table.subscribed.writable=custom_auth_table.subscribed.readable=False
custom_auth_table.starred.writable=custom_auth_table.starred.readable=False
##custom_auth_table.profile_picture.requires=[IS_IMAGE(extensions=('jpeg', 'png', 'gif'))]
custom_auth_table.email.requires = [
IS_EMAIL(error_message=auth.messages.invalid_email),
IS_NOT_IN_DB(db, custom_auth_table.email)]
auth.define_tables(username=True, signature=False)
auth.settings.table_user=custom_auth_table

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.take('smtp.server')
mail.settings.sender = myconf.take('smtp.sender')
mail.settings.login = myconf.take('smtp.login')

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)i
db.define_table('tags',
		Field('tag_name','string',length=128,unique=True)
		)


db.define_table('questions',
		Field('author_name',
			writable=False, readable=False),
		Field('anonymous','boolean',default=False),
		Field('judged','boolean',default=False,readable=False,writable=False),
		Field('sensible','boolean',default=False,readable=False,writable=False),
		Field('question','text',length=500),
		Field('description','text'),
		Field('tags','list:string',requires=IS_IN_DB(db,db.tags.tag_name,multiple=True),widget=SQLFORM.widgets.checkboxes.widget),
		auth.signature
		)
db.questions.question.requires=IS_NOT_EMPTY(error_message='Please fill in the question field')
#db.questions.tags.requires=IS_IN_DB(db,db.tags)

db.define_table('answer',
		Field('question_id','reference questions',readable=False, writable=False),
		Field('author_name',
			writable=False, readable=False),
		Field('answer','text'),
		Field('upvote','list:string',default=[]),
		auth.signature
		)

db.answer.question_id.requires=IS_IN_DB(db, db.questions)
db.answer.upvote.readable=db.answer.upvote.writable=False
db.answer.question_id.readable=db.answer.question_id.writable=False
db.answer.answer.requires=IS_NOT_EMPTY(error_message='Cant submit an empty answer!')
