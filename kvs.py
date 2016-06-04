from flask import Flask, request, jsonify, redirect
import re
import sys
import os
import time
import requests
import thread
app = Flask(__name__)


DATA = {}
MEMBERS = [5001, 5002, 5003]
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

        if sys.getsizeof(value) <= 1573000:
            if re.match("^[a-zA-Z0-9_]+$", value):
                for backup_ip in backupIPs:
                    r = requests.put(backup_ip + '/backup_kvs/' + key, data = {'val' : value})
                return handle_put(key, value) 
            return handle_char_error()
        return handle_size_error()
    #delete message
    elif method == 'DELETE':
        return handle_delete(key)
    #get message
    return handle_get(key)
   
def backupHttp(key, method):
    if(method == 'PUT'):
        try:
            value = request.args['val']
        except:
            pass
        try:
            value = request.form['val']
        except:
            return request.url
        
        r = requests.put(primaryIP + '/kvs/' + key, data = {'val' : value})
        
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

        if sys.getsizeof(value) <= 1573000:
            if re.match("^[a-zA-Z0-9_]+$", value):
                return handle_put(key, value) 
            return handle_char_error()
        return handle_size_error()
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
    return del_success(key)

def sayHello(primary):
    while (True and not primary):
        print("I am a thread")
        time.sleep(5)
        r = requests.get(primaryIP + '/hello')

primary = False
primaryIP = None
backupIPs = []

if __name__ == "__main__":
    MEMBERS = sorted(MEMBERS)
    if (int(sys.argv[1]) == MEMBERS[0]):
        primary = True
   
    primaryIP = 'http://localhost:' + str(MEMBERS[0])
    backupIPs.append('http://localhost:' + str(MEMBERS[1]))
    backupIPs.append('http://localhost:' + str(MEMBERS[2]))
    app.debug = False
    thread.start_new_thread(sayHello, (primary, ))

    app.run(port=int(sys.argv[1]), host='localhost')
