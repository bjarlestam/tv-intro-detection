import os
import json
import arrow
import signal

from time import sleep
from datetime import datetime, timezone
from requests.exceptions import HTTPError
from jellyfin_api_client import jellyfin_login, jellyfin_logout
from jellyfin_apiclient_python.exceptions import HTTPException

server_url = os.environ['JELLYFIN_URL'] if 'JELLYFIN_URL' in os.environ else ''
server_username = os.environ['JELLYFIN_USERNAME'] if 'JELLYFIN_USERNAME' in os.environ else ''
server_password = os.environ['JELLYFIN_PASSWORD'] if 'JELLYFIN_PASSWORD' in os.environ else ''

TICKS_PER_MS = 10000

preroll_seconds = 3
minimum_intro_length = 10 # seconds

client = None
should_exit = False

def monitor_sessions():
    if client == None:
        return False

    start = datetime.now(timezone.utc)
    try:
        sessions = client.jellyfin.sessions()
    except (HTTPError, HTTPException) as err:
        print("error communicating with the server")
        return False

    for session in sessions:
        if session['UserId'] != client.auth.jellyfin_user_id():
            continue
        if not 'PlayState' in session or session['PlayState']['CanSeek'] == False:
            continue
        if not 'Capabilities' in session or session['Capabilities']['SupportsMediaControl'] == False:
            continue
        if not 'LastPlaybackCheckIn' in session:
            continue
        if not 'NowPlayingItem' in session:
            continue

        sessionId = session['Id']

        #print('user id %s' % session['UserId'])
        print(session['DeviceName'])

        lastPlaybackTime = arrow.get(session['LastPlaybackCheckIn']).to('utc').datetime
        timeDiff = start - lastPlaybackTime

        item = session['NowPlayingItem']
        if not session['PlayState']['IsPaused'] and timeDiff.seconds < 5 and 'Id' in item:
            if 'SeriesName' in item and 'SeasonName' in item and 'ParentIndexNumber' in item and 'Name' in item:
                print('currently playing %s - %s - Episode %s [%s]' % (item['SeriesName'], item['SeasonName'], item['ParentIndexNumber'], item['Name']))
            print('item id %s' % item['Id'])
        else:
            print('not playing or hasn\'t checked in')
            continue

        if not 'SeriesId' in item or not 'SeasonId' in item:
            print('playing item isn\'t a series')
            continue

        position_ticks = int(session['PlayState']['PositionTicks'])
        print('current position %s minutes' % (((position_ticks / TICKS_PER_MS) / 1000) / 60))

        file_path = 'jellyfin_cache/' + str(item['SeriesId']) + '/' + str(item['SeasonId']) + '/' + str(item['Id']) + '.json'
        start_time_ticks = 0
        end_time_ticks = 0
        if os.path.exists(file_path):
            with open(file_path, "r") as json_file:
                dict = json.load(json_file)
                if 'start_time_ms' in dict and 'end_time_ms' in dict:
                    start_time_ticks = int(dict['start_time_ms']) * TICKS_PER_MS
                    end_time_ticks = int(dict['end_time_ms']) * TICKS_PER_MS
        else:
            print('couldn\'t find data for item')
            continue
        
        if start_time_ticks == 0 and end_time_ticks == 0:
            print('no useable intro data')
            continue

        if position_ticks < start_time_ticks or position_ticks > end_time_ticks:
            continue

        if end_time_ticks - start_time_ticks < minimum_intro_length * 1000 * TICKS_PER_MS:
            print('intro is less than %ss - skipping' % minimum_intro_length)
            continue

        preroll_ticks = preroll_seconds * 1000 * TICKS_PER_MS
        if end_time_ticks - preroll_ticks >= 0:
            end_time_ticks -= preroll_ticks

        print('trying to send seek to client')
        client.jellyfin.sessions(handler="/%s/Message" % sessionId, action="POST", json={
            "Text": "Skipping Intro",
            "TimeoutMs": 5000
        })

        sleep(1)
        params = {
            "SeekPositionTicks": end_time_ticks
        }
        client.jellyfin.sessions(handler="/%s/Playing/seek" % sessionId, action="POST", params=params)
        sleep(10)
    return True

def init_client():
    global client

    print('initializing client')
    if client != None:
        jellyfin_logout()
    sleep(1)
    client = jellyfin_login(server_url, server_username, server_password)
    

def monitor_loop():
    global should_exit

    if server_url == '' or server_username == '' or server_password == '':
        print('missing server info')
        return
    
    init_client()
    while not should_exit:
        if not monitor_sessions() and not should_exit:
            init_client()
        sleep(5)
    jellyfin_logout()


def receiveSignal(signalNumber, frame):
    global should_exit

    if signalNumber == signal.SIGINT:
        print('should exit')
        should_exit = True
    return

if __name__ == "__main__":
    signal.signal(signal.SIGINT, receiveSignal)
    monitor_loop()