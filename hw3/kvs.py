from flask import Flask, request, jsonify, redirect
import re
import sys
import os
import thread
import time
import requests
app = Flask(__name__)


DATA = {}
MEMBERS = [5001, 5002, 5003]


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
            return request.url

        if sys.getsizeof(value) <= 1573000:
            if re.match("^[a-zA-Z0-9_]+$", value):
                return handle_put(key, value) 
            return handle_char_error()
        return handle_size_error()
    elif request.method == 'DELETE':
        return handle_delete(key)
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
        r = requests.delete(primaryIP, data = key)
        return (r.text, r.status_code, r.headers.items())




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
        x = 2345600*100
        time.sleep(5)
        r = requests.get(primaryIP + '/hello')

primary = False
primaryIP = None

if __name__ == "__main__":
    MEMBERS = sorted(MEMBERS)
    
    print MEMBERS
    if (int(sys.argv[1]) == MEMBERS[0]):
        primary = True
    primaryIP = 'http://localhost:' + str(MEMBERS[0])
    app.debug = True
    thread.start_new_thread(sayHello, (primary, ))
    app.run(port=int(sys.argv[1]), host='localhost')
