from flask import Flask, request, jsonify
import re
import sys
app = Flask(__name__)

DATA = {}

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

@app.route("/kvs/<key>", methods=['GET', 'PUT', 'DELETE'])
def foo(key):
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
    elif request.method == 'DELETE':
        return handle_delete(key)
        
    #request.method == GET
    return handle_get(key)

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

if __name__ == "__main__":
    app.debug = True
    app.run(port=8080, host='0.0.0.0')
