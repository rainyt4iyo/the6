from itertools import count
from os import name

from flask import render_template, request, redirect, url_for
from testapp import app
import pymysql
import time
import logging
from contextlib import contextmanager
import re
import json
import time
from flask import Response, stream_with_context

BASE_POINT = 50
NUMBER_OF_KADAI = 18

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

def player_information_final(pid, class_name):
    with db_connection() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM finalplayer WHERE pid=%s AND class=%s"
            cursor.execute(sql, (pid, class_name))
            player = cursor.fetchone()
    return player

def number2area(num):
    area_map = {
        1: "A1",  2: "A2",
        3: "B1",  4: "B2",
        5: "C1",  6: "C2",
        7: "D1",  8: "D2",
        9: "E1", 10: "E2",
       11: "F1", 12: "F2",
       13: "G1", 14: "G2",
       15: "H1", 16: "H2",
       17: "I1", 18: "I2",
    }
    return area_map.get(num, None)

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
    
    elif area == "fff":
        return (1, 2, 3, 4)
    
    else:
        return None
    
def class2japanese(class_name):
    if "F" in class_name:
        prefix = "FUN"
    elif "O" in class_name:
        prefix = "OPEN"
    if "M" in class_name:   
        suffix = "男子"
    elif "W" in class_name:
        suffix = "女子"
    else:
        suffix = ""
    grade = re.sub(r'\D', '', class_name)

    return f"{prefix}{grade}年生{suffix}"

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

@app.route('/result_check/<class_name>')
def result_check(class_name): 
    with db_connection() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM player WHERE class=%s"
            cursor.execute(sql, (class_name,))
            players = cursor.fetchall()
    print(players)

    with db_connection() as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM result WHERE class=%s"
            cursor.execute(sql, (class_name,))
            results = cursor.fetchall()

    res_list = []
    for p in players:
        p_list = []
        for r in results:
            if p['pid'] == r['pid'] and r['zt'] != 0:
                p_list.append((r["kid"], r["zt"]))
        res_list.append(p_list)

    results = []
    for i in res_list:
        result = []
        for j in range(0, NUMBER_OF_KADAI):
            if not any(int(kid) == j+1 for kid, zt in i):
                result.append((0))
            else:
                for index, (kid, zt) in enumerate(i):
                    if int(kid) == j+1:
                        if zt == 1:
                            result.append(("Z"))
                        elif zt == 2:
                            result.append(("T"))
        results.append(result)

    print(results)

    return render_template('testapp/result_check.html', results=results, class_name=class_name, players=players)

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
    
    #print(player_list)

    grade_list_japanese = []
    for i in grade_list:
        i = class2japanese(i)
        grade_list_japanese.append(i)
    
    grade_list = grade_list_japanese
    
    return render_template('testapp/choice.html', grade=grade, player_list=player_list, grade_list=grade_list, area=area)

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
        player_point = 0
        top_list = []    # ← ループの外に移動
        zone_list = []   # ← ループの外に移動

        for player_result in player_results:
            kid = player_result.get('kid')
            zt = player_result.get('zt')
            if kid is not None and zt == 2:
                player_point += temp_point_list[int(kid) - 1]
                player_point += 1
                top_list.append(int(kid))
            elif kid is not None and zt == 1:
                player_point += 1
                zone_list.append(int(kid))

        player_detail = {'top': top_list, 'zone': zone_list}  # ← 変わらずループ外でOK

        for p in players:
            if p.get('pid') == pid:
                p['point'] = round(player_point, 2)
                p['detail'] = player_detail
                break
        
        for p in players:
            if 'detail' not in p:
                p['detail'] = {'top': [], 'zone': []}
            if 'point' not in p:
                p['point'] = 0


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

    tag = ["A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2", "E1", "E2", "F1", "F2", "G1", "G2", "H1", "H2", "I1", "I2"]

    return render_template('testapp/realtimeresult.html', results=results, players=players, temp_point_list=temp_point_list, class_name=class_name, tag=tag)


