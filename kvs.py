from flask import Flask, request, jsonify, redirect
import re
import sys
import os
import time
import requests
import thread
app = Flask(__name__)

addNewData = []
removeData = []
DATA = {}
MEMBERS = os.environ.get('MEMBERS').split(',')
aliveMembers = []
afkMembers = []
deadMembers = []
initThread = False


def put_success(value):
    body = {
        'replaced' : value,
        'msg' : 'success'
    }
    return jsonify(body)

def get_success(key):
    #return DATA[key]
    body = {
        'msg' : 'success',
        'value' : DATA[key]
    }
    return jsonify(body)

def get_error():
    body = {
        'msg' : 'error',
        'error' : 'key does not exist'
    }
    return jsonify(body)

def del_error(key):
    body = {
        'msg' : 'error',
        'error' : 'key does not exist'
    }
    return jsonify(body)

def del_success(key):
    del DATA[key]
    body = {
        'msg' : 'success'
    }
    return jsonify(body)

@app.route("/hello")
def hello():
    return "Hello World!"

@app.route("/echo")
def echo():
    return request.args['msg']

@app.route("/heartbeat")
def hbreturn():
    return myIP

@app.route("/kvs/")
def empty():
    return handle_noinput_error()

def primaryHttp(key, method):
    if len(key) > 250:
        return handle_keysize_error()
    
    #request value
    if method == 'PUT':
        try:
            value = request.args['val']
        except:
            pass
        try:
            value = request.form['val']
        except:
            return get_error()

        if sys.getsizeof(value) > 1573000:
            return handle_size_error()

        if not re.match("^[a-zA-Z0-9_]+$", value):
            return handle_char_error()

        return handle_put(key, value) 
            
       
    #delete message
    elif method == 'DELETE':
        
        return handle_delete(key)
    #get message
    return handle_get(key)
   
def backupHttp(key, method):
    global primaryIP
    if(method == 'PUT'):
        try:
            value = request.args['val']
        except:
            pass
        try:
            value = request.form['val']
        except:
            return request.url
        print "Trying to write to: ", primaryIP
        r = requests.put(primaryIP +  '/kvs/' + key, data = {'val' : value})
        #r = requests.get(primaryIP + '/hello')
        
        return (r.text, r.status_code, r.headers.items())

    if(method == 'GET'):
        r = requests.get(primaryIP + '/kvs/' + key)
        return (r.text, r.status_code, r.headers.items())
    if(method == 'DELETE'):
        r = requests.delete(primaryIP + '/kvs/' + key)
        return (r.text, r.status_code, r.headers.items())

@app.route("/backup_kvs/<key>", methods=['GET', 'PUT', 'DELETE'])
def backup_kvs(key):
    if len(key) > 250:
        return handle_keysize_error()

    #request value
    if request.method == 'PUT':
        try:
            value = request.args['val']
        except:
            pass
        try:
            value = request.form['val']
        except:
            return get_error()
        return handle_put(key, value) 
    #delete message
    elif request.method == 'DELETE':
        return handle_delete(key)
    #get message
    return handle_get(key)

@app.route("/kvs/<key>", methods=['GET', 'PUT', 'DELETE'])
def kvsRoute(key):    
    if primary:
        return primaryHttp(key, request.method)
    else:
        return backupHttp(key, request.method)
        


def handle_keysize_error():
    body = {
        'msg' : 'error',
        'error' : 'key size too large'
    }
    return jsonify(body), 414

def handle_size_error():
    body = {
        'msg' : 'error',
        'error' : 'input size too large'
    }
    return jsonify(body), 413

def handle_noinput_error():
    body = {
        'msg' : 'error',
        'error' : 'no key'
    }
    return jsonify(body), 412

def handle_char_error():
    body = {
        'msg' : 'error',
        'error' : 'unsupported character'
    }
    return jsonify(body), 413

def handle_put(key, value):
    if primary:
        addNewData.append((key, value))
    #key not in dict, create one
    if key not in DATA:
        DATA[key] = value
        return put_success(0), 201
    #key is in dict, replace
    DATA[key] = value
    return put_success(1)

def handle_get(key):
    #key not found
    if key not in DATA:
        return get_error(), 404
    #key found, return value
    return get_success(key)

def handle_delete(key):
    #key not found
    if key not in DATA:
        return del_error(key), 404
    #delete kvs
    if primary:
        removeData.append(key)
    return del_success(key)

@app.route("/primary_crash")
def primary_crash():
    return "Primary crash", 404

@app.route("/alive")
def alive():
    return "1", 200

@app.route("/alivecheck/<node>", methods=['GET'])
def checkNode(node):
    try:
        r = requests.get(node + 'alive')
        return "alive"
    except (requests.exceptions.ConectionError) as e:
        return "dead"
       
       
def nodeCrash(node):
    global aliveMembers
    global afkMembers
    global deadMembers
    global primaryIP
    global primary
    global backupIPs
    aliveMembers.remove(node)
    print "Alive Nodes: ", aliveMembers
    afkMembers.append(node)
    global myIP
    agreeBool = True
    for member in aliveMembers:
        try:
            r = requests.get(member + '/alivecheck/' + node)
            if r == "alive":
                agreeBool = False
        except (requests.exceptions.ConnectionError) as e:
            pass
    if agreeBool == True:
        afkMembers.remove(node)
        try:
            backupIPs.remove(node)
        except ValueError:
            pass
        deadMembers.append(node)
        print "Dead Nodes: ", deadMembers
        print "Backups: ", backupIPs
        primaryIP = aliveMembers[0]
        if myIP == primaryIP:
            primary = True
            try:
                backupIPs.remove(myIP)
            except ValueError:
                pass
          

#wakes up every 5 secondss to send a heartbeat, then waits
#1 second for response, if none begin re-election
def heartbeat():
    connect_timeout = 1
    while (True):
        time.sleep(2)
        print aliveMembers
        for node in aliveMembers:
            if(node == myIP):
                continue
            try:
                r = requests.get(node + '/heartbeat')
                # sending put request to backups
                for new_d in addNewData:
                    for backup_ip in backupIPs:
                        r = requests.put(backup_ip + '/backup_kvs/' + new_d[0], data = {'val' : new_d[1]})
                    addNewData.remove(new_d)
                # sending delete request to backups
                for rm_data in removeData:
                    for backup_ip in backupIPs: 
                        r = requests.delete(backup_ip + '/backup_kvs/' + rm_data)
                    removeData.remove(rm_data)
                    #print "text: ", r.text
            except (requests.exceptions.ConnectionError) as e:
                #r = requests.get('http://localhost:5002/primary_crash')
                nodeCrash(node)


primary = False
primaryIP = None
backupIPs = []
myIP = None
myPort = None

if __name__ == "__main__":
    MEMBERS = sorted(MEMBERS)
    print MEMBERS
    if ((os.environ.get('IP') + ':' + (os.environ.get('PORT')) == MEMBERS[0])):
        primary = True
   
    primaryIP = 'http://' + str(MEMBERS[0])
    for member in MEMBERS:
        backupIPs.append('http://' + member)
        aliveMembers.append('http://' + member)
    primaryIP = backupIPs.pop(0)
    print primaryIP      
    app.debug = False
    thread.start_new_thread(heartbeat, ())
    myPort = os.environ.get('PORT')
    myIP = 'http://' + os.environ.get('IP') +':' + myPort

    app.run(port=myPort, host=os.environ.get('IP'))