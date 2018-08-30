import sys
import requests
import operator
import re
from tqdm import tqdm
import time

if __name__ == "__main__":

    try:
        token = sys.argv[1]
    except IndexError: # user has not specified their token
        print("Usage: python GitTopFive.py <token>")
        quit()

    while True:
        org = input("Enter the organization you wish to query or q to quit.\n")
        if org == 'q':
            quit()
        rrep = requests.get("https://api.github.com/orgs/%s/repos?access_token=%s&per_page=100" % (org, token)) #get all repos by organization
        if rrep.status_code == 443:
            print("Rate limit exceeded. Please make sure your token is valid. Otherwise, try again in an hour.")
            quit()
        if rrep.status_code == 404:
            print("%s is not a valid organization."%org)
            continue
        if rrep.status_code == 401:
            print("Your OAuth token is incorrect. Please refer to Readme.txt for instructions on how to generate a token.")
            quit()
        rep = rrep.json()
        while True:  # handles pagination of results
            try:
                u = rrep.links["next"]["url"]
                rrep = requests.get(u)
                if rrep.status_code == 443:
                    print("Rate limit exceeded. Please make sure your token is valid. Otherwise, try again in an hour.")
                    quit()
                rep += rrep.json()
            except KeyError:
                break

        topFive = []
        for project in tqdm(rep):  # iterate through each project and count the pull requests
            name = project["name"]
            url = "https://api.github.com/repos/%s/%s/pulls?state=all&access_token=%s&per_page=100" % (org, name, token)
            num = 0

            r = requests.get(url)
            if r.status_code == 443:
                print("Rate limit exceeded. Please make sure your token is valid. Otherwise, try again in an hour.")
                quit()
            try:
                url = r.links["last"]["url"]
                p = re.compile('&page=\d+')
                inter = p.search(url).group()
                np = re.compile('\d+')
                pages = int(np.search(inter).group())
                r = requests.get(url)
                if r.status_code == 443:
                    print("Rate limit exceeded. Please make sure your token is valid. Otherwise, try again in an hour.")
                    quit()
                pulls = r.json()
                num = (pages-1)*100+len(pulls)
            except KeyError: # only one page of results
                pulls = r.json()
                num = len(pulls)

            if len(topFive) < 5:
                topFive.append((name, num))
                if len(topFive) == 5:
                    topFive.sort(key=operator.itemgetter(1), reverse=True)
                continue
            if num <= topFive[-1][1]: # if it's smaller than the smallest item we can discard
                continue
            for x, item in enumerate(topFive):
                if num > item[1]:
                    topFive.insert(x, (name, num))
                    topFive.pop(-1)
                    break
        time.sleep(.1) #the progress bar interferes with our results if we try to print them too fast
        print("Top 5 projects for %s :\n" % org)
        for x, proj in enumerate(topFive):
            print("%s: %d pull request(s)\n" % (proj[0], proj[1]))
