from flask import Flask, render_template

app = Flask(__name__)

# @app.route("/")
# def index():
#     name = "John"
#     letters = list(name)
#     dictionary = {'name': 'Jack', 'age': 12}
#     nums = [2, 3, 5, 7, 11, 13]
#     return render_template("basic.html", p_name=name, p_letters=letters, p_dictionary=dictionary, nums=nums)

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/person/<name>")
def person_name(name):
    return render_template("person.html", name=name)

if __name__ == "__main__":
    app.run(debug=True)
