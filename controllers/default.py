# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
#########################################################################

@auth.requires_login()
def alllist():
	if len(request.args): page=int(request.args[0])
	else: page=0
	items_per_page=10
	limitby=(page*items_per_page,(page+1)*items_per_page+1)
	topics=db().select(db.tags.ALL, limitby=limitby, orderby=db.tags.tag_name)
	return dict(page=page, items_per_page=items_per_page,user=user,topics=topics)

def subscribe():
	vars=request.post_vars
	tag=str(vars.tagid)
	subscriptions=auth.user.subscribed
	if tag not in subscriptions:
		subscriptions.insert(0,tag)
	else:
		subscriptions.remove(tag)
	row=db(db.auth_user.id==auth.user.id).select().first()
	row.update_record(subscribed=subscriptions)
	
@auth.requires_login()
def questions():
	tagname=request.args(0) or redirect(URL('index'))
	page=request.args(1,cast=int,default=0)
	items_per_page=5
	limitby=(page*items_per_page,(page+1)*items_per_page+1)
	tagname=str(tagname)
	question=db().select(db.questions.ALL,limitby=limitby ,orderby=~db.questions.created_on)
	return dict(tagname=tagname, page=page, items_per_page=items_per_page,user=user,question=question)

@auth.requires_login()
def answer():
	questionid=request.args(0, cast=int) or redirect(URL('index'))
	form=SQLFORM(db.answer)
	question=db(db.questions.id==questionid).select(db.questions.ALL)
	answers=db(db.answer.question_id==questionid).select(db.answer.ALL, orderby=~db.answer.created_on)
	if form.process().accepted:
		cur=form.vars.id
		row=db(db.answer.id==cur).select().first()
		row.update_record(question_id=questionid)
		row.update_record(author_name=auth.user.username)
		redirect(URL('answer', args=questionid))
	return dict(question=question, form=form, answers=answers, questionid=questionid)

def star():
	vars=request.post_vars
	qid=str(vars.qid)
	print qid
	stars=auth.user.starred
	if qid not in stars:
		stars.insert(0,qid)
	else:
		stars.remove(qid)
	print stars
	row=db(db.auth_user.id==auth.user.id).select().first()
	row.update_record(starred=stars)
	
@auth.requires_login()
def index():
	print auth.user.profile_picture
	alltags=db().select(db.tags.ALL)
	question=db().select(db.questions.ALL,orderby=~db.questions.created_on)
	return dict(question=question,alltags=alltags)
	
@auth.requires_login()
def yourques():
	if len(request.args): page=int(request.args[0])
	else: page=0
	items_per_page=4
	limitby=(page*items_per_page,(page+1)*items_per_page+1)
	question=db(db.questions.created_by==auth.user.id).select(limitby=limitby,orderby=~db.questions.modified_on)
	return dict(page=page, items_per_page=items_per_page,user=user,question=question,edita="EDIT/DELETE")

@auth.requires_login()
def ask():
	form=SQLFORM(db.questions)
	if form.process().accepted:
		cur=form.vars.id
		row=db(db.questions.id==cur).select().first()
		row.update_record(author_name=auth.user.username)
		response.flash = 'form accepted'
	elif form.errors:
		response.flash = 'form has errors'
	else:
		response.flash = 'fill form'
	return dict(form=form)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)

@auth.requires_membership('AppAdmn')
def manage():
	grid=SQLFORM.grid(db.questions,paginate=10,editable=False)
	return dict(grid=grid)

def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

@auth.requires_login()
def search():
	return dict(form1=FORM(INPUT(_id='keyword1',_name='keyword1', _onkeyup="ajax('callback2', ['keyword1'], 'target1');")),target_div1=DIV(_id='target1'),form2=FORM(INPUT(_id='keyword2',_name='keyword2', _onkeyup="ajax('callback3', ['keyword2'], 'target2');")),target_div2=DIV(_id='target2'),form3=FORM(INPUT(_id='keyword3',_name='keyword3', _onkeyup="ajax('callbackcomb', ['keyword3'], 'target3');")),target_div3=DIV(_id='target3'))

def callback2():
	if not request.vars.keyword1: return ''
	query = db.questions.question.contains(request.vars.keyword1)
	ques = db(query).select(orderby=db.questions.question)
	links = [A(p.question, _href=URL('answer',args=p.id)) for p in ques]
	return DIV(*[DIV(k,  _onmouseover="this.style.backgroundColor='yellow'", _onmouseout="this.style.backgroundColor='white'")for k in links])

