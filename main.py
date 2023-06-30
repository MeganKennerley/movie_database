from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
import requests
import os

API_KEY = os.environ.get("API_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = "secret key"
Bootstrap5(app)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie.db"
db.init_app(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.String, nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=True)


class EditMovie(FlaskForm):
    rating = SelectField("What is your rating out of 10?", validators=[DataRequired()],
                         choices=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    review = StringField("Your review", validators=[DataRequired()])
    submit = SubmitField("Submit", validators=[DataRequired()])


class FindMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


# with app.app_context():
#     db.create_all()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc()))
    all_movies = result.scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = i + 1
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=['GET', 'POST'])
def add():
    global API_KEY
    form = FindMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": API_KEY,
            "query": movie_title
        }
        response = requests.get(url, params=params).json()["results"]
        return render_template("select.html", options=response)
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    global API_KEY
    movie_api_id = request.args.get("id")
    if movie_api_id:
        url = "https://api.themoviedb.org/3/movie"
        movie_api_url = f"{url}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": API_KEY}).json()
        new_movie = Movie(
            title=response["title"],
            year=response["release_date"].split("-")[0],
            img_url=f"https://image.tmdb.org/t/p/w500{response['poster_path']}",
            description=response["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditMovie()
    movie_id = request.args.get('id')
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    with app.app_context():
        current_db_sessions = db.session.object_session(movie_to_delete)
        current_db_sessions.delete(movie_to_delete)
        current_db_sessions.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)