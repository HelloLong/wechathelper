#!/usr/bin/env python3
# coding: utf-8

from flask import Flask, render_template, redirect
import itchat
from itchat.content import *
import base64
from threading import Thread # 多线程
from time import sleep
import os, sys, time, io, re
import threading
import logging
import datetime


dir_path = os.path.dirname(os.path.realpath(__file__))

bot = itchat.new_instance()

def auto_add_member(msg, roomName):
    friend = bot.search_friends(userName=msg['FromUserName'])
    bot.get_chatrooms(update=True)
    chatroom = bot.search_chatrooms(roomName)[0]
    r = bot.add_member_into_chatroom(chatroom['UserName'], [friend], useInvitation=True)
    if r['BaseResponse']['ErrMsg'] == '请求成功':
        return ''
    else:
        return '邀请入群出错，请重试！'

# 普通文本消息，带自动邀请入群
@bot.msg_register(TEXT)
def text_reply(msg):
    if '入群' in msg['Text'].lower():
        return auto_add_member(msg, '群名称')

    return '机器人的回复信息'

# 群消息
@bot.msg_register(TEXT, isGroupChat=True)
def group_reply(msg):
    if msg['IsAt']:
        return u'@%s\u2005%s' % (msg['ActualNickName'], '圈机器人后，在群里的回复，收到：' + msg['Text'])

# 欢迎新人消息
@bot.msg_register(NOTE, isGroupChat=True)
def note_reply(msg):
    try:
        new_member_name = re.search(r'邀请"(.+?)"|"(.+?)"通过', msg['Text']).group(1)
    except AttributeError:
        return

    return '\U0001F389 欢迎新人 @{}\u2005！'.format(new_member_name)

# 收到好友邀请自动添加好友
@bot.msg_register(FRIENDS)
def add_friend(msg):
    bot.add_friend(msg['RecommendInfo']['UserName'], status=3, verifyContent='自动添加好友成功！')
    newer = msg['Text']['autoUpdate']
    bot.send_msg('{} 你好！', newer['UserName'])


def uptime(login_timestamp):
    if bot.alive:
        _uptime = datetime.datetime.now() - login_timestamp
        _uptime = str(_uptime).split('.')[0]
        return '[UPTIME] {}'.format(_uptime)

# 定时报告 uptime
def report_uptime(remote_admin, login_timestamp):
    while True:
        time.sleep(600)
        remote_admin.send(uptime(login_timestamp))


# 机器人主线程
def wechat_main(login_info):
    if not login_info:
        isLoggedIn = False
        while 1:
            waiting_time = 0
            while not isLoggedIn:
                status = bot.check_login()
                waiting_time += 1

                if status == '200':
                    isLoggedIn = True
                elif status == '201':
                    if isLoggedIn is not None:
                        isLoggedIn = None
                elif status != '408':
                    break
                elif waiting_time == 5:
                    raise
            if isLoggedIn:
                break

        bot.web_init()
        bot.show_mobile_login()
        bot.get_contact(True)
        bot.start_receiving()

        bot.dump_login_status(dir_path + '/itchat.pkl')
        bot.hotReloadDir = dir_path + '/itchat.pkl'

    # 记录登录时间戳
    login_timestamp = datetime.datetime.now()
    # 这里需要指定管理员昵称
    remote_admin = bot.search_friends(nickName='管理员')[0]
    remote_admin.send('[START] OK!')
    report_thread = Thread(target=report_uptime, daemon=True, args = (remote_admin, login_timestamp, ))
    report_thread.start()

    bot.run()

# 将二维码转化为base64 string, 简单的使用了全局变量
qr_b64 = ''
def QR_to_b64(uuid, status, qrcode):
    global qr_b64
    qr_b64 = base64.b64encode(qrcode)
    return qr_b64

app = Flask(__name__)

thread = Thread()

@app.route('/')
def index():
    return render_template('index.html', alive=bot.alive, bot=bot)

# 生成二维码 登录
@app.route('/login')
def wechat_login():
    global thread

    if bot.alive:
        return redirect('/')

    if thread.is_alive():
        return render_template('login.html', qr=qr_b64.decode('utf-8'), alive=bot.alive)

    bot.useHotReload = True
    info = bot.load_login_status(dir_path + '/itchat.pkl')

    if not info:
        bot.get_QRuuid()
        bot.get_QR(qrCallback=QR_to_b64)

    thread = Thread(target = wechat_main, daemon=True, args = (info, ))
    thread.start()

    if info:
        return redirect('/')
    else:
        return render_template('login.html', qr=qr_b64.decode('utf-8'), alive=bot.alive)

# 登出
@app.route('/logout')
def logout():
    try:
        bot.logout()
        return redirect('/')
    except Exception as e:
        return "Error {0}".format(str(e))


if __name__ == '__main__':
    start_info = bot.load_login_status(dir_path + '/itchat.pkl')

    if start_info:
        thread = Thread(target = wechat_main, daemon=True, args = (start_info, ))
        thread.start()

    app.run(host='0.0.0.0', port=8080)