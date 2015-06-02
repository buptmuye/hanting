# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Email, Length, EqualTo, Regexp
from wtforms import ValidationError
#because we want to judge the valid user here, so we import User
from ..models import User

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
