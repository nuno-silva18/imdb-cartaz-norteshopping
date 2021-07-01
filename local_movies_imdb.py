from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from imdb import IMDb
import os
import re
import requests
import smtplib

movies_names_list = []
movies_id_list = []
movies_ratings_list = []
stop_words_movies = ['2D', '3D', '4DX', 'ATMOS', 'IMAX', 'VP', 'VO', 'VIP', 'XVision']

cartaz_norteshop_page = requests.get("http://cinemas.nos.pt/cinemas/Pages/norteshopping.aspx")
cartaz_norteshop_soup = BeautifulSoup(cartaz_norteshop_page.text, 'html.parser')

cartaz_norteshop_a_links = cartaz_norteshop_soup.find_all('a', class_= 'list-item')
for a_link in cartaz_norteshop_a_links:
    a_href = a_link['href']
    if re.match(r'/Filmes/', a_href):
        movies_names_list.append(a_link.text)

imdb_obj = IMDb()

for movie in movies_names_list:
    movie_flag = 0
    for stop_word in stop_words_movies:
        if stop_word in movie:
            movie.replace(stop_word, '').strip() # Remove words that might throw off search on IMDB website
            re.sub('[($-)]+', '', movie) # Remove parenthesis with no chars between them from the titles of the movie
    movie_search_results = imdb_obj.search_movie(movie)
    if movie_search_results:
        movie_obj = movie_search_results[0]
        movie_obj_id = movie_obj.getID()
        if movie_obj_id not in movies_id_list:
            movies_id_list.append(movie_obj_id)
            imdb_obj.update(movie_obj)
            print(movie_obj)
            if 'rating' in movie_obj:
                movies_ratings_list.append([movie, movie_obj, movie_obj['rating']]) # Movies that have not yet been released will not have a rating
            else:
                movies_ratings_list.append([movie, movie_obj, "This movie has not been released yet!"])
        else:
            movies_ratings_list.append([movie, '', "No information has been found for this movie :("])

msg_text = "Here are this week's movies airing at NorteShopping with an IMDB rating equal to or over 7.5:\n\n"

for movie, movie_en, rating in movies_ratings_list:
    if isinstance(rating, float):
        if rating > 7.5:
            msg_text += str(movie) + '\nOriginal title: ' + str(movie_en) + '\nIMDB Rating: ' + str(rating) + '\n\n'

msg = MIMEMultipart('alternative', None, [MIMEText(msg_text)])

msg['Subject'] = 'Your weekly update on great movies airing at NorteShopping!'
msg['From'] = os.environ.get("EMAIL_SENDER") 
msg['To'] = os.environ.get("EMAIL_RECIPIENT")

server = smtplib.SMTP('smtp.gmail.com', 587)
server.ehlo()
server.starttls()
server.login(os.environ.get("EMAIL_SENDER"), os.environ.get("EMAIL_PASSWORD"))
server.sendmail(os.environ.get("EMAIL_SENDER"), os.environ.get("EMAIL_RECIPIENT"), msg.as_string())
server.quit()