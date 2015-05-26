# -*- coding: utf-8 -*-
from flask import render_template, session, redirect, url_for, current_app, flash, request, abort
from flask.ext.login import login_required, current_user
from .. import db, basedir, formats, cache, mc, sae_storage
from ..models import User, Post, Permission, Card, Goods, Detail, Role, Images
from ..email import send_email
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, BindCardForm, GoodsForm, EachbuyForm, ChangeOrderForm, PostForm, ChangeGoodsForm, SearchGoodsForm, SearchCardsForm, ChargeForm
from ..decorators import admin_required, permission_required, saler_required, gmanager_required
from sqlalchemy import and_
import os
from werkzeug import secure_filename
import shutil

#i use memcached and flask-cache
#memcached to cache data of database, reducing offload of db
#flask-cache to cache search-result
#note: when goods change(eg:add,change,delete), some keys in memcached and some pages in flask-cache should clear immediately.

@main.route('/charge/<int:id>', methods=['GET', 'POST'])
@login_required
@saler_required
def charge(id):
    card = Card.query.get_or_404(id)
    form = ChargeForm()
    if form.validate_on_submit():
        card.money += form.money.data
        db.session.add(card)
        db.session.commit()
        flash(u'充值成功！')
        posts = card.author.posts.filter(and_(Post.tag2==0, Post.tag==1)).order_by(Post.timestamp).all()
        return render_template('user-money-order.html', card=card, posts=posts)
    return render_template('charge.html', form=form, card=card)

@main.route('/staff-finish/<int:id>', methods=['GET', 'POST'])
@login_required
@saler_required
def staff_finish(id):
    post = Post.query.get_or_404(id)
    post.tag2 = 1
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('.staff_page'))

@main.route('/staff-page/', methods=['GET', 'POST'])
@login_required
@saler_required
def staff_page():
    lists = Post.query.filter(and_(Post.tag2==0, Post.tag==1)).order_by(Post.timestamp).all()
    form = SearchCardsForm()
    if form.validate_on_submit():
        card = Card.query.filter_by(number=form.number.data).first()
        if card is None:
            flash(u'没有该卡号')
        else:
            if card.author:
                posts = card.author.posts.filter(and_(Post.tag2==0, Post.tag==1)).order_by(Post.timestamp).all()
                return render_template('user-money-order.html', card=card, posts=posts)
            else:
                flash(u'暂无用户绑定该会员卡!')
                return redirect(url_for('.staff_page'))
    return render_template('staff-page.html', lists=lists, len=len(lists), form=form)

@main.route('/search/<goodsname>', methods=['GET'])
@cache.cached()
def search_goods_res(goodsname):
    test = '%' + goodsname + '%'
    res = Goods.query.filter(Goods.name.like(test)).all()
    if not len(res):
        flash(u'没有符合条件的商品，尝试更换关键词')
        return redirect(url_for('.index'))
    else:
        filenames = []
        for item in res:
            image0 = sae_storage.url(item.images[0].name)
            image1 = sae_storage.url(item.images[1].name)
            filenames.append([image0, image1])

        res_images = zip(res, filenames)
        return render_template('search-goods-res.html', res_images=res_images, len=len(res))

@main.route('/', methods=['GET', 'POST'])
def index():
    form = SearchGoodsForm()
    if form.validate_on_submit():
        return redirect(url_for('.search_goods_res', goodsname=form.name.data))

    #use memcache to reduce offload of db
    if mc.get('key_goods_images'):
        goods_images = mc.get('key_goods_images')
        return render_template('index.html', form=form, goods_images=goods_images)

    goods = Goods.query.order_by(Goods.timestamp.desc()).all()
    imagenames = []
    for item in goods:
        image0 = sae_storage.url(item.images[0].name)
        image1 = sae_storage.url(item.images[1].name)
        imagenames.append([image0, image1])
#    filenames = []
#    for item in goods:
#        path = os.path.join(basedir, 'static/uploads/'+item.name)
#        for parent,dirname,files in os.walk(path):
#            filenames.append([files[0], files[1]])
    goods_images = zip(goods, imagenames)
    mc.set('key_goods_images', goods_images)

    #测试render_tempalte能承受多大的list，如果商品数量过多，是否导致flienames传递不了。
    #经过测试，百万量级是可以的，千万的话浏览器崩掉了。
#    testlist = []
#    for i in range(1000000):
#        testlist.append(i)
    return render_template('index.html', form=form, goods_images=goods_images)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in formats

