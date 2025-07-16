# Program that tests MongoDB functions
import os
from pymongo import MongoClient
from datetime import datetime

# Setup connection
client = MongoClient(os.environ.get("MONGO_CONNECTION_STRING"))
db = client['mongodbVSCodePlaygroundDB']
collection = db['sales']

collection.insert_many([
  {
    "item" : "banana",
    "price" : 75,
    "quantity" : 14,
    "date" : datetime.now()
  }, 
  {
    "item" : "apple",
    "price" : 15,
    "quantity" : 80,
    "date" : datetime.now()
  }, 
  {
    "item" : "grape",
    "price" : 4,
    "quantity" : 110,
    "date" : datetime.now()
  }
])

collection.delete_many({"$or" : [{"price" : 75}, {"item" : "abc"}]})
collection.insert_many([
  {
    "item" : "apple",
    "price" : 18,
    "quantity" : 200,
    "date" : datetime.now()
  }, 
  {
    "item" : "grape",
    "price" : 40,
    "quantity" : 10,
    "date" : datetime.now()
  },
    {
    "item" : "apple",
    "price" : 5,
    "quantity" : 800,
    "date" : datetime.now()
  }, 
  {
    "item" : "grape",
    "price" : 14,
    "quantity" : 67,
    "date" : datetime.now()
  }
])

collection.aggregate([
  {
    "$group" : {
      "_id" : "$item",
      "num_sales" : {"$sum" : "$quantity"},
      "total_amt" : {"$sum" : {"$multiply" : ["$price", "$quantity"]}}}
  },
  {
    "$out" : "itemSales"
  }
])

collection.aggregate([
  {
    "$group" : {
      "_id" : "$date",
      "num_sales" : {"$sum" : "$quantity"},
      "total_amt" : {"$sum" : {"$multiply" : ["$price", "$quantity"]}}}
  },
  {
    "$out" : "salesByDate"
  }
])