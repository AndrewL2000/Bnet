from asyncio.windows_events import NULL
from riotwatcher import LolWatcher
import json
from time import strftime, gmtime
import requests
from datetime import datetime

riotAPIKey = 'RGAPI-3e2257cd-ed8b-48eb-b573-b1b5e4ddc439'

watcher = LolWatcher(riotAPIKey)  # Generate Instance of the watcher

region = 'oc1'

summonerNameList = ['XxlAndrewlxX','Richie Kim','Jiyoon','Horgexu', 'Musicality', 'gammasensei', 'JudgeBeast','Naidah','Hayden Tieng Sii']
summonerDict = {}
for summoner in summonerNameList:
    summonerDict[summoner] = {'name': summoner, 'ingame': False, 'puuid': '0', 'gameId': '0', 'summonerId': '0'}
activeGameIDs = []
gameIdDict = {}

# Get a json file of all the champions
url = 'https://ddragon.leagueoflegends.com/cdn/12.10.1/data/en_US/champion.json'
response = requests.get(url).json()
response = json.dumps(response)
champions_dict = json.loads(response)['data']

def stats(summonerName):
    summoner = watcher.summoner.by_name(region, summonerName)
    stats = watcher.league.by_summoner(region, summoner['id'])
    solo_stats = []
    
    for stat in stats:
        if stat['queueType'] == "RANKED_SOLO_5x5":
            solo_stats = stat
            break
    
    if solo_stats:
        tier = solo_stats['tier']
        rank = solo_stats['rank']
        solo_rank = f'{tier} {rank}'

        wins = int(solo_stats['wins'])
        losses = int(solo_stats['losses'])

        winrate = round(wins/(wins + losses)*100)
        return solo_rank, winrate, wins+losses

    else:   # No solo/duo stats
        return "UNRANKED", "N/A", 0

def champMastery(summonerID, champID):
    try:
        champ_mastery_stats = watcher.champion_mastery.by_summoner_by_champion(region, summonerID, champID)
        champ_mastery = champ_mastery_stats['championPoints']
        return champ_mastery
    except:
        return 0

def getMatchResult(puuid):
    try:
        matchList = watcher.match.matchlist_by_puuid(region, puuid, count=1)
        matchID = matchList[0]

        match = watcher.match.by_id(region, matchID)

        for participant in match['info']['participants']:
            if participant['puuid'] == puuid:
                result = participant['win']
                return result
    except:
        print("Match does not exist")
        return NULL
    
def checkGameFinished(msgId, summonerName):
    if gameIdDict[msgId]['gameFinish'] == False:
        try:
            currentGameInfo = watcher.spectator.by_summoner(region, summonerDict[summonerName]['summonerId'])
            return False
        except:
            if summonerName == gameIdDict[msgId]['name']:
                result = getMatchResult(gameIdDict[msgId]['puuid'])
                gameIdDict[msgId].update({'gameResult': result, 'gameFinish': True})
            summonerDict[summonerName].update({'ingame': False})
            return True



def currentGame(summonerName):
    try:    
        summoner = watcher.summoner.by_name(region, summonerName)
        summonerDict[summonerName].update({'puuid': summoner['puuid']})
        currentGameInfo = watcher.spectator.by_summoner(region, summoner['id'])
        tempDict = {}       
        participants = {}
        if currentGameInfo['gameQueueConfigId']:
        #if currentGameInfo['gameQueueConfigId'] == 420 or currentGameInfo['gameQueueConfigId'] == 440:  # Solo/Duo or Flex
            summonerDict[summonerName].update({'ingame': True, 'gameId': currentGameInfo['gameId'], 'summonerId': summoner['id']})
            for participant in currentGameInfo['participants']:
                name = participant['summonerName']
                rank, winrate, gamesPlayed = stats(name)
                champId = participant['championId']
                for champ in champions_dict:
                    champKey = int(champions_dict[champ]['key'])
                    if champId == champKey:
                        champName = champions_dict[champ]['id']
                        break
                champ_mastery = champMastery(participant['summonerId'], champId)
                participants[name] = {'name': name, 'rank': rank, 'winrate': winrate, 'champ': champName, 'team': participant['teamId'], 'masteryPoints': champ_mastery, 'gamesPlayed': gamesPlayed}
            tempDict = {'msgId':'0', 'gameId':currentGameInfo['gameId'], 'startTime':datetime.now(), 'gameFinish':False, 'gameType':('Ranked Solo/Duo' if currentGameInfo['gameQueueConfigId'] == 420 else 'Ranked Flex 5v5'), 'participants':participants, 'timeFinishEpoch':None, 'gameResult':None, 'puuid':summoner['puuid'], 'summonerId':summoner['id'], 'name':summonerName, 'embed':None}
            print(f"{summonerName} is currently in game")
            return tempDict
    except:
        print(f"{summonerName} is currently not in a League of Legends game")
        return []



