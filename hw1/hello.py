from flask import Flask, request
app = Flask(__name__)

@app.route("/hello")
def hello():
    return "Hello World!"

@app.route("/echo")
def echo():
	return request.args['msg']

if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0') 