import database

from flask import Flask, request, redirect, url_for, render_template

from data.university_websites import university_websites
from data.university_abbreviations import university_abbreviations


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.get('/unipage2')
def unipage2():

    school_weekly_averages = database.get_school_weekly_averages()
    # for school, averages in school_weekly_averages.items():
    #     print(f"{school}", end="")
    #     for rating in averages:
    #         print(f"{rating}")
    #     print("\n")


    return render_template('unipage2.html', ratings=school_weekly_averages)

@app.get('/testpage')
def testpage():
    return render_template('testing.html')

@app.get('/unipage')
def unipage():
    return render_template('unipage.html')


@app.route('/', methods=['GET', 'POST'])
def home():
    # If user types in a school and presses submit
    if request.method == 'POST':
        school_name = request.form.get('school_input')
        return redirect(url_for('school', school_name=school_name))
    
    # Default display (GET)
    
    # Grabs all school info (curr avg rating, school name, rating change) -> sorted by curr avg rating (desc.)
    school_info = database.grab_university_info()
    school_info.sort(reverse=True)

    # Grabs all user rating changes -> sorted by rating changes (desc.)
    user_rating_changes = database.get_user_rating_changes()
    user_rating_changes.sort(reverse=True)

    # Grabs all school info (curr avg rating, school name, rating change) -> sorted by rating change (desc.)
    school_rating_changes = database.grab_university_info()
    school_rating_changes.sort(key=lambda x: x[2], reverse=True)

    return render_template('home.html', school_info=school_info, user_rating_changes=user_rating_changes, school_rating_changes=school_rating_changes,
                           university_websites=university_websites, university_abbreviations=university_abbreviations)



@app.route('/school', methods=['GET', 'POST'])
def school():
    if request.method == 'POST':
        school_name = request.form.get('school_input')
        users = database.get_users_by_school(school_name)
        users.sort(key=lambda user: user['currentRating'], reverse=True)


        return render_template('school.html', users=users, school_name=school_name)

    # if just /school is typed in for some reason
    return render_template('school.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)