@main.route('/add-goods', methods=['GET', 'POST'])
@login_required
@gmanager_required
def add_goods():
    form = GoodsForm()
    if current_user.can(Permission.FOLLOW) and form.validate_on_submit():
        if Goods.query.filter_by(name=form.name.data).first():
            flash(u'存在相同名字的商品,请修改商品名称')
            return render_template('add-goods.html', form=form)

        files = request.files.getlist('files')
        if len(files) < 2:
            flash(u'上传2张以上的商品图片')
            return render_template('add-goods.html', form=form)

        images = Images.query.all()
        imagenames = []
        for i in images:
            imagenames.append(i.name)
        for file in files:
            filename = secure_filename(file.filename)
            if not file or not allowed_file(filename) or filename in imagenames:
                flash(u'已存在同名图片或图片格式不符，使用.jpg、.jpeg、.png格式')
                return render_template('add-goods.html', form=form)

        goods = Goods(body=form.body.data,
                      name=form.name.data,
                      price=form.price.data)
        db.session.add(goods)
        db.session.commit()

        for file in files:
            filename = secure_filename(file.filename)
            sae_storage.save(file, filename)
            image = Images(name=filename,
                           goods=goods)
            db.session.add(image)
            db.session.commit()

        mc.delete('key_goods_images')
        cache.clear()
        flash(u'成功添加新商品')
        return redirect(url_for('.index'))

    return render_template('add-goods.html', form=form)

@main.route('/change-goods/<int:id>', methods=['GET', 'POST'])
@login_required
@gmanager_required
def change_goods(id):
    goods = Goods.query.get_or_404(id)
    form = ChangeGoodsForm()
    if current_user.can(Permission.FOLLOW) and form.validate_on_submit():
        if goods.name != form.name.data and Goods.query.filter_by(name=form.name.data).first():
            flash(u'已存在同样商品名字，请更改')
            return redirect(url_for('.change_goods', id=id))

        files = request.files.getlist('files')

        images = Images.query.all()
        imagenames = []
        for i in images:
            imagenames.append(i.name)

        for file in files:
            if not file:
                goods.price = form.price.data
                goods.body = form.body.data
                goods.name = form.name.data
                db.session.add(goods)
                db.session.commit()

                mc.delete('key_goods_images')
                mc.delete(str(id))
                mc.delete(str(id)+'image')
                cache.clear()
                flash(u'成功修改商品信息')
                return redirect(url_for('.index'))

            filename = secure_filename(file.filename)
            if not allowed_file(file.filename) or filename in imagenames:
                flash(u'已存在同名图片或者图片格式不符，使用.jpg、.jpeg、.png格式')
                form.name.data = goods.name
                form.price.data = goods.price
                form.body.data = goods.body

                filelist =[]
                for item in goods.images.all():
                    filelist.append([item.name, sae_storage.url(item.name)])

                return render_template('change-goods.html',
                                       form=form,
                                       goods=goods,
                                       filelist=filelist)

        goods.price = form.price.data
        goods.body = form.body.data
        goods.name = form.name.data
        db.session.add(goods)
        db.session.commit()

        for file in files:
            filename = secure_filename(file.filename)
            sae_storage.save(file, filename)
            image = Images(name=filename,
                           goods=goods)
            db.session.add(image)
            db.session.commit()


        mc.delete('key_goods_images')
        mc.delete(str(id))
        mc.delete(str(id)+'image')
        cache.clear()
        flash(u'成功修改商品信息')
        return redirect(url_for('.index'))

    form.name.data = goods.name
    form.price.data = goods.price
    form.body.data = goods.body

    filelist =[]
    for item in goods.images.all():
        filelist.append([item.name, sae_storage.url(item.name)])

    return render_template('change-goods.html',
                           form=form,
                           goods=goods,
                           filelist=filelist)

@main.route('/del-image/<int:id>/<name>', methods=['GET', 'POST'])
@login_required
@gmanager_required
def del_image(id, name):
    goods = Goods.query.get_or_404(id)
    image = Images.query.filter_by(name=name).first()

    if goods.images.count() <= 2:
        flash(u'保留图片个数不能少于2张，请先增加图片')
        return redirect(url_for('.change_goods', id=id))
    if image:
        db.session.delete(image)
        db.session.commit()
        sae_storage.delete(name)
        flash(u'删除图片成功')
    return redirect(url_for('.change_goods', id=id))

@main.route('/delete-goods-all', methods=['GET', 'POST'])
@login_required
@gmanager_required
def delete_goods_all():
    allgoods = Goods.query.all()
    for goods in allgoods:
        for image in goods.images.all():
            sae_storage.delete(image.name)
        db.session.delete(goods)
        db.session.commit()
        mc.delete(str(goods.id))

    mc.delete('key_goods_images')
    cache.clear()
    return redirect(url_for('.index'))