def callback3():
	if not request.vars.keyword2: return ''
	ques = db(db.questions.author_name.contains(request.vars.keyword2) & (db.questions.anonymous==False)).select(orderby=db.questions.question)
	#ques = db(query).select(orderby=db.questions.question)
	links = [A(p.question+ "(" + p.author_name + ")" , _href=URL('answer',args=p.id)) for p in ques]
	return DIV(*[DIV(k,  _onmouseover="this.style.backgroundColor='yellow'", _onmouseout="this.style.backgroundColor='white'")for k in links])

def callbackcomb():
	if not request.vars.keyword3: return ''
	query = db.questions.question.contains(request.vars.keyword3)
	ques = db(query).select(orderby=db.questions.question)
	links = [A(p.question + "(Body)",  _href=URL('answer',args=p.id)) for p in ques]
	ques2 = db(db.questions.author_name.contains(request.vars.keyword2) & (db.questions.anonymous==False)).select(orderby=db.questions.question)
	links2 = [A(p.question+ "(" + p.author_name + ")" , _href=URL('answer',args=p.id)) for p in ques2]
	links=links+links2
	return DIV(*[DIV(k,  _onmouseover="this.style.backgroundColor='yellow'", _onmouseout="this.style.backgroundColor='white'")for k in links])

@auth.requires_membership('AppAdmn')
def admin():
	if len(request.args): page=int(request.args[0])
	else: page=0
	items_per_page=2
	limitby=(page*items_per_page,(page+1)*items_per_page+1)
	ques=db().select(db.questions.ALL,limitby=limitby,orderby=~db.questions.created_on)
	return dict(page=page, items_per_page=items_per_page,user=user,ques=ques)


def validate():
	vars=request.post_vars
	qid=(vars.qid)
	row=db(db.questions.id==qid).select().first()
	row.update_record(judged=True,sensible=True)
def devalidate():
	vars=request.post_vars
	qid=(vars.qid)
	row=db(db.questions.id==qid).select().first()
	row.update_record(judged=True,sensible=False)


def edita():
        row=db.questions(request.args(0,cast=int))
	form=SQLFORM(db.questions,row,deletable=True)
	form.process(detect_record_change=True)
	x=row.created_by
	print x
	if x!=auth.user.id:
		return dict(form="Not Authorised")
	if form.accepted:
	 	row.update()
		response.flash = 'Recipe Updated'
		redirect(URL('yourques'))
	elif form.errors:
		response.flash = 'Fill The Form Correctly'
	else:
		response.flash = 'Edit The Form as Per Your Choice'
	return dict(form=form)


def like():
	newbie="Newbie"
	underdog="Underdog"
	risingstar="risingstar"
	allrounder="Allrounder"
	master="Master"
	sensei="Sensei"
	vars=request.post_vars
	answerid=vars.answerid
	row=db(db.answer.id==int(answerid)).select().first()
	row1=db(db.auth_user.id==row.created_by).select().first()
	totallikes=int(row1.totalupvotes)
	liked=row.upvote
	userid=str(auth.user.id)
	if userid not in liked:
		totallikes=totallikes+1
	        liked.insert(0,userid)
	else:
	        totallikes=totallikes-1
	        liked.remove(userid)
	row1.update_record(totalupvotes=totallikes)
	row.update_record(upvote=liked)
	if totallikes < 2:
	        row1.update_record(category=newbie)
	elif totallikes > 2 and totallikes <= 50: 
	        row1.update_record(category=underdog)
	elif totallikes > 50 and totallikes <=100:
	        row1.update_record(category=risingstar)
	elif totallikes > 100 and totallikes <=500:
	        row1.update_record(category=allrounder)
	elif totallikes > 500 and totallikes <=100:
	        row1.update_record(category=master)
	elif totallikes > 1000:
	        row1.update_record(category=sensei)
	return len(liked)

@auth.requires_login()
def profile():
	if request.args(0)=='hello':
		userid=auth.user.id
	else:
		userid=request.args(0) or redirect(URL('index'))
	user=db(db.auth_user.id==userid).select().first()
	questions=db((db.questions.created_by==userid) & (db.questions.anonymous==False)).select(orderby=db.questions.created_on)
	questionsforanswers=db().select(db.questions.ALL)
	return dict(user=user,questions=questions,questionsforanswers=questionsforanswers)

@auth.requires_login()
def starred():
	questions=db().select(db.questions.ALL)
	return dict(questions=questions)

