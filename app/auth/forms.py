# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Email, Length, EqualTo, Regexp
from wtforms import ValidationError
#because we want to judge the valid user here, so we import User
from ..models import User

class LoginForm(Form):
    email = StringField(u'电子邮箱名', validators=[Required(message=u'请填写电子邮箱'), Length(1, 64, message=u'确定没有更短的邮箱名吗⊙﹏⊙'), Email(message=u'请填写规范的电子邮箱名')])
    password = PasswordField(u'登录密码', validators=[Required(message=u'请输入登录密码')])
    remember_me = BooleanField(u'记住我')
    submit = SubmitField(u'确认登录')

class RegistrationForm(Form):
    email = StringField(u'电子邮箱名', validators=[Required(message=u'请填写电子邮箱'), Length(1, 64, message=u'确定没有更短的邮箱名吗⊙﹏⊙'), Email(message=u'请填写规范的电子邮箱名')])
    username = StringField(u'用户名', validators=[Required(message=u'请填写用户名'), Length(1, 32, message=u'请填写更简洁的用户名')])
    password = PasswordField(u'登录密码', validators=[Required(message=u'请输入登录密码'), EqualTo('password2', message=u'两次输入密码不匹配')])
    password2 = PasswordField(u'重复输入密码', validators=[Required(message=u'请确认登录密码')])

    submit = SubmitField(u'确认注册')
#validate_attribute(self, ..) will be auto-called when validating the attribute
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'抱歉,该电子邮箱已被注册⊙﹏⊙')
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'抱歉,该用户名已被别人使用⊙﹏⊙')
        
class ChangeEmailForm(Form):
    email = StringField(u'绑定新的Email', validators=[Required(message=u'请填写电子邮箱'), Length(1, 64, message=u'确定没有更短的邮箱名吗⊙﹏⊙'), Email(message=u'请填写规范的电子邮箱名')])
    password = PasswordField(u'输入登录密码', validators=[Required(message=u'请输入登录密码')])
    submit = SubmitField(u'确认绑定该Email')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'抱歉,该电子邮箱已被注册⊙﹏⊙')

class ChangePasswordForm(Form):
    old_password = PasswordField(u'旧密码', validators=[Required(message=u'请输入旧密码')])
    password = PasswordField(u'新密码', validators=[Required(message=u'请输入新密码'), EqualTo('password2', message=u'两次输入密码不匹配')])
    password2 = PasswordField(u'重新输入新密码', validators=[Required(message=u'请确认新密码')])
    submit = SubmitField(u'确认更新密码')

class PasswordResetRequestForm(Form):
    email = StringField(u'输入您的电子邮箱', validators=[Required(message=u'请填写电子邮箱'), Length(1, 64, message=u'确定没有更短的邮箱名吗⊙﹏⊙'), Email(message=u'请填写规范的电子邮箱名')])
    submit = SubmitField(u'确认重置密码')

class PasswordResetForm(Form):
    email = StringField(u'输入您的电子邮箱', validators=[Required(message=u'请填写电子邮箱'), Length(1, 64, message=u'确定没有更短的邮箱名吗⊙﹏⊙'), Email(message=u'请填写规范的电子邮箱名')])
    password = PasswordField(u'输入新的密码', validators=[Required(message=u'请输入新密码'), EqualTo('password2', message=u'两次输入密码不匹配')])
    password2 = PasswordField(u'重复输入密码', validators=[Required(message=u'请确认新密码')])
    submit = SubmitField(u'确认重置密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError(u'电子邮箱不匹配,请确认输入您的电子邮箱名')

class WeixinRegistrationForm(Form):
    email = StringField(u'电子邮箱名', validators=[Required(message=u'请填写电子邮箱'), Length(1, 64, message=u'确定没有更短的邮箱名吗⊙﹏⊙'), Email(message=u'请填写规范的电子邮箱名')])
    password = PasswordField(u'登录密码', validators=[Required(message=u'请输入登录密码'), EqualTo('password2', message=u'两次输入密码不匹配')])
    password2 = PasswordField(u'重复输入密码', validators=[Required(message=u'请确认登录密码')])
    phone = StringField(u'联系方式', validators=[Required(message=u'请填写手机联系方式'), Length(11, 11, message=u'只支持11位的手机号码')])

    submit = SubmitField(u'完善提交')
#validate_attribute(self, ..) will be auto-called when validating the attribute
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'抱歉,该电子邮箱已被注册⊙﹏⊙')
