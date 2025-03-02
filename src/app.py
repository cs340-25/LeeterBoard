import database

from flask import Flask, request, redirect, url_for, render_template


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True



@app.route('/', methods=['GET', 'POST'])
def home():
    # If user types in a school and presses submit
    if request.method == 'POST':
        school_name = request.form.get('school_input')
        return redirect(url_for('school', school_name=school_name))
    
    # Default display
    school_ratings = database.grab_all_school_ratings();

    result = []
    for school, ratings in school_ratings.items():
        avg = round(sum(ratings) / len(ratings), 2)
        result.append((avg, school))

    result.sort(reverse=True)

    return render_template('index.html', result=result)



@app.route('/school', methods=['GET', 'POST'])
def school():
    # This is for if we're already on the /school page and a user types in search bar
    if request.method == 'POST':
        school_name = request.form.get('school_input')
        users = database.get_users_by_school(school_name)
        users.sort(key=lambda user: user['contestRating'], reverse=True)
        return render_template('school.html', users=users, school_name=school_name)
    
    # This is for if we just got redirected from /home
    school_name = request.args.get('school_name', '') # Get school name from url
    users = database.get_users_by_school(school_name)
    users.sort(key=lambda user: user['contestRating'], reverse=True)
    return render_template('school.html', users=users, school_name=school_name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)