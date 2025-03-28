import database

from flask import Flask, request, redirect, url_for, render_template
import json

from data.university_websites import university_websites
from data.university_abbreviations import university_abbreviations
from data.university_slugs import university_slugs
from data.university_colors import university_colors


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
        school_input = request.form.get('school_input')
        for slug, school_name in university_slugs.items():
            if school_input == school_name:
                return redirect(url_for('school', slug=slug))
        
        # Did not find school, return error page
        return render_template('testing.html')
    

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
def uni_comp_tool():
    school_weekly_averages = database.get_school_weekly_averages()
    ratings_json = json.dumps(school_weekly_averages)

    school_names = database.grab_all_schools_only()
    return render_template('uni_comp_tool.html', ratings_json=ratings_json, school_names=school_names, school_colors=university_colors, school_abbrev=university_abbreviations, school_websites=university_websites)




@app.route('/<slug>', methods=['GET'])
def school(slug):
    # GET (direct URL access from homepage)
    if slug in university_slugs:
        school_name = university_slugs[slug]
        users = database.get_users_by_school(school_name)
        users.sort(key=lambda user: user['currentRating'], reverse=True)

        return render_template('school.html', users=users, school_name=school_name, slug=slug)
    
    # School not found in slug list
    print("got to school, not found")
    return render_template('testing.html')
    # return an error.html


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)