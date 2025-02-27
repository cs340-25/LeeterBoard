import database

from flask import Flask, request, render_template


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.get('/')
def index():
    users = database.get_users_by_school('University of Florida')
    users.sort(key=lambda user: user['contestRating'], reverse=True)
    return render_template('index.html', users=users)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)