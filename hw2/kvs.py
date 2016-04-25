from flask import Flask, request, jsonify


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

@app.route("/kvs/<key>", methods=['GET', 'PUT', 'DELETE'])
def foo(key):
    #request value
    if request.method == 'PUT':
        try:
            value = request.args['val']
        except:
            pass
        try:
            value = request.form['val']
        except:
            get_error
            
        return handle_put(key, value)
    elif request.method == 'DELETE':
        return handle_delete(key)
    #request.method == GET
    return handle_get(key)

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
    app.run(port=8080, host='localhost')