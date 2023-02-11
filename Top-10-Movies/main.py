from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired
import requests

SEARCH_API = "https://api.themoviedb.org/3/search/movie"
GET_API = "https://api.themoviedb.org/3/movie/"
API_KEY = "e108c081cc06897202c1540efe873d77"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-collection.db'
db.init_app(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

class EditForm(FlaskForm):
    rating = StringField("Your Rating out of 10", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")

class AddForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Search Movie")
   
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    all_movies = db.session.query(Movie).order_by(Movie.rating.desc()).all()
    for movie in all_movies:
        movie.ranking = all_movies.index(movie) + 1
    db.session.commit()
    return render_template("index.html", movies=all_movies)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    edit_form = EditForm()
    movie_to_update = db.get_or_404(Movie, id)
    if edit_form.validate_on_submit():
        movie_to_update.rating = float(edit_form.rating.data)
        movie_to_update.review = edit_form.review.data
        db.session.commit()
        return redirect("/")
    return render_template("edit.html", form=edit_form, movie=movie_to_update)

@app.route("/add", methods=["GET", "POST"])
def add_movie():
    add_form = AddForm()
    if add_form.validate_on_submit():
        title = add_form.title.data
        params = {
            "api_key": API_KEY,
            "query": title
        }
        res = requests.get(SEARCH_API, params=params)
        data = res.json()
        movies = data['results']
        return render_template("/select.html", movies=movies)
    return render_template("add.html", form=add_form)

@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete(id):
    movie_to_delete = db.get_or_404(Movie, id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect("/")

@app.route("/select/<int:id>", methods=["GET", "POST"])
def select(id):
    movie_id = id
    params = {
        "api_key": API_KEY
    }
    res = requests.get(f"{GET_API}{movie_id}", params=params)
    movie = res.json()
    new_movie = Movie(
            title=movie['title'], 
            year=movie['release_date'].split("-")[0], 
            desc=movie['overview'], 
            rating=movie['vote_average'], 
            img_url=f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(f"/edit/{new_movie.id}")

if __name__ == '__main__':
    app.run(debug=True)
