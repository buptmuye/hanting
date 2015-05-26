# -*- coding: utf-8 -*-
from flask import render_template, redirect, request, url_for, flash, abort
from flask.ext.login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..models import User
from ..email import send_email
from .forms import LoginForm, RegistrationForm, ChangeEmailForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm, WeixinRegistrationForm
import requests

@auth.before_app_request
def before_request():
    if current_user.is_authenticated():
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            return redirect(request.args.get('next') or url_for('main.index'))

        flash(u'密码不符或用户名不存在')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'退出成功')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        
        token = user.generate_confirmation_token()
        send_email(user.email,
                   u'账户激活邮件',
                   'auth/email/confirm',
                   user=user, token=token)
        flash(u'一封激活邮件已发送到您的邮箱,请在一小时内激活账户呦O(∩_∩)O~')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash(u'账户激活成功!')
    else:
        flash(u'激活失败,激活命令失效,请重新获取')
    return redirect(url_for('main.index'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous() or current_user.confirmed:
        return redirect('main.index')
    return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, u'新邮箱激活邮件', 'auth/email/confirm',
               user=current_user, token=token)
    flash(u'新的激活邮件已经发送至您的邮箱')
    return redirect(url_for('main.index'))

@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address',
                       'auth/email/change_email', user=current_user, token=token)
            flash(u'一封激活邮件已经发送至您的新邮箱,请及时查收')
            return redirect(url_for('main.index'))
        else:
            flash(u'密码输入不正确')
    return render_template('auth/change_email.html', form=form)

@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash(u'您已成功绑定新的电子邮箱')
    else:
        flash(u'验证不符,请重新绑定新的电子邮箱')
    return redirect(url_for('main.index'))

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash(u'您的登录密码已经更新')
            return redirect(url_for('main.index'))
        else:
            flash(u'旧登录密码不正确')
    return render_template('auth/change_password.html', form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if current_user.is_authenticated():
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, u'密码重置激活邮件',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
            flash(u'一封密码重置的激活邮件已经发送至您的邮箱,请及时查收')
            return redirect(url_for('auth.login'))
        else:
            flash(u'电子邮箱名输入不正确')
    return render_template('auth/reset_password.html', form=form)

@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if current_user.is_authenticated():
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash(u'您的登录密码已成功重置')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/weixin')
def weixin_login():
    #get code and use it to get access_token
    code = request.args.get('code', 0)
    if 0 == code:
        abort(404)
    token_url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=wxb85b39cce0d2fc57&secret=77b969413906b5059cd468fce8c0f50d&code=%s&grant_type=authorization_code' % code
    token_res = requests.get(token_url).json()
    token = token_res['access_token']
    openid = token_res['openid']

    #use token to get user_info
    info_url = 'https://api.weixin.qq.com/sns/userinfo?access_token=%s&openid=%slang=zh_CN' % (token, openid)
    info_res = requests.get(info_url)
    # should set result to utf-8
    info_res.encoding = 'utf-8'
    info_res = info_res.json()

    #now use user_info to register or login
    user = User.query.filter_by(username=info_res['openid']).first()
    if user is not None and user.confirmed:
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
