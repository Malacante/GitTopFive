import sys
import requests
import operator
import re

from flask import Flask
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app)


class Organization(Resource):

    def get(self, org):
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=str)
        token= parser.parse_args()['token']
        rrep = requests.get("https://api.github.com/orgs/%s/repos?access_token=%s&per_page=100" % (org, token)) #get all repos by organization
        if rrep.status_code == 443:
            return {"message": "Rate limit exceeded. Please try again in an hour."}, 443
        if rrep.status_code == 404:
            return {"message": "%s is not a valid organization." % org}, 404

        if rrep.status_code == 401:
            return {"message": "Your OAuth token is incorrect. Make sure to include the 'token' field in your request."}, 401
        rep = rrep.json()
        while True:  # handles pagination of results
            try:
                u = rrep.links["next"]["url"]
                rrep = requests.get(u)
                if rrep.status_code == 443:
                    return {"message": "Rate limit exceeded. Please try again in an hour."}, 443
                rep += rrep.json()
            except KeyError:
                break

        topFive = []
        for project in rep:  # iterate through each project and count the pull requests
            name = project["name"]
            url = "https://api.github.com/repos/%s/%s/pulls?state=all&access_token=%s&per_page=100" % (org, name, token)
            num = 0

            r = requests.get(url)
            if r.status_code == 443:
                return {"message": "Rate limit exceeded. Please try again in an hour."}, 443
            try:
                # extract number of last page and navigate to it
                url = r.links["last"]["url"]
                p = re.compile('&page=\d+')
                inter = p.search(url).group()
                np = re.compile('\d+')
                pages = int(np.search(inter).group())
                r = requests.get(url)
                if r.status_code == 443:
                    return {"message": "Rate limit exceeded. Please try again in an hour."}, 443
                pulls = r.json()
                num = (pages-1)*100+len(pulls)
            except KeyError:  # only one page of results
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
        if len(topFive) < 5:  # make sure orgs with 2-4 repositories are sorted
            topFive.sort(key=operator.itemgetter(1), reverse=True)
        rdict = {"organization": org, "repositories": {}}
        for x, proj in enumerate(topFive):
            rdict["repositories"][proj[0]] = proj[1]

        return rdict, 200

api.add_resource(Organization, "/org/<string:org>")

app.run(debug=True)
