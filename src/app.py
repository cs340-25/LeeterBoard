import database

from flask import Flask, request, redirect, url_for, render_template
import json

from data.university_websites import university_websites
from data.university_abbreviations import university_abbreviations
from data.university_slugs import university_slugs


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.get('/unipage2/<slug>')
def unipage2(slug):
    regular_school_name = university_slugs[slug]

    school_weekly_averages = database.get_school_weekly_averages()
    # for school, averages in school_weekly_averages.items():
    #     print(f"{school}")
    #     for rating in averages:
    #         print(f"{rating['week']}, {rating['average']}")
    #     print("\n")

    # Convert the python list to JSON string for Chart.js
    ratings_json = json.dumps(school_weekly_averages[regular_school_name])
    logo_url = university_websites[regular_school_name]
    
    return render_template('unipage2.html', ratings_json=ratings_json, logo_url=logo_url)

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

@app.get('/uni-comp-tool')
def stats():
    school_names = database.grab_all_schools_only()
    return render_template('uni_comp_tool.html', school_names=school_names)


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