@main.route('/cancel-goods/<int:id>', methods=['GET', 'POST'])
@login_required
@gmanager_required
def cancel_goods(id):
    goods = Goods.query.get_or_404(id)
    if current_user.can(Permission.FOLLOW):
        for image in goods.images.all():
            sae_storage.delete(image.name)
        db.session.delete(goods)
        db.session.commit()

        mc.delete('key_goods_images')
        mc.delete(str(id))
        mc.delete(str(id)+'image')
        cache.clear()
        flash(u'删除商品成功！')
        return redirect(url_for('.index'))

    flash(u'您没有权限删除商品！')
    return redirect(url_for('.index'))

@main.route('/finish-post/<int:id>', methods=['GET', 'POST'])
@login_required
def finish_post(id):
    post = Post.query.get_or_404(id)
    return render_template('finish-post.html', post=post)

@main.route('/cal-post/<int:id>', methods=['GET', 'POST'])
@login_required
def cal_post(id):
    form = PostForm()
    post = Post.query.get_or_404(id)

    if form.validate_on_submit():
        goods = Goods.query.all()
        goodsnames = []
        for i in goods:
            goodsnames.append(i.name)
        details = post.details.all()
        for detail in details:
            print goodsnames[0]
            print detail.name
            if detail.name not in goodsnames:
                flash(u'抱歉，存在已下架或更名的商品！')
                return redirect(url_for('.cancel_detail', id=detail.id))
#        print int(form.payway.data)
        #should update user's information
        post.phone = current_user.phone = form.phone.data
        post.address = current_user.location = form.address.data
        db.session.add(current_user)
        db.session.commit()
        #now should calculate the final cost
        post.payway = int(form.payway.data)
        post.fetchway = int(form.fetchway.data)
        if post.sumcost >= 39:
            if int(form.payway.data) == 0:
                post.tag = 1
                db.session.add(post)
                db.session.commit()
                return redirect(url_for('.finish_post', id=post.id))                 
            else:
                if current_user.cards is None:
                    flash(u'没有会员卡，不能使用在线支付，请使用货到付款，或在自提点办理')
                    return redirect(url_for('.cal_post', id=post.id))           
                if current_user.cards.money < post.sumcost:
                    flash(u'余额不足，请使用货到付款，或在自提点充值')
                    return redirect(url_for('.cal_post', id=post.id))
                else:
                    current_user.cards.money -= post.sumcost
                    db.session.add(current_user)
                    db.session.commit()
                    post.tag = 1
                    db.session.add(post)
                    db.session.commit()
                    return redirect(url_for('.finish_post', id=post.id))
        else:
            if int(form.payway.data) == 0:
                post.tag = 1
                db.session.add(post)
                db.session.commit()
                if int(form.fetchway.data) == 0:
                    post.sumcost += 5
                    db.session.add(post)
                    db.session.commit()
                return redirect(url_for('.finish_post', id=post.id))                 
            else:
                if current_user.cards is None:
                    flash(u'没有会员卡，不能使用在线支付，请使用货到付款，或在自提点办理')
                    return redirect(url_for('.cal_post', id=post.id))           

                if int(form.fetchway.data) == 0:
                    if current_user.cards.money < post.sumcost+5:
                        flash(u'余额不足，请使用货到付款，或自提')
                        return redirect(url_for('.cal_post', id=post.id))
                    else:
                        post.sumcost += 5
                        db.session.add(post)
                        db.session.commit()
                        current_user.cards.money -= post.sumcost
                        db.session.add(current_user)
                        db.session.commit()
                        post.tag = 1
                        db.session.add(post)
                        db.session.commit()
                        return redirect(url_for('.finish_post', id=post.id))
                else:
                    if current_user.cards.money < post.sumcost:
                        flash(u'余额不足，请使用货到付款，或自提')
                        return redirect(url_for('.cal_post', id=post.id))
                    else:
                        current_user.cards.money -= post.sumcost
                        db.session.add(current_user)
                        db.session.commit()
                        post.tag = 1
                        db.session.add(post)
                        db.session.commit()
                        return redirect(url_for('.finish_post', id=post.id))
        
    form.phone.data = current_user.phone
    form.address.data = current_user.location
    return render_template('cal-post.html', form=form, post=post)

