# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import json
from os import listdir
from os.path import isfile, join
from pprint import pprint
import sys


def readJSONfile(filename):
    json_data = open(filename).read()
    data = json.loads(json_data)
    return data


def readJSONfiles(args):
    data = []
    for i in range(1, len(args)):
        directory = args[i]
        for filename in listdir(directory):
            pathFilename = join(directory, filename)
            if isfile(pathFilename):
                if pathFilename.endswith(".json"):
                    data.append(readJSONfile(pathFilename))
    return data


def getTypes(alldata):
    entityTypes = {}
    relationTypes = {}
    for data in alldata:
        datasection = parseJSONdata(data)
        for etypename in datasection.entityTypes:
            enttype = datasection.entityTypes[etypename]
            if etypename not in entityTypes:
                entityTypes[enttype] = 1
            else:
                entityTypes[enttype] += 1
        for rtypename in datasection.relationTypes:
            reltype = datasection.relationTypes[rtypename]
            if rtypename not in relationTypes:
                relationTypes[rtypename] = reltype
            else:
                relationTypes[rtypename].occurrences += reltype.occurrences
                for atype in reltype.arg1types:
                    relationTypes[rtypename].addarg1type(atype, reltype.arg1types[atype])
                for atype in reltype.arg2types:
                    relationTypes[rtypename].addarg2type(atype, reltype.arg2types[atype])
    return entityTypes, relationTypes


def parseJSONdata(data):
    sectionName = data["section"]
    source_db = data["source_db"]
    source_id = data["source_id"]
    newsection = section(sectionName, source_db, source_id)
    if "catanns" in data:
        for dataentity in data["catanns"]:
            etype = unun(dataentity["category"])
            eid = dataentity["id"]
            span = dataentity["span"]
            start = span["begin"]
            end = span["end"]
            newentity = entity(eid, start, end, etype)
            newsection.entities[eid] = newentity
            if etype not in newsection.entityTypes:
                newsection.entityTypes[etype] = etype
    if 'insanns' in data:
        for instance in data["insanns"]:
            tid = instance["id"]
            eid = instance["object"]
            newtrigger = eventTrigger(tid, newsection.entities[eid])
            newsection.triggers[tid] = newtrigger
    if 'relanns' in data:
        for datarelation in data["relanns"]:
            rid = datarelation["id"]
            rtype = unun(datarelation["type"])
            robject = datarelation["object"]
            rsubject = datarelation["subject"]
            newrelation = relation(rid, robject, rsubject, rtype)
            newsection.relations[rid] = newrelation
            if rtype not in newsection.relationTypes:
                newreltype = relationType(rtype)
                newreltype.addarg1type(newsection.getentitytype(rsubject))
                newreltype.addarg2type(newsection.getentitytype(robject))
                newreltype.occurrences = 1
                newsection.relationTypes[rtype] = newreltype
            else:
                newsection.relationTypes[rtype].addarg1type(newsection.getentitytype(rsubject))
                newsection.relationTypes[rtype].addarg2type(newsection.getentitytype(robject))
                newsection.relationTypes[rtype].occurrences += 1
    return newsection


class entity:
    def __init__(self, eid, charStart, charEnd, etype):
        self.start = charStart
        self.end = charEnd
        self.eid = eid
        self.etype = etype


class eventTrigger:
    def __init__(self, tid, entity):
        self.triggerid = tid
        self.entity = entity


class relation:
    def __init__(self, rid, robject, rsubject, rtype):
        self.rid = rid
        self.robject = robject
        self.rsubject = rsubject
        self.rtype = rtype


class section:
    def __init__(self, name, sourcedb, sourceid):
        self.name = name
        self.sourcedb = sourcedb
        self.sourceid = sourceid
        self.relations = {}
        self.entities = {}
        self.triggers = {}
        self.entityTypes = {}
        self.relationTypes = {}

    def getentitytype(self, eid):
        if eid in self.entities:
            return self.entities[eid].etype
        elif eid in self.triggers:
            return "event"


class relationType:
    def __init__(self, name):
        self.name = name
        self.arg1types = {}
        self.arg2types = {}
        self.occurrences = 0

    def name(self):
        return self.name

    def addarg1type(self, argtype, occ=1):
        if argtype not in self.arg1types:
            self.arg1types[argtype] = occ
        else:
            self.arg1types[argtype] += occ

    def addarg2type(self, argtype, occ=1):
        if argtype not in self.arg2types:
            self.arg2types[argtype] = occ
        else:
            self.arg2types[argtype] += occ

    def args(self, arg1, arg2):
        self.addarg1type(arg1)
        self.addarg2type(arg2)

    def argwords(self, arg1, arg2):
        self.addarg1typeword(arg1)
        self.addarg2typeword(arg2)

    def getargTypes(self):
        return self.arg1types, self.arg2types


def unun(thing):
    newthing = thing
    if isinstance(thing, unicode):
            newthing = thing.encode('utf8')
    return newthing


def printrelationdetails(relationTypes):
    for reltypename in relationTypes:
        reltype = relationTypes[reltypename]
        print reltypename, reltype.occurrences
        print "\tsubject types \t"
        for atype in reltype.arg1types:
            print "\t\t " + atype + ":", reltype.arg1types[atype]
        print "\tobject types \t"
        for atype in reltype.arg2types:
            print "\t\t" + atype + ":", reltype.arg2types[atype]


data = readJSONfiles(sys.argv)
entityTypes, relationTypes = getTypes(data)
pprint(entityTypes)
printrelationdetails(relationTypes)
