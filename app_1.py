from flask import Flask, render_template, request

app = Flask(__name__)

LOOKER_BASE_URL = "https://lookerstudio.google.com/reporting/c18e2663-f49b-4d0c-b52e-f9f751af31dc/page/grvIF"

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        batch = request.form.get('batch_year')
        semester = request.form.get('semester')
        course = request.form.get('course')

        looker_url = f"{LOOKER_BASE_URL}?Batch_year_={batch}&Semester_={semester}&Course_={course}"
        return render_template('dashboard.html', looker_url=looker_url)

    # Default case (GET): show empty iframe
    return render_template('dashboard.html', looker_url=None)

if __name__ == "__main__":
    app.run(debug=True)
