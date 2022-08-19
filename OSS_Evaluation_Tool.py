#!/usr/bin/env python
# coding: utf-8

# In[8]:


import requests
import re
import time
import numpy as np
from bs4 import BeautifulSoup 
from sklearn import preprocessing

myToken = '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'
client_id='83352693b87485370e8a'
client_secret='f6cc77a83ca7303342bc5716427aacfd92c319be'
oneMonth = 2592000
update=1.5
push = 1.5
watcher = 0.6
star = 0.8
fork = 0.6
open_issue = 0.4
subscriber = 0.6
has_wiki = 1.0
read = 1.8
description = 0.4 
contributing = 0.2
license = 0.2
code_conduct = 0.2 
pull_req = 0.2
issue = 0.2
default_weight = np.array([update,push,watcher,star,fork,
                       open_issue,subscriber,has_wiki,
                       read,description,contributing,
                       license,code_conduct,pull_req,issue])

def getGitURL(keyword,sortway):
    url = 'https://api.github.com/search/repositories?q={keyword}&s={sortway}&type=Repositories'.format(keyword=keyword,sortway=sortway)

    return url

# Returns the responses obtained according to 4 different sorts
def getKeywordResponses(keyword):
    url = getGitURL(keyword,"stars")
    r_stars = requests.get(url,auth = (client_id, client_secret))
    
    url = getGitURL(keyword,"")
    r_bestMatch = requests.get(url,auth = (client_id, client_secret))
    
    url = getGitURL(keyword,"forks")
    r_forks = requests.get(url,auth = (client_id, client_secret))
    
    url = getGitURL(keyword,"updated")
    r_updated= requests.get(url,auth = (client_id, client_secret))

    
    return [r_stars,r_bestMatch,r_forks,r_updated]


def getURLgroup(responses):
    dict1 = dict()
    for res in responses:
        res_dict = res.json()
        if 'items' in res_dict.keys():
            r_dicts = res_dict['items']
            # Here the URLs obtained by traversing each search sort are stored in a dictionary,
            # the key of which is the URL and the value is the number of occurrences.
            for i in r_dicts:
                dict1.update([(i['html_url'], dict1[i['html_url']] + 1)]) if i['html_url'] in dict1 else dict1.update([(i['html_url'], 1)])
    return dict1
        
    
def getRepositoryInfomation(r):
    response_dict = r.json()
    print(response_dict.keys())
    print("Toal:", response_dict['total_count'])
    repo_dicts = response_dict['items']
    print("Repositories number:", len(repo_dicts))
    for repo_dict in repo_dicts:
        print('Name:', repo_dict['name'])
        print('Owner:', repo_dict['owner']['login'])
        print('Stars:', repo_dict['stargazers_count'])
        print('URL:', repo_dict['html_url'])
        print('Created_At:', repo_dict['created_at'])
        print('Updated_At:', repo_dict['updated_at'])
        print('Description:', repo_dict['description'])


def githubAPIadaptor(rawURL):
    index = rawURL.find(r'github') # Find 'api' index
    index2 = rawURL.find(r'github.com/')+len(r'github.com/')
    return rawURL[:index] + 'api.' + rawURL[index:index2]+r'repos/'+rawURL[index2:]

def timestampToSec(date):
    # Transfer Date to Timestamp
    t = time.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    return time.mktime(t)

def MaxMinNormalization(x):
    min_max_scaler = preprocessing.MinMaxScaler()
    x = min_max_scaler.fit_transform(x)
    return x

def checkDocument(base):
    my_dict = {}
    # Document Keywords
    checkList = ["READ","CONTRIBUTING","LICENSE","CODE","REQUEST","REMAINING"]
    for c in checkList:
        my_dict[c] = 0.0
    # Locate the Community page
    myURL = base + "/community"
    response = requests.get(myURL,auth = (client_id,client_secret))
    response.encoding = 'utf-8'
    mySoup = BeautifulSoup(response.text, 'html.parser')  #HTML File
    found = 0
    # Find all hyperlinked Tags
    for k in mySoup.find_all('a'):
        link = k.get('href')
        if link is not None and "README.md" in str(link):
            my_dict["READ"] = 1
            found += 1
        if link is not None and "CONTRIBUTING.md" in str(link):
            my_dict["CONTRIBUTING"] = 1
            found += 1
        if link is not None and "LICENSE" in str(link):
            my_dict["LICENSE"] = 1
            found += 1
        if link is not None and "CODE_OF_CONDUCT.md" in str(link):
            my_dict["CODE"] = 1
            found += 1
        if link is not None and "PULL_REQUEST_TEMPLATE" in str(link):
            my_dict["REQUEST"] = 1
            found += 1
            
    flag_list = ['octicon', 'octicon-check', 'mr-1', 'color-fg-success']
    total = 0.0
    for k in mySoup.find_all('svg',{"aria-label" : "Added"}):
        if k.get("class") == flag_list:
            total = total + 1
    
    my_dict["REMAINING"] = total - found
    return my_dict

def checkInput(user_input,keyword=True):
    user_input = user_input.strip().lower()
    if keyword:
        return True if re.match(r'^(?=.*[a-zA-Z])|(?=.*[0-9])', user_input) else False
    else:
        return True if user_input.startswith( r'https://github.com/') else False

