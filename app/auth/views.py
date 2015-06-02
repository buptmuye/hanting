# -*- coding: utf-8 -*-
from flask import render_template, redirect, request, url_for, flash, abort
from flask.ext.login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..models import User
from ..email import send_email
from .forms import LoginForm, RegistrationForm, ChangeEmailForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm, WeixinRegistrationForm
import requests

@auth.route('/weixin')
def weixin_login():
    #get code and use it to get access_token
    code = request.args.get('code', 0)
    if 0 == code:
        abort(404)
    token_url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=wxb85b39cce0d2fc57&secret=77b969413906b5059cd468fce8c0f50d&code=%s&grant_type=authorization_code' % code
    token_res = requests.get(token_url).json()
    # you can define accurate error and flash it to user, here i only return 404, should make some improvement
    if 'errcode' in token_res:
        abort(404)
    token = token_res['access_token']
    openid = token_res['openid']

    #use token to get user_info
    info_url = 'https://api.weixin.qq.com/sns/userinfo?access_token=%s&openid=%slang=zh_CN' % (token, openid)
    info_res = requests.get(info_url)
    if 'errcode' in info_res:
        abort(404)
    # should set result to utf-8
    info_res.encoding = 'utf-8'
    info_res = info_res.json()

    #now use user_info to register or login
    user = User.query.filter_by(username=info_res['openid']).first()
    if user is not None and user.confirmed:
        user.name = info_res['nickname']
        user.about_me = info_res['headimgurl']
        user.location = info_res['province'] + info_res['city']
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(request.args.get('next') or url_for('main.index')) 

    #does not exist, should set up a new account which is not confirmed, should add email and password later.
    if user is None:
        user = User(location=info_res['province']+info_res['city'],
                    username=info_res['openid'],
                    name=info_res['nickname'],
                    about_me=info_res['headimgurl'])
        db.session.add(user)
        db.session.commit()
        return render_template('auth/test_weixin.html', user=user)
    
    user.name = info_res['nickname']
    user.about_me = info_res['headimgurl']
    user.location = info_res['province'] + info_res['city']
    db.session.add(user)
    db.session.commit()

    return render_template('auth/test_weixin.html', user=user)

@auth.route('/weixin_register/<username>', methods=['GET', 'POST'])
def weixin_register(username):
    form = WeixinRegistrationForm()
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'用户不存在!')
        return redirect(url_for('auth.register'))
    if form.validate_on_submit():
        user.email = form.email.data
        user.password = form.password.data
        user.phone = form.phone.data
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('main.index'))

    return render_template('auth/weixin_register.html', form=form, nickname=user.name)
