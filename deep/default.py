import datetime

now=datetime.datetime.now


@auth.requires_login()
def index():
    if len(request.args):
        page=int(request.args[0])
    else:
        page=0
    items_per_page=2
    limitby=(page*items_per_page,(page+1)*items_per_page+1)
    rows=db().select(db.image.ALL, limitby=limitby, orderby=~db.image.upload_date)
    return dict(rows=rows, page=page, items_per_page=items_per_page)



def myprofile():
    x=auth.user
    if len(request.args):
        page=int(request.args[0])
    else:
        page=0
    items_per_page=2
    limitby=(page*items_per_page,(page+1)*items_per_page+1)
    rows=db(db.image.author_id==auth.user.id).select(db.image.ALL,limitby=limitby, orderby=~db.image.upload_date)
    coms=db(db.post.author_id==auth.user.id).select(db.post.ALL,limitby=limitby)
    return dict(rows=rows, page=page, items_per_page=items_per_page,x=x,coms=coms)

def showprofile():
    auid=request.args(0,cast=int) or redirect(URL('index'))
    if auid==auth.user.id :
        redirect(URL('myprofile'))
    x=db(db.auth_user.id==auid).select(db.auth_user.ALL)
    rows=db(db.image.author_id==x[0].id).select(db.image.ALL,orderby=~db.image.upload_date)
    coms=db(db.post.author_id==x[0].id).select(db.post.ALL)
    return dict(rows=rows,x=x,coms=coms)

def upload():
    form=SQLFORM(db.image)
    if form.process().accepted:
        cur=form.vars.id
        row=db(db.image.id==cur).select().first()
        row.update_record(author_id=auth.user.id)
        row.update_record(upload_date=now)
        response.flash = 'Your Image Has Been Uploaded'
        redirect(URL('addtag',args=cur))
    return dict(form=form)

def addtag():
    imgid=request.args[0]
    return dict(form=FORM(INPUT(_id='keyword',_name='keyword', _onkeyup="ajax('func', ['keyword','imgid'], 'target');")),target_div=DIV(_id='target'))
 
def func():
    if not request.vars.keyword: return ''
    query = db.tags.name.contains(request.vars.keyword)
    tag = db(query).select(orderby=db.tags.name)
    links = [P([p.name,p.id]) for p in tag]
    imgid=request.vars.imgid
    return DIV(*[DIV(k[0], _onmouseclick="ajax('uptag',['k[1]','imgid'],'target')", _onmouseover="this.style.backgroundColor='yellow'", _onmouseout="this.style.backgroundColor='white'")for k in links])
    
def uptag():
    tagid=request.vars.k[1]
    imgid=request.vars.imgid
    tag=db(db.tag.id==tagid).select(db.tag.ALL)
    tag[0].imglist.append(imgid)
    img=db(db.image.id==imgid).select(db.image.ALL)
    img[0].taglist.append(tagid)
    return dict()
    
def search():
    return dict(form=FORM(INPUT(_id='keyword',_name='keyword', _onkeyup="ajax('callback', ['keyword'], 'target');")),target_div=DIV(_id='target'))


def callback():
    query = db.image.title.contains(request.vars.keyword)
    images = db(query).select(orderby=db.image.title)
    links = [A(p.title, _href=URL('show',args=p.id)) for p in images]
    return UL(*links)


def search2():
    return dict(form1=FORM(INPUT(_id='keyword1',_name='keyword1', _onkeyup="ajax('callback2', ['keyword1'], 'target1');")),target_div1=DIV(_id='target1'),form2=FORM(INPUT(_id='keyword2',_name='keyword2', _onkeyup="ajax('callback3', ['keyword2'], 'target2');")),target_div2=DIV(_id='target2'),form3=FORM(INPUT(_id='keyword3',_name='keyword3', _onkeyup="ajax('callbackcomb', ['keyword3'], 'target3');")),target_div3=DIV(_id='target3'))

def callback2():
    if not request.vars.keyword1: return ''
    query = db.image.title.contains(request.vars.keyword1)
    images = db(query).select(orderby=db.image.title)
    links = [A(p.title, _href=URL('show',args=p.id)) for p in images]
    return DIV(*[DIV(k,  _onmouseover="this.style.backgroundColor='yellow'", _onmouseout="this.style.backgroundColor='white'")for k in links])

def callback3():
    if not request.vars.keyword2: return ''
    query = db.auth_user.username.contains(request.vars.keyword2)
    users = db(query).select(orderby=db.auth_user.username)
    links = [A(p.username, _href=URL('showprofile',args=p.id)) for p in users]
    return DIV(*[DIV(k,  _onmouseover="this.style.backgroundColor='yellow'", _onmouseout="this.style.backgroundColor='white'")for k in links])

