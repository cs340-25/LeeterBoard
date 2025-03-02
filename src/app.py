import database

from flask import Flask, request, render_template


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True



@app.get('/test/schools/')
def test():
    school_ratings = database.grab_all_school_ratings();

    result = []
    for school, ratings in school_ratings.items():
        avg = round(sum(ratings) / len(ratings), 2)
        result.append((avg, school))

    result.sort(reverse=True)

    return render_template('index.html', result=result)



@app.get('/')
def index():
    users = database.get_users_by_school('University of Texas -Austin')
    users.sort(key=lambda user: user['contestRating'], reverse=True)
    return render_template('base.html', users=users)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)