@main.route('/delete-post/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_post(id):
    order = Post.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash(u'删除订单记录成功！')
    return redirect(url_for('.his_order'))

@main.route('/cancel-post/<int:id>', methods=['GET', 'POST'])
@login_required
def cancel_post(id):
    order = Post.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    flash(u'成功取消订单')
    return redirect(url_for('.index'))

@main.route('/cancel-detail/<int:id>', methods=['GET', 'POST'])
@login_required
def cancel_detail(id):
    eachorder = Detail.query.get_or_404(id)
    order = eachorder.summary
    if order.details.count() == 1:
        return redirect(url_for('.cancel_post', id=order.id))
    db.session.delete(eachorder)
    db.session.commit()
    flash(u'成功取消订单')
    return redirect(url_for('.order', id=order.id))

@main.route('/change-order/<int:id>', methods=['GET', 'POST'])
@login_required
def change_order(id):
    eachorder = Detail.query.get_or_404(id)
    goods = Goods.query.filter_by(name=eachorder.name).first()
    if goods is None:
        flash(u'抱歉，商品已经下架，请购买其他商品！')
        return redirect(url_for('.cancel_detail', id=id))
    form = ChangeOrderForm()
    if form.validate_on_submit():
        eachorder.numbers = form.numbers.data
        db.session.add(eachorder)
        db.session.commit()
        return redirect(url_for('.order', id=eachorder.summary.id))

    filenames = []
    for item in goods.images.all():
        filenames.append(sae_storage.url(item.name))

    return render_template('change-order.html', eachorder=eachorder, form=form, filenames=filenames, goods=goods)

@main.route('/his-order', methods=['GET', 'POST'])
@login_required
def his_order():
    posts = current_user.posts.order_by(Post.timestamp.desc()).all()
    goods = Goods.query.all()
    goodsnames = []
    for item in goods:
        goodsnames.append(item.name)
    return render_template('his-order.html', posts=posts, goodsnames=goodsnames)

@main.route('/order/<int:id>', methods=['GET', 'POST'])
@login_required
def order(id):
    order = Post.query.get_or_404(id)
    order.sumcost = 0
    for item in order.details.all():
        order.sumcost += item.numbers * item.pricenow
#    db.session.delete(order)
#    db.session.commit()

    return render_template('order.html', order=order)

@main.route('/goods/<int:id>', methods=['GET', 'POST'])
def goods(id):
    if mc.get(str(id)):
        item = mc.get(str(id))
    else:
        item = Goods.query.get_or_404(id)
        mc.set(str(id), item)
    form = EachbuyForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated():
            flash(u'请先登录才能购买')
            return redirect(url_for('.goods', id=id))
        post = current_user.posts.order_by(Post.timestamp.desc()).first()
#        db.session.delete(post)
#        db.session.commit()
        if post is None or (post.tag == True):
            #should add the summary order
            post = Post(author=current_user._get_current_object())
            db.session.add(post)
            db.session.commit()

            detail = Detail(numbers=form.numbers.data,
                            pricenow=item.price,
                            summary=post,
                            name=item.name,
                            goods_id=id)
            db.session.add(detail)
            db.session.commit()
            return redirect(url_for('.order', id=post.id))
        else:
            #summary order exists, only add the each order
            #should put same fruit in one each order
            flag = False
            for i in post.details.all():
                if i.goods_id == id:
                    i.numbers += form.numbers.data
                    flag = True
                    db.session.add(i)
                    db.session.commit()
                    break
            if not flag:
                    detail = Detail(numbers=form.numbers.data,
                                    pricenow=item.price,
                                    summary=post,
                                    name=item.name,
                                    goods_id=id)
                    db.session.add(detail)
                    db.session.commit()

            return redirect(url_for('.order', id=post.id))

    if mc.get(str(id)+'image'):
        filenames = mc.get(str(id)+'image')
    else:
        filenames = []
        goods = Goods.query.get_or_404(id)
        for i in goods.images.all():
            filenames.append(sae_storage.url(i.name))
        mc.set(str(id)+'image', filenames)

    return render_template('item.html', item=item, form=form, filenames=filenames)

@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first()
    if user != current_user and not current_user.is_administrator():
        flash(u'您没有权限查看其他用户个人信息！')
        return redirect(url_for('.user', username=current_user.username))
    if user is None:
        abort(404)
    return render_template('user.html', user=user)

@main.route('/bind-card', methods=['GET', 'POST'])
@login_required
def bind_card():
    form = BindCardForm()
    if form.validate_on_submit():
        card = Card.query.filter_by(number=form.number.data).first()
        if card is None or (not card.varify_password(form.password.data)):
            flash(u'该会员卡号不存在或密码不正确')
            return render_template('bind_card.html', form=form)
        else:
            current_user.cards = card
            db.session.add(current_user)
            db.session.commit()
            flash(u'绑定会员卡成功')
            return redirect(url_for('.user', username=current_user.username))
    if current_user.cards:
        form.number.data = current_user.cards.number
    return render_template('bind_card.html', form=form)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.phone = form.phone.data
        current_user.location = form.address.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash(u'个人资料更新成功!')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.phone.data = current_user.phone
    form.address.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)

@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.phone = form.phone.data
        user.location = form.address.data
        user.about_me = form.about_me.data
        flash(u'用户个人资料更新成功')
        return redirect(url_for('.user', username=user.username))
     
    form.email.data = user.email
    form.phone.data = user.phone
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role
    form.name.data = user.name
    form.address.data = user.location
    form.about_me.data = user.about_me

    return render_template('edit_profile.html', form=form, user=user)
        