def getDataOfSingleRepo(repo):
    apiURL = githubAPIadaptor(repo)
    r = requests.get(apiURL,auth = (client_id, client_secret))
    response_dict = r.json()
    update_sec = timestampToSec(response_dict['updated_at'])
    push_sec = timestampToSec(response_dict['pushed_at'])
    has_wiki = 1 if response_dict['has_wiki'] is True else 0
    checkList = checkDocument(repo)
    if checkList["REMAINING"] == 2:
        checkList["ISSUE"] = 1
    elif checkList["REMAINING"] == 1 and response_dict["description"] == None:
        checkList["ISSUE"] = 1
    elif checkList["REMAINING"] == 1 and response_dict["description"] != None:
        checkList["Description"] = 1

    row = np.array([update_sec,
                    push_sec,
                    response_dict['watchers_count'],
                    response_dict['stargazers_count'],
                    response_dict['forks'],
                    response_dict['open_issues'],
                    response_dict['subscribers_count'],
                    has_wiki,
                    checkList.get("READ",0.0),
                    checkList.get("Description",0.0),
                    checkList.get("CONTRIBUTING",0.0),
                    checkList.get("LICENSE",0.0),
                    checkList.get("CODE",0.0),
                    checkList.get("REQUEST",0.0),
                    checkList.get("ISSUE",0.0)
                   ])
    return row

def singleRepoDataProcess(repoData):
    res = repoData.copy()
    update_gap = time.time() - repoData[0]
    push_gap = time.time() - repoData[1]
    update_gap = 1 - ((update_gap/oneMonth)*0.1)
    push_gap = 1 - ((push_gap/oneMonth)*0.1)
    update_gap = '%.4f' % update_gap
    push_gap = '%.4f' % push_gap
    update_gap = update_gap if float(update_gap) > 0.0 else 0.0
    push_gap = push_gap if float(push_gap) > 0.0 else 0.0
    res[0] = update_gap
    res[1] = push_gap
    index = 2
    for d in repoData[2:7]:
        new_data = 0.1
        if d <= 100:
            new_data = d/200
        elif d >100 and d<=3100:
            new_data = 0.5+((d-100)/10000)
        elif d >3100 and d<=10000:
            new_data = 0.9
        else:
            new_data = 1
        res[index] = new_data
        index += 1
    return res

def searchByKeyword(myKey):
    res = getURLgroup(getKeywordResponses(myKey))
    arr = np.array([[1.1,2.2,3.3,4.4,5.5,6.6,7.7,8.8,9.9,10.1,11.2,12.3,23.1,3.3,4.4]])
    for k,v in res.items():
        row = getDataOfSingleRepo(k)
        row_n = arr.shape[0] ##last row
        arr = np.insert(arr,row_n,[row],axis= 0)
    arr = np.delete(arr,0,axis = 0)
    normed_data = MaxMinNormalization(arr)
    open_issue = 0.4 if arr[6].any() > 0.2 else 0.1
    normed_data*=np.array([update,push,watcher,star,fork,
                           open_issue,subscriber,has_wiki,
                           read,description,contributing,
                           license,code_conduct,pull_req,issue])
    sum_data = np.sum(normed_data,axis=1)
    higestScore = np.where(sum_data==np.max(sum_data))[0][0]
    print("Best project found by the input:",list(res.keys())[higestScore])
    generateReport(normed_data[higestScore])

def searchByURL(myURL):
    repoData = getDataOfSingleRepo(myURL)
    final_data = singleRepoDataProcess(repoData)*default_weight
    generateReport(final_data)

def generateReport(final_data):
    r_update_time = 10-int(final_data[0]*10)
    r_push_time = 10-int(final_data[1]*10)
    r_popularity = '%.4f' %sum(final_data[2:7])
    total_score = '%.4f' %sum(final_data)
    if r_update_time <= 1:
        print("This project has been updated recently")
    else:
        print("This project has been updated at least {update_time} month ago".format(update_time=r_update_time))
        
    if r_push_time <= 1:
        print("This project has been pushed recently")
    else:
        print("This project has been pushed at least {push_time} month ago".format(push_time=r_push_time))
        
    print("This popularity of this project is {popularity}/3".format(popularity=r_popularity))
    if final_data[7] > 0:
        print("This project contains wiki page")
    if final_data[8] > 0:
        print("This project contains README file")
    if final_data[9] > 0:
        print("This project contains Description")
    if final_data[10] > 0:
        print("This project contains Contributing")
    if final_data[11] > 0:
        print("This project contains License")
    if final_data[12] > 0:
        print("This project contains Code of Conduct")
    if final_data[13] > 0:
        print("This project contains Pull_Request_Template")
    if final_data[14] > 0:
        print("This project contains Issue_Template")
    print("Total Score for this project: {total}".format(total = total_score))
    if ((r_update_time<=6 or r_push_time<=6) and final_data[8] > 0 and float(r_popularity) >= 0.3 and float(total_score) >= 3.8) or (float(total_score) >= 8):
        print("This project looks worth downloading to try")
    else:
        print("This project does not look good, you need to reconsider whether to download it or not")

def start():
    use_keyword = True
    print("Do you want to use a keyword search or a specific repository address？ 1.Keyword 2.Repository address")
    while(True):
        ans_q1 = input()
        if ans_q1 != "1" and ans_q1 != "2":
            print("You must enter a legal parameter: 1 or 2")
        else:
            if ans_q1 is "2":
                use_keyword = False
            break

    if use_keyword:
        the_key = input("Please enter your keyword:")
        if checkInput(the_key,use_keyword):
            print("The report is being generated, please wait a few minutes")
            searchByKeyword(the_key)
        else:
            print("Illegal input")
    else:
        the_URL = input("Please enter the repository address:")
        if checkInput(the_URL,use_keyword):
            print("The report is being generated, please wait a few minutes")
            searchByURL(the_URL)
        else:
            print("Illegal input")   


def main():
    start()

if __name__ == "__main__":
    main()




