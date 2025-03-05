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
    
    # Default display (GET)
    # Display averages here
    result = []
    result = database.calculate_university_averages()
    return render_template('index.html', result=result)



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