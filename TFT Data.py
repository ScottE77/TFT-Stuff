import requests
from collections import Counter
import json
import math
import time
import pyodbc
import pandas as pd



f = open('matches.txt','r')
matches = f.read()
f.close()
matches = 'matches = '+matches 
exec(matches) #matches.txt format = [matchdata,morematchdata,etc]

f = open('players.txt','r')
file = f.read()
f.close()
players = 'players = '+file
exec(players)
DKey = ''# you need to update this key every 24 hours from https://developer.riotgames.com/

def RequestSummonerData(region,IGN):
    for i in range(len(players)):
        if players[i]['name'].lower().replace(' ','') == IGN.lower().replace(' ','') and players[i]['region'].lower() == region.lower():
            return players[i]
    URL = "https://" + region + ".api.riotgames.com/tft/summoner/v1/summoners/by-name/" + IGN + "?api_key=" + DKey
    response = requests.get(URL)
    response = response.json()
    response['region'] = region
    if 'status' in response:
        raise ValueError('an error has occured')
    players.append(response)
    f = open('players.txt','w')
    f.write(str(players))
    f.close()
    return response


def RequestRankedData(region,ID):
    URL = "https://" + region + ".api.riotgames.com/tft/league/v1/entries/by-summoner/" + ID + "?api_key=" + DKey
    response = requests.get(URL)
    return response.json()

def RequestSummonerDatafrompuuid(region,puuid):
    for i in range(len(players)):
        if players[i]['puuid'] == puuid and players[i]['region'].lower() == region.lower():
            return players[i]
    URL = "https://" + region + ".api.riotgames.com/tft/summoner/v1/summoners/by-puuid/" + puuid + "?api_key=" + DKey
    response = requests.get(URL)
    response = response.json()
    response['region'] = region
    players.append(response)
    f = open('players.txt','w')
    f.write(str(players))
    f.close()
    return response


def RequestingRank(region,IGN):
    region = region.upper()
    if region == 'NA':
        region = 'na1'
    elif region == 'EU':
        region = 'euw1'
    ID = RequestSummonerData(region,IGN)['id']
    RankedData = RequestRankedData(region,ID)[0]
    Rank = RankedData['tier']+ ' ' + RankedData['rank'] + ' ' + str(RankedData['leaguePoints'])+'lp'
    return Rank

def last20games(region,puuid,count=20):
    if region == 'na1':
        region1 = 'americas'
    elif region == 'euw1':
        region1 = 'europe'
    URL = "https://" + region1 + ".api.riotgames.com/tft/match/v1/matches/by-puuid/" + puuid + "/ids?start=0&count=" + str(count) + "&api_key=" + DKey
    response = requests.get(URL)
    return response.json()

def matchdata(region,matchid):
    for i in range(len(matches)):
        if matches[i]['metadata']['match_id'] == matchid:
            return matches[i]
    if region == 'na1':
        region = 'americas'
    elif region == 'euw1':
        region = 'europe'
    URL = "https://"+region+".api.riotgames.com/tft/match/v1/matches/"+matchid+"?api_key="+DKey
    response = requests.get(URL)
    response = response.json()
    if matches == {'status': {'message': 'Data not found - match file not found', 'status_code': 404}}:
        ValueError('match file not found')
    else:
        matches.append(response)
    f = open('matches.txt','w')
    f.write(str(matches))
    f.close()
    return response

def whointhegame(region,matchid):
    if region == 'na1':
        region1 = 'americas'
    elif region == 'euw1':
        region1 = 'europe'
    match = matchdata(region1,matchid)
    participants = match['metadata']['participants']
    summonernames = []
    for i in range(len(participants)):
        summonernames.append(RequestSummonerDatafrompuuid(region,participants[i])['name'])
    return summonernames

def damagedone(region,matchid,puuida,puuidb):
    if region == 'na1':
        region1 = 'americas'
    elif region == 'euw1':
        region1 = 'europe'
    match = matchdata(region1,matchid)
    participants = match['metadata']['participants']
    for i in range(8):
        if puuida == participants[i]:
            a = i
        elif puuidb == participants[i]:
            b = i
    aDamage = match['info']['participants'][a]['total_damage_to_players']
    bDamage = match['info']['participants'][b]['total_damage_to_players']
    return [aDamage,bDamage]

def comparematches(region,puuida,puuidb,count=20):
    aMatches = last20games(region,puuida)
    bMatches = last20games(region,puuidb)
    bothMatches = list(set(aMatches) & set(bMatches))
    return bothMatches


