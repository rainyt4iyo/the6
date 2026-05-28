from itertools import count
from os import name

from flask import render_template, request, redirect, url_for
from testapp import app
import pymysql
import time
import logging
from contextlib import contextmanager

BASE_POINT = 50

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

def area2number(area):
    if area == "A":
        return (1, 2)
    elif area == "B":
        return (3, 4)
    elif area == "C":
        return (5, 6)
    elif area == "D":
        return (7, 8)
    elif area == "E":
        return (9, 10)
    elif area == "F":
        return (11, 12)
    elif area == "G":
        return (13, 14)
    elif area == "H":
        return (15, 16)
    elif area == "I":
        return (17, 18)
    else:
        return None
    
@app.route('/')
def mainpage():
    return render_template('testapp/mainpage.html')

@app.route('/hub')
def information():
    return render_template('testapp/hub.html')

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

@app.route('/registration/<area>/<grade>')
def registration_choice(grade, area):
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
        return render_template('testapp/choice1.html', grade=grade, player_list=player_list, grade_list=grade_list, area=area)
    if grade == 4:
        return render_template('testapp/choice4.html', grade=grade, player_list=player_list, grade_list=grade_list, area=area)
    if grade == 5 or grade == 6:
        return render_template('testapp/choice5.html', grade=grade, player_list=player_list, grade_list=grade_list, area=area)

@app.route('/submit/<area>/<class_name>/<pid>', methods=['GET','POST'])
def submit(area, class_name, pid):
    nums = area2number(area)
    if nums is None:
        return "Invalid area", 400 

    if request.method == 'GET':
        player = player_information(pid, class_name)
        if player is None:
            return "Player not found", 404

        with db_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM result WHERE pid=%s AND class=%s"
                cursor.execute(sql, (pid, class_name))
                res = cursor.fetchall()
                print(res)
    
        res_0 = next((row for row in res if str(row.get('kid')) == str(nums[0])), {'pid': pid, 'class': class_name, 'kid': nums[0], 'zt': 0})
        res_1 = next((row for row in res if str(row.get('kid')) == str(nums[1])), {'pid': pid, 'class': class_name, 'kid': nums[1], 'zt': 0})
        result = [res_0, res_1]

        print(result)
        return render_template('testapp/submit.html', player=player, result=result, nums=nums, area=area)

    if request.method == 'POST':
        with db_connection() as conn:
            with conn.cursor() as cursor:
                # 2つのエリア分、ループ処理で順番に保存する
                for num in nums:
                    # HTMLの name="zt_1" や name="zt_2" から値を取得
                    zt_value = request.form.get(f'zt_{num}', '')

                    if zt_value == "":
                        zt = 0
                    elif zt_value == "Z":
                        zt = 1
                    elif zt_value == "T":            
                        zt = 2
                    
                    # 各エリア（num）ごとにINSERT or UPDATEを実行
                    sql = "INSERT INTO result (pid, class, kid, zt) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE zt=%s"
                    cursor.execute(sql, (pid, class_name, num, zt, zt))
            conn.commit()
        
        # グレード判定ロジック
        if class_name in ["F1", "O1"]: grade = 1
        elif class_name in ["F2", "O2"]: grade = 2
        elif class_name in ["F3", "O3"]: grade = 3
        elif class_name in ["F4", "O4M", "O4W"]: grade = 4
        elif class_name in ["F5M", "F5W", "O5M", "O5W"]: grade = 5
        elif class_name in ["F6M", "F6W", "O6M", "O6W"]: grade = 6
        else: return "Invalid class", 400

        return redirect(url_for('registration_choice', grade=grade, area=area))
    
@app.route('/realtimeresult/<class_name>')
def realtimeresult(class_name):
    with db_connection() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM result WHERE class=%s"
            cursor.execute(sql, (class_name,))
            results = cursor.fetchall()
    print(results)

    with db_connection() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM player WHERE class=%s"
            cursor.execute(sql, (class_name,))
            players= cursor.fetchall()
    print(players)

    temp_point_list = []
    for n in range(1, 19):     
        count = sum(1 for row in results if str(row.get('kid')) == str(n) and row.get('zt') == 2)
        point = round(BASE_POINT / count, 2) if count > 0 else BASE_POINT
        temp_point_list.append(point)

    pid_list = list(set(row['pid'] for row in results if 'pid' in row))
    print(pid_list)

    for pid in pid_list:
        player_results = [row for row in results if row.get('pid') == pid]
        print(player_results)
        player_point = 0
        for player_result in player_results:
            kid = player_result.get('kid')
            zt = player_result.get('zt')
            if kid is not None and zt == 2:
                player_point += temp_point_list[int(kid) - 1]
            elif kid is not None and zt == 1:
                player_point += 1

        for p in players:
            if p.get('pid') == pid:
                p['point'] = player_point  # 新しいキー 'point' として値を代入
                break  # 見つかったらこれ以上この内側ループを回す必要はないので抜ける  

    players.sort(key=lambda x: x.get('point', 0), reverse=True)
    for i, player in enumerate(players):
        current_point = player.get('point', 0)
        
        if i > 0 and current_point == players[i-1].get('point', 0):
            # 直前のプレイヤーと同点なら、同じ順位にする
            player['rank'] = players[i-1]['rank']
        else:
            # 同点でないなら、現在の「順番（インデックス + 1）」を順位にする
            player['rank'] = i + 1
    
    print(players)
    print(temp_point_list)

    return render_template('testapp/realtimeresult.html', results=results, players=players, temp_point_list=temp_point_list, class_name=class_name)