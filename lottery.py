import os
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def wheel_page():
    return render_template('wheel.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
