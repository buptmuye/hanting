# -*- coding: utf-8 -*-
from flask import current_app, request
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from flask.ext.login import UserMixin, AnonymousUserMixin
from datetime import datetime
import hashlib

class Images(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, index=True)
    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'))

class Goods(db.Model):
    __tablename__ = 'goods'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    name = db.Column(db.String(64), unique=True, index=True)
    price = db.Column(db.Float, default=100)
    body = db.Column(db.Text)
    images = db.relationship('Images', backref='goods', lazy='dynamic', cascade='all, delete, delete-orphan')
#    details = db.relationship('Detail', backref='goods', lazy='dynamic')
#    list_id = db.Column(db.Integer, db.ForeignKey('details.id'))

class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    money = db.Column(db.Float, default=5)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def varify_password(self, password):
        return check_password_hash(self.password_hash, password)
        
class Permission:
    FOLLOW = 0x01             #manage goods
    COMMENT = 0x02            #charge money and handle orders
    WRITE_ARTICLES = 0x04     #leave for future use
    MODERATE_COMMENTS = 0x08  #leave for future use
    ADMINISTER = 0x80

class Role(db.Model, UserMixin):
    '''
    we let each other diffent bit 1, 
    follow:   0b00000001 0x01 --manage goods
    commit:   0b00000010 0x02 --charge money and handle orders
    write:    0b00000100 0x04 --
    full:     0b10000000 0x80
    '''
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
#default: normal user is true, moderate/admin user is false
    default = db.Column(db.Boolean, default=True, index=True)
    permissions = db.Column(db.Integer)

#permissions such as follow/commit/write/moderate/full-access
    @staticmethod
    def insert_roles():
        roles = {
            'User': (0x00, True),
            'Saler': (Permission.COMMENT, False),
            'GManager': (Permission.FOLLOW, False),
            'Manager': (Permission.FOLLOW | 
                        Permission.COMMENT |
                        Permission.WRITE_ARTICLES, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            # r: User/Saler/GManager/Manager/Administrator
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

class Detail(db.Model):
    __tablename__ = 'details'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    name = db.Column(db.String(64))
    pricenow = db.Column(db.Float)
    numbers = db.Column(db.Integer)
    goods_id = db.Column(db.Integer)
#    goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'))
#    goods = db.relationship('Goods', backref='list', uselist=False)

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    sumcost = db.Column(db.Float, default=0)
    phone = db.Column(db.String(11))
    address = db.Column(db.Text)
    payway = db.Column(db.Integer)
    fetchway = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    details = db.relationship('Detail', backref='summary', lazy='dynamic', cascade='all, delete, delete-orphan')
    tag = db.Column(db.Boolean, default=False)
    tag2 = db.Column(db.Boolean, default=False)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    phone = db.Column(db.String(11))
    location = db.Column(db.Text())
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    #i use avatar_hash to store the hashlib for avatar, reducing CPU load
    avatar_hash = db.Column(db.String(32))
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete, delete-orphan')
    cards = db.relationship('Card', backref='author', uselist=False)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                #will be assigned admin role, because 0xff
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                #will be assigned user role, because only user's default is True
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})
    
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
           data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first():
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def can(self, permissions):
        #judge if the role contains permissions
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def __repr__(self):
        return '<User %r>' % self.username

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

