#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 12 12:38:00 2018

@author: Raphael Durner
"""
import redis
import json

def configMemAccVNF(name,config):
    r=redis.StrictRedis(host='192.168.3.20', port=6379, db=0)
    set_dic=dict();
    for k,v in config.items():
        set_dic[name +'.'+k]=v
    r.publish('Mockup_Settings',json.dumps(set_dic))
    
#%%    
configMemAccVNF('contrib-stretch',{'pps':500,'mem':100,'alpha':1})

#%%
r=redis.StrictRedis(host='192.168.3.20', port=6379, db=0)
r.publish('Mockup_Settings','{"stop":0}')