# ★ SSE用の新しいエンドポイントを追加
@app.route('/realtimeresult/<class_name>/stream')
def realtimeresult_stream(class_name):
    def get_data():
        """DBからデータを取得してプレイヤーリストを返す"""
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM result WHERE class=%s", (class_name,))
                results = cursor.fetchall()

        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM player WHERE class=%s", (class_name,))
                players = cursor.fetchall()

        temp_point_list = []
        for n in range(1, 19):
            count = sum(1 for row in results if str(row.get('kid')) == str(n) and row.get('zt') == 2)
            point = round(BASE_POINT / count, 2) if count > 0 else BASE_POINT
            temp_point_list.append(point)

        pid_list = list(set(row['pid'] for row in results if 'pid' in row))

        for pid in pid_list:
            player_results = [row for row in results if row.get('pid') == pid]
            player_point = 0
            top_list = []   # ★ ループ外に移動
            zone_list = []  # ★ ループ外に移動

            for player_result in player_results:
                kid = player_result.get('kid')
                zt = player_result.get('zt')
                if kid is not None and zt == 2:
                    player_point += temp_point_list[int(kid) - 1]
                    player_point += 1
                    top_list.append(int(kid))   # ★ 追加
                elif kid is not None and zt == 1:
                    player_point += 1
                    zone_list.append(int(kid))  # ★ 追加

            player_detail = {'top': top_list, 'zone': zone_list}  # ★ 追加

            for p in players:
                if p.get('pid') == pid:
                    p['point'] = round(player_point, 2)  # ★ round追加
                    p['detail'] = player_detail           # ★ 追加
                    break

        # ★ ポイント未計算プレイヤーへのデフォルト値設定
        for p in players:
            if 'detail' not in p:
                p['detail'] = {'top': [], 'zone': []}
            if 'point' not in p:
                p['point'] = 0

        players.sort(key=lambda x: x.get('point', 0), reverse=True)
        for i, player in enumerate(players):
            current_point = player.get('point', 0)
            if i > 0 and current_point == players[i-1].get('point', 0):
                player['rank'] = players[i-1]['rank']
            else:
                player['rank'] = i + 1

        return players, temp_point_list


    def event_stream():
        last_data = None
        while True:
            try:
                players, temp_point_list = get_data()
                # シリアライズして前回と比較（変化があった時だけ送信）
                current_data = json.dumps(players, ensure_ascii=False, default=str)
                if current_data != last_data:
                    last_data = current_data
                    payload = json.dumps({
                        'players': players,
                        'temp_point_list': temp_point_list
                    }, ensure_ascii=False, default=str)
                    yield f"data: {payload}\n\n"
            except Exception as e:
                print(f"SSE error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            time.sleep(3)  # ★ 3秒ごとにDBを確認

    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'  # Nginxを使う場合に必要
        }
    )

'''
@app.route('/monitor/<grade>')
def monitor(grade):

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
'''


def calc_players(results, players_raw):
    """resultsとplayers_rawからポイント計算済みのplayersリストを返す共通関数"""
    temp_point_list = []
    for n in range(1, 19):
        count = sum(1 for row in results if str(row.get('kid')) == str(n) and row.get('zt') == 2)
        point = round(BASE_POINT / count, 2) if count > 0 else BASE_POINT
        temp_point_list.append(point)

    players = list(players_raw)  # コピー

    pid_list = list(set(row['pid'] for row in results if 'pid' in row))

    for pid in pid_list:
        player_results = [row for row in results if row.get('pid') == pid]
        player_point = 0
        top_list = []
        zone_list = []

        for player_result in player_results:
            kid = player_result.get('kid')
            zt = player_result.get('zt')
            if kid is not None and zt == 2:
                player_point += temp_point_list[int(kid) - 1]
                player_point += 1
                top_list.append(int(kid))
            elif kid is not None and zt == 1:
                player_point += 1
                zone_list.append(int(kid))

        player_detail = {'top': top_list, 'zone': zone_list}

        for p in players:
            if p.get('pid') == pid:
                p['point'] = round(player_point, 2)
                p['detail'] = player_detail
                break

    for p in players:
        if 'detail' not in p:
            p['detail'] = {'top': [], 'zone': []}
        if 'point' not in p:
            p['point'] = 0

    players.sort(key=lambda x: x.get('point', 0), reverse=True)
    for i, player in enumerate(players):
        current_point = player.get('point', 0)
        if i > 0 and current_point == players[i-1].get('point', 0):
            player['rank'] = players[i-1]['rank']
        else:
            player['rank'] = i + 1

    return players, temp_point_list


@app.route('/monitor/<grade>')
def monitor(grade):
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

    classes_data = []
    for class_name in grade_list:
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM result WHERE class=%s", (class_name,))
                results = cursor.fetchall()

        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM player WHERE class=%s", (class_name,))
                players_raw = cursor.fetchall()

        players, temp_point_list = calc_players(results, players_raw)

        classes_data.append({
            'class_name': class2japanese(class_name),
            'players': players,
            'temp_point_list': temp_point_list,
        })

    return render_template(
        'testapp/monitor.html',
        grade=grade,
        grade_list=grade_list,
        classes_data=classes_data,
    )


# SSEエンドポイント（monitor用）
@app.route('/monitor/<grade>/stream')
def monitor_stream(grade):
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

    def get_data():
        classes_data = []
        for class_name in grade_list:
            with db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM result WHERE class=%s", (class_name,))
                    results = cursor.fetchall()

            with db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM player WHERE class=%s", (class_name,))
                    players_raw = cursor.fetchall()

            players, temp_point_list = calc_players(results, players_raw)

            classes_data.append({
                'class_name': class2japanese(class_name),
                'players': players,
                'temp_point_list': temp_point_list,
            })
        return classes_data

    def event_stream():
        while True:
            try:
                classes_data = get_data()
                payload = json.dumps(classes_data, ensure_ascii=False, default=str)
                yield f"data: {payload}\n\n"  # ★ 変化チェックを削除 → 毎回必ず送信
            except Exception as e:
                print(f"SSE monitor error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            time.sleep(3)

    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )