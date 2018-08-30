import json
import sys
import requests
from collections import defaultdict
import operator
import re

if __name__=="__main__":

    hostname = 'https://api.github.com'
    try:
        username = sys.argv[0]
        password = sys.argv[1]
    except: #user has not specified their github username
        print("Usage: python GitTopFive.py <username> <password>")
        quit()

    while True:
        org = input("Enter the organization you wish to query or q to quit.\n")
        if org == 'q':
            quit()
        rep = requests.get("https://api.github.com/orgs/%s/repos?access_token=65cb1fe8fb137f76629950ba8a692303bfb3b84e&per_page=100" % (org)).json() #get all repos by organization
        print(rep)

        topFive=[]
        for project in rep:
            name = project["name"]
            owner = project["owner"]["login"]
            url = "https://api.github.com/repos/%s/%s/pulls?state=all&access_token=65cb1fe8fb137f76629950ba8a692303bfb3b84e&per_page=100" % (owner, name)
            num = 0

            r = requests.get(url)
            try:
                url = r.links["last"]["url"]
                p = re.compile('&page=\d+')
                inter = p.search(url).group()
                np = re.compile('\d+')
                pages = int(np.search(inter).group())
                r = requests.get(url)
                pulls = r.json()
                num = (pages-1)*100+len(pulls)
            except KeyError: #only one page
                pulls = r.json()
                num = len(pulls)


            if len(topFive) < 5:
                topFive.append((name, num))
                if len(topFive) == 5:
                    topFive.sort(key=operator.itemgetter(1), reverse=True)
                continue
            if num <= topFive[-1][1]:
                continue
            for x, item in enumerate(topFive):
                if num > item[1]:
                    topFive.insert(x, (name, num))
                    topFive.pop(-1)
                    break
        print("Top 5 projects for %s :\n" % org)
        for x, proj in enumerate(topFive):
            print("%s: %d pull request(s)\n" % (proj[0], proj[1]))