def whodidmoredmg(region,puuida,puuidb,count=20):
    start = time.time()
    matches = comparematches(region,puuida,puuidb,count)
    alldamage = []
    if len(matches)==0:
        return[0,0,0]
    for i in range(len(matches)):
        alldamage.append(damagedone(region,matches[i],puuida,puuidb))
    alladmg = []
    allbdmg = []
    for i in range(len(alldamage)):
        alladmg.append(alldamage[i][0])
        allbdmg.append(alldamage[i][1])
    aaverage = sum(alladmg)/len(alladmg)
    baverage = sum(allbdmg)/len(allbdmg)
    end = time.time()
    print(end-start)
    return [aaverage,baverage,len(alldamage)]
        
def whocarriedthelobby(region,matchid):
    start = time.time()
    match = matchdata(region,matchid)
    damagedone = []
    actualposition = []
    puuidorder = []
    summonernames = []
    orderofpositions = []
    knockedout = []
    for i in range(8):
        damagedone.append(match['info']['participants'][i]['total_damage_to_players'])
        actualposition.append(match['info']['participants'][i]['placement'])
        puuidorder.append(match['metadata']['participants'][i])
        knockedout.append(match['info']['participants'][i]['players_eliminated'])
    for i in range(8):
        summonernames.append(RequestSummonerDatafrompuuid(region,puuidorder[i])['name'])
        orderofpositions.append(actualposition.index(i+1))
    print(summonernames[orderofpositions[0]]+' finished 1 and did ' + str(damagedone[orderofpositions[0]]) + ' damage and knocked out '+str(knockedout[orderofpositions[0]])+' players')
    print(str(summonernames[damagedone.index(max(damagedone))])+ ' did the most damage at '+str(max(damagedone))+', knocked out '+str(knockedout[damagedone.index(max(damagedone))])+' players and finished ' +str(actualposition[damagedone.index(max(damagedone))]))
    end = time.time()
    print(end-start)
    return [damagedone,actualposition,summonernames,orderofpositions]

def GameStats(region,puuid,matchid):
    matchinfo = matchdata(region,matchid)
    position = 9
    for i in range(8):
        if puuid == matchinfo['metadata']['participants'][i]:
            position = i
    if position == 9:
        raise ValueError('puuid of this player didnt play in this match')
    userdata = matchinfo['info']['participants'][position]
    return userdata

def Last50GameData(region,puuid,count=50):
    start = time.time()
    matches = last20games(region,puuid,count)
    data = []
    for i in range(len(matches)):
        data.append(GameStats(region,puuid,matches[i]))
    for i in range(len(data)):
        position = []
        for j in range(len(data[i]['traits'])):
            data[i]['traits'][j] = [data[i]['traits'][j]['name'],data[i]['traits'][j]['tier_current']]
            if data[i]['traits'][j][1] == 0:
                position.append(j)
        for j in range(len(data[i]['units'])):
            data[i]['units'][j] = data[i]['units'][j]['character_id']
        del data[i]['companion']
        del data[i]['puuid']
        del data[i]['time_eliminated']
        for j in range(len(position)):
            del data[i]['traits'][position[-(j+1)]]
    augments = []
    units = []
    traits = []
    for i in range(len(matches)):
        augments += [data[i]['augments']]
        units += [data[i]['units']]
        traits += [data[i]['traits']]
    end = time.time()
    print(end-start)
    return data

def WhatImDoingWrong(region,puuid,count=50):
    start = time.time()
    data = Last50GameData(region,puuid,count)
    alldata = {'augments': [], 'gold_left': [],'last_round': [],'level': [],'placement': [],'players_eliminated': [],'total_damage_to_players': [],'traits': [],'units': []}
    for i in range(len(data)):
        alldata['augments'] += data[i]['augments']
        alldata['gold_left'].append(data[i]['gold_left'])
        alldata['last_round'].append(data[i]['last_round'])
        alldata['level'].append(data[i]['level'])
        alldata['placement'].append(data[i]['placement'])
        alldata['players_eliminated'].append(data[i]['players_eliminated'])
        alldata['total_damage_to_players'].append(data[i]['total_damage_to_players'])
        alldata['traits'] += data[i]['traits']
        alldata['units'] += data[i]['units']
    avedata = {'augments':Counter(alldata['augments']), 'gold_left':sum(alldata['gold_left'])/count,'last_round':sum(alldata['last_round'])/count,
               'level':sum(alldata['level'])/count,'placement':sum(alldata['placement'])/count,'total_damage_to_players':sum(alldata['total_damage_to_players'])/count,
               'units':Counter(alldata['units'])}#traits aren't done yet, Counter function doesn't work with lists.
    end = time.time()
    print(end-start)
    return [alldata,avedata]
    

f = open('matches.txt','w')
f.write(str(matches))
f.close()

f = open('players.txt','w')
f.write(str(players))
f.close()