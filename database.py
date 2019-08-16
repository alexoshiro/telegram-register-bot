import os
from pymongo import MongoClient

client = None
database = None

def getDatabase():
    global client
    global database
    if(client == None):
        client = MongoClient(os.environ['MONGO_URL'])
    if(database == None):
        database = client['alerts']
    return database

def getUserCollection():
    db = getDatabase()
    return db['users']