def callbackcomb():
    if not request.vars.keyword3: return ''
    query1 = db.image.title.contains(request.vars.keyword3)
    images = db(query1).select(orderby=db.image.title)
    links1 = [A(p.title + " (image)", _href=URL('show',args=p.id)) for p in images]
    query = db.auth_user.username.contains(request.vars.keyword3)
    users = db(query).select(orderby=db.auth_user.username)
    links = [A(p.username+" (user)", _href=URL('showprofile',args=p.id)) for p in users]
    links=links+links1
    return DIV(*[DIV(k,  _onmouseover="this.style.backgroundColor='yellow'", _onmouseout="this.style.backgroundColor='white'")for k in links])

def show():
	imgid=request.args(0,cast=int) or redirect(URL('index'))
       	image=db(db.image.id==imgid).select(db.image.ALL)
        db.post.image_id.default = image[0].id
        db.post.author_id.default = auth.user.id
        form = SQLFORM(db.post)
        like1=image[0].like1
        like2=image[0].like2
        like3=image[0].like3
        like4=image[0].like4
        like5=image[0].like5
        totlik=like1+like2+like3+like4+like5
        if form.process().accepted:
            response.flash = 'your comment is posted'
        comments = db(db.post.image_id==imgid).select()
	return dict(image=image, comments=comments,form=form,like1=like1,like2=like2,like3=like3,like4=like4,like5=like5,totlik=totlik)

def like_count():
	imgid=request.args(0,cast=int) or redirect(URL('index'))
       	image=db(db.image.id==imgid).select(db.image.ALL)
        like1=image[0].like1
        like2=image[0].like2
        like3=image[0].like3
        like4=image[0].like4
        like5=image[0].like5
        totlik=like1+like2+like3+like4+like5
	return dict(like1=like1,like2=like2,like3=like3,like4=like4,like5=like5,totlik=totlik)



def like_image():
    print "\n\n\nreturning1"
    type= request.args[1]
    img = db.image[request.args[0]]
    print request.args[0]
    like = db((db.likes.created_by == auth.user.id) & (db.likes.imageid == img.id)).select().first()
    print "returningnew"
    if like:
        print "if"
        if like.score==1:
            img.update_record(like1=img.like1-1)
            print "if me 1st"
            print img.like1
        elif like.score==2:
            img.update_record(like2=img.like2-1)
        elif like.score==3:
            img.update_record(like3=img.like3-1)
        elif like.score==4:
            img.update_record(like4=img.like4-1)
        elif like.score==5:
            img.update_record(like5=img.like5-1)
            like.update_record(score=type)
        if type==str(1):
            img.update_record(like1=img.like1+1)
            print "if me 1st"
            print img.like1
        elif type==str(2):
            img.update_record(like2=img.like2+1)
        elif type==str(3):
            img.update_record(like3=img.like3+1)
        elif type==str(4):
            img.update_record(like4=img.like4+1)
        elif type==str(5):
            img.update_record(like5=img.like5+1)
            like.update_record(score=type)
        like.update_record(score=int(type))

    else:
        print "else"
        print auth.user.id
        print img.id
        db.likes.insert(score=type,created_by=auth.user.id,imageid=img.id)
        print type
        if type==str(1):
            img.update_record(like1=img.like1+1)
            print "else wala"
            print img.like1
        elif type==str(2):
            img.update_record(like2=img.like2+1)
        elif type==str(3):
            img.update_record(like3=img.like3+1)
        elif type==str(4):
            img.update_record(like4=img.like4+1)
        elif type==str(5):
            img.update_record(like5=img.like5+1)
            like.update_record(score=type)
        print "khatam ho gaya"
    totlik=img.like1+img.like2+img.like3+img.like4+img.like5
    img.update_record(total=totlik)
    print totlik
    return dict(like1=img.like1,like2=img.like2,like3=img.like3,like4=img.like4,like5=img.like5,totlik=totlik)

def delete():
    imgid=request.args[0]
    db(db.image.id==imgid).delete()
    redirect(URL('myprofile'))

def edit():
    row=db.image(request.args(0,cast=int))
    imgid=row.id
    form=SQLFORM(db.image,row)
    form.process(detect_record_change=True)
    x=row.author_id
    if x!=auth.user.id:
        return dict(form="Not Authorised")
    db(db.image.id==x).delete()
    if form.accepted:
        row.update()
        response.flash = 'Image Updated'
        redirect(URL('show',args=row.id))
    elif form.errors:
        response.flash = 'Fill the form properly'
    else:
        response.flash='Edit the form as per your choice'
    return dict(form=form,imgid=imgid)

def manage():
    grid=SQLFORM.grid(db.image,paginate=10)
    return locals()

def user():
    return dict(form=auth())

@cache.action()
def download():
    return response.download(request,db)

def call():
    return service()

def test():
    return "hi"
