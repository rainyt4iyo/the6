from os import name

from flask import render_template, request, redirect, url_for
from testapp import app
import pymysql
import time
import logging
from contextlib import contextmanager


def db_connection():
    return pymysql.connect(host='localhost',
                           user='t4',
                           password='t4_password',
                           database='the6',
                           cursorclass=pymysql.cursors.DictCursor)

def player_information(pid, class_name):
    with db_connection() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM player WHERE pid=%s AND class=%s"
            cursor.execute(sql, (pid, class_name))
            player = cursor.fetchone()
    return player

@app.route('/')
def mainpage():
    return render_template('testapp/mainpage.html')

@app.route('/rules')
def rules():
    return render_template('testapp/rules.html')

@app.route('/player_check')
def player_check():
    with db_connection() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM player"
            cursor.execute(sql)
            players = cursor.fetchall()
    print(players)
    return render_template('testapp/player_check.html', players=players)

@app.route('/result_check')
def result_check(): 
    with db_connection() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM result"
            cursor.execute(sql)
            results = cursor.fetchall()
    print(results)
    return render_template('testapp/result_check.html', results=results)

@app.route('/registration/<grade>')
def registration_choice(grade):
    grade = int(grade)
    if grade == 1:
        grade_list = ["F1", "O1"]
    elif grade == 2:
        grade_list = ["F2", "O2"]
    elif grade == 3:
        grade_list = ["F3", "O3"]
    elif grade == 4:
        grade_list = ["F4", "O4M", "O4W"]
    elif grade == 5:
        grade_list = ["F5M", "F5W", "O5M", "O5W"]
    elif grade == 6:
        grade_list = ["F6M", "F6W", "O6M", "O6W"]
    else:
        grade_list = []

    player_list = []

    for class_name in grade_list:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM player WHERE class=%s"
                cursor.execute(sql, (class_name,))
                players = cursor.fetchall()
        player_list.append(players)
    
    print(player_list)

    if grade == 1 or grade == 2 or grade == 3:
        return render_template('testapp/choice1.html', grade=grade, player_list=player_list, grade_list=grade_list)
    if grade == 4:
        return render_template('testapp/choice4.html', grade=grade, player_list=player_list, grade_list=grade_list)
    if grade == 5 or grade == 6:
        return render_template('testapp/choice5.html', grade=grade, player_list=player_list, grade_list=grade_list)

@app.route('/submit/<class_name>/<pid>', methods=['GET','POST'])
def submit(class_name, pid):
    if request.method == 'GET':
        player = player_information(pid, class_name)
        if player is None:
            return "Player not found", 404
        
        with db_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM result WHERE pid=%s AND class=%s"
                cursor.execute(sql, (pid, class_name))
                result = cursor.fetchone()

        return render_template('testapp/submit.html', player=player, result=result)

    if request.method == 'POST':
        kid = request.form['kid']
        zt = request.form['zt']

        if zt == "":
            zt = 0
        elif zt == "Z":
            zt = 1
        elif zt == "T":            
            zt = 2
        
        with db_connection() as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO result (pid, class, kid, zt) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE kid=%s, zt=%s"
                cursor.execute(sql, (pid, class_name, kid, zt, kid, zt))
            conn.commit()
    
    if class_name in ["F1", "O1"]:
        grade = 1
    elif class_name in ["F2", "O2"]:
        grade = 2
    elif class_name in ["F3", "O3"]:
        grade = 3
    elif class_name in ["F4", "O4M", "O4W"]:
        grade = 4
    elif class_name in ["F5M", "F5W", "O5M", "O5W"]:
        grade = 5
    elif class_name in ["F6M", "F6W", "O6M", "O6W"]:
        grade = 6
    else:
        return "Invalid class", 400

    return redirect(url_for('player_check', grade=grade))