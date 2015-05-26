# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, PasswordField, FloatField, IntegerField, DecimalField, RadioField
from wtforms.validators import Required, Length, Regexp, Email, NumberRange
from wtforms import ValidationError
from ..models import Role, User, Card, Post, Detail, Goods

class ChargeForm(Form):
    money = IntegerField(u'充值金额', validators=[Required(u'充值金额不能为空!'), NumberRange(min=20, message=u'充值金额最少为20元!')])
    submit = SubmitField(u'确认充值')

class SearchCardsForm(Form):
    number = StringField(u'会员卡号', validators=[Required(u'搜索会员卡号不能为空!'), Length(11, 11, message=u'请输入11位的会员卡号'), Regexp('^[0-9]+$', message=u'会员卡号为11位的数字')])
    submit = SubmitField(u'开始搜索')
    
class SearchGoodsForm(Form):
    name = StringField(u'搜索商品', validators=[Required(u'请输入要搜索的商品名O(∩_∩)O~')])
    submit = SubmitField(u'点击搜索')
    
#    def validate_name(self, field):
#        if Goods.query.whoosh_search(field.data).first() is None:
#            raise ValidationError('no such goods.')

class ChangeGoodsForm(Form):
    name = StringField('name', validators=[Required(message=u'商品名字不能为空!')])
    price = DecimalField('Goods Price', places=2, rounding='ROUND_UP', validators=[Required(u'商品价格不能为空!'), NumberRange(min=1, message=u'商品价格单位最小为1元呦~')])
    body = TextAreaField("Goods Introduce", validators=[Required(message=u'商品简介不能为空'), Length(max=256, message=u'商品简介字数过多')])
    submit = SubmitField('Submit')
#    images = FileField('images', validators=[FileRequired(),
#                                             FileAllowed(['jpg'], '(.jpg) images only!')])

class PostForm(Form):
    phone = StringField(u'联系方式', validators=[Required(message=u'请输入手机联系方式!'), Length(11, 11, message=u'只支持11位的电话哦⊙﹏⊙')])
    address = TextAreaField(u'收货地址', validators=[Length(1, 128, message=u'确定没有更简短的送货地址吗⊙﹏⊙')])
    payway = RadioField('methods of payment',
                        choices=[('0', u'货到付款'),
                                 ('1', u'在线余额支付')],
                        default='1')
    fetchway = RadioField('fetch methods',
                          choices=[('0', u'送货上门'),
                                   ('1', u'自提')],
                          default='0')
    submit = SubmitField(u'确认下单')

class ChangeOrderForm(Form):
    numbers = IntegerField('numbers', validators=[Required(message=u'购买数量至少为1'), NumberRange(min=1, message=u'购买数量至少为1')])

class EachbuyForm(Form):
    numbers = IntegerField('numbers', validators=[Required(message=u'购买数量至少为1'), NumberRange(min=1, message=u'购买数量至少为1')])

class EditProfileForm(Form):
    name = StringField(u'真实姓名（可空）', validators=[Length(0, 32, message=u'没有更简短的名字了吗⊙﹏⊙')])
    phone = StringField(u'联系方式', validators=[Required(message=u'请输入11位的手机联系方式'), Length(11, 11, message=u'请输入11位的手机联系方式')])
    address = TextAreaField(u'收货地址', validators=[Length(0, 128, message=u'确定没有更简短的送货地址吗⊙﹏⊙')])
    about_me = TextAreaField(u'自我简介（可空）', validators=[Length(0, 128, message=u'可以更简短的介绍自己呀(⊙o⊙)')])
    submit = SubmitField(u'确认修改')

class BindCardForm(Form):
    number = StringField(u'新的会员卡号', validators=[Required(message=u'请绑定11位的会员卡号'), Length(11, 11, message=u'请绑定11位的会员卡号'), Regexp('^[0-9]+$', message=u'会员卡都是纯数字哦(⊙o⊙)')])
    password = PasswordField(u'会员卡密令', validators=[Required(message=u'请输入会员卡密令')])
    submit = SubmitField(u'确认绑定')
    def validate_number(self, field):
        if Card.query.filter_by(number=field.data).first() is None:
            raise ValidationError(u'该会员卡号不存在')

class EditProfileAdminForm(Form):
    email = StringField(u'电子邮箱', validators=[Required(message=u'请填写电子邮箱'), Length(1, 64, message=u'确定没有更短的邮箱名吗⊙﹏⊙'), Email(message=u'请填写规范的电子邮箱名')])
    username = StringField(u'用户名', validators=[Required(message=u'请填写用户名'), Length(1, 32, message=u'请填写更简洁的用户名')])
    confirmed = BooleanField(u'是否认证')
    #i put choices in __init__ function
    role = SelectField(u'角色权限', coerce=int)
    name = StringField(u'真实姓名', validators=[Length(0, 64, message=u'您没有更简短的名字吗⊙﹏⊙')])
    phone = StringField(u'联系方式', validators=[Required(message=u'请填写手机联系方式'), Length(11, 11, message=u'只支持11位的手机号码')])
    address = TextAreaField(u'收货地址', validators=[Length(0, 128, message=u'确定没有更简短的送货地址吗⊙﹏⊙')])
    about_me = TextAreaField(u'自我描述')
    submit = SubmitField(u'确认修改')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.filter_by(name=Role.name).all()]
        self.user = user
    #i define validate_email/username, because these two are unique attributes, so system should judge after editing     
    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError(u'抱歉,该电子邮箱已被注册⊙﹏⊙')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError(u'抱歉,该用户名已被别人使用')

class GoodsForm(Form):
    name = StringField('Goods Name', validators=[Required(message=u'请填写商品名称'), Length(1, 32, message=u'商品名字不要过长')])
#    price = FloatField('Goods Price', validators=[Required(), NumberRange(min=0)])
    price = DecimalField('Goods Price', places=2, rounding='ROUND_UP', validators=[Required(message=u'请填写商品价格'), NumberRange(min=1, message=u'商品价格单位最小为1元')])
    body = TextAreaField("Goods Introduce", validators=[Required(message=u'商品简介不能为空'), Length(max=256, message=u'商品简介字数过多')])
#    def validate_name(self, field):
#        if Goods.query.filter_by(name=field.data).first():
#            raise ValidationError(u'存在相同名字的商品,请修改商品名称')
#images don't need to be inside a form
#    images = FileField('images', validators=[FileRequired(),
#                                             FileAllowed(['jpg'], '(.jpg) images only!')])
