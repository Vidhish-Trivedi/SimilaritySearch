from flask import Flask, render_template, request

app = Flask(__name__)

###################################################################################################################
# @app.route("/")
# def index():
#     name = "John"
#     letters = list(name)
#     dictionary = {'name': 'Jack', 'age': 12}
#     nums = [2, 3, 5, 7, 11, 13]
#     return render_template("basic.html", p_name=name, p_letters=letters, p_dictionary=dictionary, nums=nums)

###################################################################################################################
# @app.route("/")
# def index():
#     return render_template("home.html")

# @app.route("/person/<name>")
# def person_name(name):
#     return render_template("person.html", name=name)

###################################################################################################################
@app.route("/")
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/thankyou')
def thankyou():
    # Name of the variable in session that stores 'First Name' is 'first'.
    first = request.args.get('first')
    last = request.args.get('last')

    return render_template('thankyou.html', first=first, last=last)

# Pass in the error code.
@app.errorhandler(404)
def page_not_found(err):
    return (render_template('404.html'), 404)

if __name__ == "__main__":
    app.run(debug=True)
