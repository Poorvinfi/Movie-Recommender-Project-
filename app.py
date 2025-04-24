# Import necessary libraries
from flask import Flask, render_template, request, jsonify, redirect
import requests
import re
import os
from textblob import TextBlob
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get OMDB API key from environment variables
# You'll need to sign up for an API key at http://www.omdbapi.com/
API_KEY = os.getenv("OMDB_API_KEY")
BASE_URL = "http://www.omdbapi.com/"

def get_movie_details(imdb_id):
    """Fetch detailed information about a specific movie."""
    params = {
        "apikey": API_KEY,
        "i": imdb_id,
        "plot": "full"
    }
    response = requests.get(BASE_URL, params=params)
    return response.json()

def get_movie_reviews(title):
    """Fetch movie reviews and perform sentiment analysis."""
    # OMDB doesn't provide user reviews directly, this is a mock function
    # In a real app, you might want to use another API or web scraping for reviews
    # For the purpose of this demo, we'll generate some mock reviews
    mock_reviews = [
        {"author": "MovieFan1", "content": "Absolutely loved this movie! The acting was superb.", "date": "2024-03-15"},
        {"author": "CriticEye", "content": "While the visuals were stunning, the plot was somewhat lacking in depth.", "date": "2024-02-28"},
        {"author": "FilmBuff42", "content": "A masterpiece of modern cinema. One of the best films I've seen this year.", "date": "2024-01-20"},
        {"author": "RegularViewer", "content": "It was okay. Not great, not terrible. Decent way to spend an evening.", "date": "2024-04-10"},
        {"author": "DisappointedFan", "content": "I expected much more based on the trailer. The pacing was off and characters underdeveloped.", "date": "2024-03-05"}
    ]
    
    # Filter reviews to make them seem related to the movie title
    title_words = title.lower().split()
    filtered_reviews = []
    for review in mock_reviews:
        # Include the review if it doesn't directly contradict the sentiment we're trying to show
        filtered_reviews.append(review)
        if len(filtered_reviews) >= 3:  # Limit to 3 reviews
            break
    
    return filtered_reviews

def search_movies(query):
    """Search for movies based on a query."""
    params = {
        "apikey": API_KEY,
        "s": query,
        "type": "movie"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    
    if data.get("Response") == "True":
        return data.get("Search", [])
    else:
        return []

def get_similar_movies(movie):
    """Get similar movies based on a movie's title and genre."""
    # OMDB doesn't have a similar movies endpoint
    # We'll search for movies with similar genres or from the same year
    
    # Extract genre and year
    genre = movie.get("Genre", "").split(",")[0].strip()
    year = movie.get("Year", "").split("–")[0].strip()  # Handle TV series with year ranges
    
    # Construct a search query based on genre
    if genre:
        params = {
            "apikey": API_KEY,
            "s": genre,
            "type": "movie",
            "y": year
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if data.get("Response") == "True":
            # Filter out the original movie and limit to 8 results
            similar_movies = [movie for movie in data.get("Search", []) if movie.get("imdbID") != movie.get("imdbID")][:8]
            return similar_movies
    
    # Fallback: search for movies from the same year
    params = {
        "apikey": API_KEY,
        "s": "movie",
        "type": "movie",
        "y": year
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    
    if data.get("Response") == "True":
        # Filter out the original movie and limit to 8 results
        similar_movies = [movie for movie in data.get("Search", []) if movie.get("imdbID") != movie.get("imdbID")][:8]
        return similar_movies
    
    return []

def perform_sentiment_analysis(reviews):
    """Perform sentiment analysis on movie reviews."""
    if not reviews:
        return {"positive": 0, "neutral": 0, "negative": 0, "average": 0}
    
    sentiments = []
    for review in reviews:
        content = review.get("content", "")
        blob = TextBlob(content)
        sentiments.append(blob.sentiment.polarity)
    
    # Count sentiments
    positive = sum(1 for s in sentiments if s > 0.1)
    negative = sum(1 for s in sentiments if s < -0.1)
    neutral = len(sentiments) - positive - negative
    
    # Calculate average sentiment
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    
    return {
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "average": round(avg_sentiment, 2)
    }

def get_popular_movies():
    """Get a list of popular movies."""
    # OMDB doesn't have a popular movies endpoint
    # We'll use a list of popular movie titles to search for
    popular_titles = [
        "Inception", "The Shawshank Redemption", "The Dark Knight",
        "Pulp Fiction", "Fight Club", "Forrest Gump", "The Matrix",
        "Goodfellas", "The Lord of the Rings", "Interstellar", "Parasite", "Oppenheimer"
    ]
    
    popular_movies = []
    for title in popular_titles:
        params = {
            "apikey": API_KEY,
            "s": title,
            "type": "movie"
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        if data.get("Response") == "True" and data.get("Search"):
            popular_movies.append(data.get("Search")[0])  # Add the first result
    
    return popular_movies

@app.route('/')
def index():
    """Home page - shows popular movies initially."""
    movies = get_popular_movies()
    return render_template('index.html', movies=movies)

@app.route('/movie/<imdb_id>')
def movie_detail(imdb_id):
    """Movie detail page."""
    movie = get_movie_details(imdb_id)
    
    # Check if movie was found
    if movie.get("Response") == "False":
        return redirect('/')
    
    # Get reviews and perform sentiment analysis
    reviews = get_movie_reviews(movie.get("Title", ""))
    sentiment = perform_sentiment_analysis(reviews)
    
    # Get similar movies
    similar_movies = get_similar_movies(movie)
    
    # Extract cast information
    cast = movie.get("Actors", "").split(", ")
    cast_info = [{"name": actor} for actor in cast]
    
    return render_template('movie_detail.html', 
                           movie=movie, 
                           similar_movies=similar_movies, 
                           cast=cast_info, 
                           reviews=reviews, 
                           sentiment=sentiment)

@app.route('/search')
def search():
    """Search for movies."""
    query = request.args.get('query', '')
    if not query:
        return redirect('/')
    
    movies = search_movies(query)
    return render_template('search_results.html', movies=movies, query=query)

@app.route('/api/similar/<imdb_id>')
def api_similar_movies(imdb_id):
    """API endpoint to get similar movies."""
    movie = get_movie_details(imdb_id)
    similar_movies = get_similar_movies(movie)
    return jsonify(similar_movies)

if __name__ == '__main__':
    app.run(debug=True)