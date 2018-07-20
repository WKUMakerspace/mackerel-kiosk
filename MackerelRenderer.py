#!/usr/bin/python

from flask import Flask, redirect, url_for, render_template, request
from wtforms import Form, TextField, validators, StringField, SubmitField

from datetime import datetime

from MackerelClient import MackerelClient
from saltgen import SaltShaker

import logging

app = Flask(__name__)
client = MackerelClient('kiosk', 'kiosk')
client.ip = '161.6.145.51'
client.port = 4400


def make_salt():
    dt = datetime.now()
    dt = datetime(dt.year, dt.month, dt.day)
    ts = int(dt.strftime('%s'))

    ss = SaltShaker(ts)
    for _ in range(100):
        salt = ss.nextRand(32)

    return salt


class SignInForm(Form):
    wkuid = TextField('WKU ID#:', validators=[validators.required(),
                                              validators.Regexp('80[0-9]{7}')])
    description = StringField('Description:')
    signin = SubmitField('Sign in')


class SignOutForm(Form):
    wkuid = TextField('WKU ID#:', validators=[validators.required(),
                                              validators.Regexp('80[0-9]{7}')])
    signout = SubmitField('Sign out')


class CreateUserForm(Form):
    wkuid = TextField('WKU ID#:', validators=[validators.required(),
                                              validators.Regexp('80[0-9]{7}')])
    signin = SubmitField('Sign out')


def forms():
    return {'signin': SignInForm(),
            'signout': SignOutForm(),
            'user_create': CreateUserForm()}


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', forms=forms())


def send_command(cmd, *args):
    args = list(args)
    wkuid = int(args[0])
    salt = make_salt()
    wkuid ^= salt
    args[0] = str(wkuid)
    return client.run_command(cmd, *args)


@app.route('/user_create', methods=['POST'])
def user_create(*args):
    wkuid = request.form['wkuid']
    first = request.form['first']
    last = request.form['last']
    phone = request.form['phone']
    args = [wkuid, last, first, phone] if phone else [wkuid, last, first]
    success, _ = send_command('USER_CREATE', *args)
    if success:
        # Fading message.
        pass

    return redirect(url_for('index'))


@app.route('/signin', methods=['POST'])
def signin():
    wkuid = request.form['wkuid']
    desc = request.form['desc']
    args = [wkuid, desc] if desc else [wkuid]
    success, _ = send_command('SIGNIN', *args)
    if success:
        client.users.add(args[0])
        # Fading message.
        pass
    return redirect(url_for('index'))


@app.route('/signout', methods=['POST'])
def signout(*args):
    wkuid = request.form['wkuid']
    args = [wkuid]
    success, _ = send_command('SIGNOUT', *args)
    if success:
        try:
            client.users.remove(args[0])
        except KeyError:
            # User not signed in.
            pass
        # Fading message.
        pass

    return redirect(url_for('index'))


def __main__():
    app.run(host='localhost', port=1729)


if __name__ == '__main__':
    client.connect()
    __main__()
    client.disconnect()
