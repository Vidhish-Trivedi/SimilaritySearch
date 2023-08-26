from flask import Flask

app = Flask(__name__)

# Basic routing.
@app.route("/")
def index():
    return("<h1>Hello, World!</h1>")

@app.route("/info")
def info():
    return("<p>This is the info page.</p>")

# Dynamic routing.
@app.route("/page/<page_num>")
def num_page(page_num): # This parameter comes from the url and is treated as a string.
    return(f"<p>You are on page {page_num}, page_num + 5: {int(page_num) + 5}</p>")

if __name__ == "__main__":
    app.run(debug=True)
