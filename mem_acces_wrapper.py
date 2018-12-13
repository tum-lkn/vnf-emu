#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 09:42:07 2018

@author: Raphael Durner
"""

import redis
import logging
import argparse
from subprocess import PIPE,Popen, TimeoutExpired
from time import sleep
import socket
import json

log = logging.getLogger(__name__)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Start Mockup VNF emulating Memory Accesses.")
    parser.add_argument('-r', '--redis', help="Output redis host.",type=str,required=True)
    parser.add_argument('-i', '--id', help="VNF ID",type=str,default=socket.gethostname())
    parser.add_argument('-p', '--publish', help="Channel for publishing results.",type=str,default='VNF_Metrics')
    parser.add_argument('-s', '--settings', help="Key for Settingsdict.",type=str,default='Mockup_Settings')
    parser.add_argument('-P', '--port', help="Output redis instance port.",type=int,default=6379)
    parser.add_argument('-x', '--executable', help="Memory access executable.",default='./mem_access')
    parser.add_argument('-C', '--core', help="Which core to use with taskset. Default without taskset",type=int,default=-1)
    parser.add_argument('-v', '--verbose', help="Enable debug log.", dest='verbose', action='store_true')
    
    
    

    cmdargs = parser.parse_args()

    logconf = {'format': '[%(asctime)s.%(msecs)-3d: %(name)-16s - %(levelname)-5s] %(message)s', 'datefmt': "%H:%M:%S"}

    if cmdargs.verbose:
        logging.basicConfig(level=logging.DEBUG, **logconf)
    else:
        logging.basicConfig(level=logging.INFO, **logconf)

    log.info("Starting with arguments: "+ str(vars(cmdargs))) 
    r = redis.StrictRedis(host=cmdargs.redis, port=cmdargs.port, db=0)
    #init process object
    p=Popen(['echo','1'],stdout=PIPE)
    p.wait()# Wait until finished
    categories=list()
    pubsub=r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(cmdargs.settings)
    ping_cnt=0
    while True:
        mess=pubsub.get_message()
        if mess:
            log.debug('Got Message:'+str(mess))
            try:
                settings=json.loads(mess['data'].decode())
                log.debug('Got Settings:'+str(settings))
            except json.decoder.JSONDecodeError:
                log.info('Redis Channel Message:'+cmdargs.settings+'empty or malformed')
                settings=dict()  
            if 'stop' in settings:
                p.terminate()
                try:
                    p.wait(timeout=10)
                except TimeoutExpired:
                    log.warning("Mem access did not terminate in 10s ! Killing it.")
                    p.kill()
                    p.wait()

            if (cmdargs.id+'.pps' in settings and 
                cmdargs.id+'.mem' in settings and 
                cmdargs.id+'.alpha' in settings):
                    p.terminate()
                    p.wait()

                    if cmdargs.core < 0:
                        command=[cmdargs.executable,str(settings[cmdargs.id+'.pps']),
                             str(settings[cmdargs.id+'.mem']),str(settings[cmdargs.id+'.alpha'])]
                        log.info('Executing:'+str(command))
                        p= Popen(command,stdout=PIPE,universal_newlines=True)  
                    else:
                        command=['taskset','-c',str(cmdargs.core),cmdargs.executable,str(settings[cmdargs.id+'.pps']),
                             str(settings[cmdargs.id+'.mem']),str(settings[cmdargs.id+'.alpha'])]
                        log.info('Executing:'+str(command))
                        p= Popen(command,stdout=PIPE,universal_newlines=True)  
                    first_line=p.stdout.readline()
                    log.debug("Got from stdout:"+first_line)
                    categories=first_line.rstrip().split(',')
                    categories=[cmdargs.id+'.'+cat for cat in categories]
                    log.info("Publishing categories: "+str(categories))
            else:
                log.debug('Redis Channel:'+cmdargs.settings+' has no settings for us')
                continue #check for more messages
        else: #received no message
            ping_cnt+=1
            if ping_cnt>100:
                pubsub.subscribe(cmdargs.settings) #network timeout workaround
                ping_cnt=0
            
        if p.poll() is None:#process is active
            r_line=p.stdout.readline()#blocking call
            log.debug("Got from stdout:"+str(r_line))
            r_tup=r_line.rstrip().split(',')
            data=dict()
            for i,cat in enumerate(categories):
                data[cat]=r_tup[i]
            r.publish(cmdargs.publish,json.dumps(data))
        else:
            sleep(1)
