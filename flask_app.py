from flask import Flask, render_template, request, url_for
import sqlite3
#need below for bar chart of customer gender
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import numpy as np
import os

PARENT_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('artist_management_home_page.html')

@app.route('/home')
def home():
    return render_template('artist_management_home_page.html')

@app.route('/get_artist', methods=['GET', 'POST'])
def get_artist():
    if request.method == 'POST':
        # read the form data
        artist_first_name = request.form['artist_first_name']
        artist_last_name = request.form['artist_last_name']

        db_file = os.path.join(PARENT_DIR, "artist_management.db")
        # connect to the database
        conn = sqlite3.connect(db_file)

        # create a cursor object
        cursor = conn.cursor()

        # if no last name
        if (artist_last_name == ''):
            query = "SELECT artist_id AS 'Artist ID', artist_first_name || ' ' || artist_last_name AS 'Artist Name', artist_dob AS 'Date of Birth',\
                    number_of_albums AS 'No. of Albums', number_of_grammys_won AS 'No. of Grammys',monthly_spotify_listeners_M AS 'Monthly Spotify Listeners (M)'\
                    FROM artist WHERE artist_first_name = ?;"
            artist_info = pd.read_sql_query(query, conn, params=(artist_first_name,))

        else: # assumes we will ALWAYS have a first name
            # retrieve the artist information from the artist table
            query = "SELECT artist_id AS 'Artist ID', artist_first_name || ' ' || artist_last_name AS 'Artist Name', artist_dob AS 'Date of Birth',\
                    number_of_albums AS 'No. of Albums', number_of_grammys_won AS 'No. of Grammys',monthly_spotify_listeners_M AS 'Monthly Spotify Listeners (M)'\
                    FROM artist WHERE artist_first_name = ? AND artist_last_name = ?;"
            artist_info = pd.read_sql_query(query, conn, params = (artist_first_name,artist_last_name,))

        # close the database connection
        conn.close()

        if artist_info.empty:
            message = 'Check the artist name spelling and try again. This artist might not be in our management.\
            Please refer to our list of managed artists to search for those we represent.'
            return render_template('get_artist.html', message=message)
        else:
            return render_template('get_artist.html', artist_info = artist_info.to_html(index = False))
    else:
        return render_template('get_artist.html')

@app.route('/tour_sales', methods=['GET', 'POST'])
def tour_sales():
    if request.method == 'POST':
        artist_first_name = request.form['artist_first_name']
        artist_last_name = request.form['artist_last_name']

        # Establish a connection to the SQLite database
        conn = sqlite3.connect(os.path.join(PARENT_DIR, "artist_management.db"))

        # Create a cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # if no last name
        if (artist_last_name == ''):
            query = """SELECT artist_first_name || ' ' || artist_last_name AS 'Artist Name', tour_name AS 'Tour Name',
            customer.customer_id AS 'Fan ID', customer.customer_first_name || ' ' || customer.customer_last_name AS 'Fan Name',
            venue_name as Venue, location as Location, attendance_date AS 'Tour Date'
            FROM artist INNER JOIN headliner ON artist.artist_id = headliner.artist_id
            INNER JOIN tour ON headliner.headliner_id = tour.headliner_id
            LEFT JOIN tour_attendance ON tour.tour_id = tour_attendance.tour_id
            LEFT JOIN MA_venue ON tour_attendance.venue_id = MA_venue.venue_id
            LEFT JOIN customer ON customer.customer_id = tour_attendance.customer_id
            WHERE artist_first_name = ? ORDER BY 'Artist Name';"""
            total_sales = "SELECT count(customer.customer_id) AS 'Total Ticket Sales' FROM artist INNER JOIN headliner ON artist.artist_id = headliner.artist_id\
            INNER JOIN tour ON headliner.headliner_id = tour.headliner_id\
            LEFT JOIN tour_attendance ON tour.tour_id = tour_attendance.tour_id\
            LEFT JOIN MA_venue ON tour_attendance.venue_id = MA_venue.venue_id\
            LEFT JOIN customer ON customer.customer_id = tour_attendance.customer_id\
            WHERE artist_first_name = ? GROUP BY 'Artist Name' ORDER BY 'Artist Name';"
            fan_info = pd.read_sql_query(query, conn, params=(artist_first_name,))
            total_sales = pd.read_sql_query(total_sales, conn, params=(artist_first_name,))

        else: # assumes we will ALWAYS have a first name
         # retrieve the fan information from the tables
            query = "SELECT artist_first_name || ' ' || artist_last_name AS 'Artist Name', tour_name AS 'Tour Name',\
            customer.customer_id AS 'Fan ID', customer.customer_first_name || ' ' || customer.customer_last_name AS 'Fan Name',\
            venue_name as Venue, location as Location, attendance_date AS 'Tour Date'\
            FROM artist INNER JOIN headliner ON artist.artist_id = headliner.artist_id\
            INNER JOIN tour ON headliner.headliner_id = tour.headliner_id\
            LEFT JOIN tour_attendance ON tour.tour_id = tour_attendance.tour_id\
            LEFT JOIN MA_venue ON tour_attendance.venue_id = MA_venue.venue_id\
            LEFT JOIN customer ON customer.customer_id = tour_attendance.customer_id\
            WHERE artist_first_name = ? AND artist_last_name = ? ORDER BY 'Artist Name';"
            total_sales = "SELECT count(customer.customer_id) AS 'Total Ticket Sales' FROM artist INNER JOIN headliner ON artist.artist_id = headliner.artist_id\
            INNER JOIN tour ON headliner.headliner_id = tour.headliner_id\
            LEFT JOIN tour_attendance ON tour.tour_id = tour_attendance.tour_id\
            LEFT JOIN MA_venue ON tour_attendance.venue_id = MA_venue.venue_id\
            LEFT JOIN customer ON customer.customer_id = tour_attendance.customer_id\
            WHERE artist_first_name = ? AND artist_last_name = ? GROUP BY 'Artist Name' ORDER BY 'Artist Name';"
            fan_info = pd.read_sql_query(query, conn, params = (artist_first_name,artist_last_name,))
            total_sales = pd.read_sql_query(total_sales, conn, params=(artist_first_name,artist_last_name))

        # close the database connection
        conn.close()

        if fan_info.empty:
            message = 'No sales currently found.'
            return render_template('tour_sales.html', message=message)
        else:
            return render_template('tour_sales.html', fan_info = fan_info.to_html(index = False),total_sales=total_sales.to_html(index=False))
    else:
        return render_template('tour_sales.html')
    
@app.route('/add_new_artist', methods=['GET', 'POST'])
def add_new_artist():
    if request.method == 'POST':
        # read the form data
        artist_first_name = request.form.get('artist_first_name')
        artist_last_name = request.form.get('artist_last_name')
        artist_dob = request.form.get('artist_dob')
        number_of_albums = request.form.get('number_of_albums')
        number_of_grammys_won = request.form.get('number_of_grammys_won')
        monthly_spotify_listeners_M = request.form.get('monthly_spotify_listeners_M')
        genre_name = request.form.get('genre_name')

    # specify the file path for the database file
    # best wat is to go to db file in windows explorer
    #then cut/paste path here. change "\" to "/"
        db_file = os.path.join(PARENT_DIR, "artist_management.db")

        # connect to the database
        conn = sqlite3.connect(db_file)

        # create a cursor object
        cursor = conn.cursor()

        # retrieve the maximum product_id from the customer table
        cursor.execute("SELECT MAX(artist.artist_id), MAX(genre_id) FROM artist LEFT JOIN artist_genre ON artist.artist_id = artist_genre.artist_id")
        max_artist_id = cursor.fetchone()[0]

        # if the table is empty, start with customer_id = 1
        if max_artist_id is None:
            artist_id = 1
        else:
            artist_id = max_artist_id + 1

            # insert a new record into the customer table
            cursor.execute("INSERT INTO artist (artist_id, artist_first_name,\
                artist_last_name, artist_dob, number_of_albums, number_of_grammys_won, monthly_spotify_listeners_M)\
                VALUES (?, ?, ?, ?, ?, ?, ?)",\
                (artist_id, artist_first_name, artist_last_name, artist_dob, number_of_albums,number_of_grammys_won, monthly_spotify_listeners_M))

            cursor.execute("SELECT genre.genre_id FROM genre LEFT JOIN artist_genre ON genre.genre_id = artist_genre.genre_id\
                           WHERE genre_name = ?",(genre_name,))

            genre_id = cursor.fetchone()[0]
           
            cursor.execute('INSERT INTO artist_genre (genre_id, artist_id) VALUES (?, ?)', (genre_id, artist_id))

            # commit the transaction
            conn.commit()

                # close the database connection
            conn.close()

             # return a response to the user
            message = "Success: The new artist has been added \
             successfully to the database."
            return render_template('add_new_artist.html', message=message)
        
    else:
        # Render the form
        return render_template('add_new_artist.html')
    
@app.route('/add_single', methods=['GET', 'POST'])
def add_single():
    if request.method == 'POST':
        # read the form data
        artist_first_name = request.form.get('artist_first_name')
        artist_last_name = request.form.get('artist_last_name')
        album_name = request.form.get('album_name')
        song_name = request.form.get('song_name')
        single_release_date = request.form.get('single_release')
        highest_US_ranking = request.form.get('highest_US_ranking')

        # specify the file path for the database file
        db_file = os.path.join(PARENT_DIR, "artist_management.db")

        # connect to the database
        conn = sqlite3.connect(db_file)
            # create a cursor object
        cursor = conn.cursor()
        # retrieve the maximum single_id and album_id
        cursor.execute("""
                    SELECT MAX(single_id), MAX(album.album_id)
                    FROM single INNER JOIN album ON album.album_id = single.album_id""")
                
        result = cursor.fetchone()
        # if no last name
        if (artist_last_name == ''):
            if result is not None:
                    max_single_id = result[0]
                    single_id = max_single_id + 1
                    max_album_id = result[1]
            else:
                    print(None)

            cursor.execute("""
                    SELECT album.album_id
                    FROM album
                    INNER JOIN artist ON artist.artist_id = album.artist_id
                    WHERE artist_first_name = ? AND album_name = ?;
                """, (artist_first_name, album_name,))
            
            result1 = cursor.fetchone()

            if result1 is not None:
                retreived_album_id = result1[0]
                album_id = retreived_album_id
            else:
                print(' ')
                album_id = max_album_id + 1

                # insert a new record into the single table
            cursor.execute("""
                    INSERT INTO single (single_id, album_id,
                    song_name, single_release, highest_US_ranking)
                    VALUES (?, ?, ?, ?, ?)
                """, (single_id, album_id, song_name, single_release_date, highest_US_ranking))

            # commit the transaction
            conn.commit()

            # return a response to the user
        
            message = "Success: The new song has been added \
                successfully to the database."
            return render_template('add_single.html', message=message)
        else: # assumes we will ALWAYS have a first name
            if result is not None:
                    max_single_id = result[0]
                    single_id = max_single_id + 1
                    max_album_id = result[1]
            else:
                    print(None)

            cursor.execute("""
                    SELECT album.album_id
                    FROM album
                    INNER JOIN artist ON artist.artist_id = album.artist_id
                    WHERE artist_first_name = ? AND artist_last_name = ? AND album_name = ?;
                """, (artist_first_name, artist_last_name, album_name,))
            
            result1 = cursor.fetchone()

            if result1 is not None:
                retreived_album_id = result1[0]
                album_id = retreived_album_id
            else:
                print(' ')
                album_id = max_album_id + 1

                # insert a new record into the single table
            cursor.execute("""
                    INSERT INTO single (single_id, album_id,
                    song_name, single_release, highest_US_ranking)
                    VALUES (?, ?, ?, ?, ?)
                """, (single_id, album_id, song_name, single_release_date, highest_US_ranking))

            # commit the transaction
            conn.commit()

            # return a response to the user
        
            message = "Success: The new song has been added \
                successfully to the database."
            return render_template('add_single.html', message=message)


    else:
        # Render the form
        return render_template('add_single.html')
    
@app.route('/get_tour', methods=['GET', 'POST'])
def get_tour():
    if request.method == 'POST':
        # read the form data
        artist_first_name = request.form['artist_first_name']
        artist_last_name = request.form['artist_last_name']

        db_file = os.path.join(PARENT_DIR, "artist_management.db")
        # connect to the database
        conn = sqlite3.connect(db_file)

        # create a cursor object
        cursor = conn.cursor()

        # if no last name
        if (artist_last_name == ''):
            query = """SELECT h.artist_first_name || ' ' || h.artist_last_name AS 'Headlining Artist', t.tour_name AS 'Tour Name', o.artist_first_name || ' ' || o.artist_last_name AS 'Opener Artist'
            FROM artist AS h
            INNER JOIN headliner ON h.artist_id = headliner.artist_id
            INNER JOIN tour AS t ON t.headliner_id = headliner.headliner_id
            INNER JOIN opener AS op ON t.opener_id = op.opener_id
            INNER JOIN artist AS o ON op.artist_id = o.artist_id WHERE h.artist_first_name = ?"""
            tour_info = pd.read_sql_query(query, conn, params = (artist_first_name,))

        else: # assumes we will ALWAYS have a first name
            # retrieve the artist information from the artist table
            query = """SELECT h.artist_first_name || ' ' || h.artist_last_name AS 'Headlining Artist', t.tour_name AS 'Tour Name', o.artist_first_name || ' ' || o.artist_last_name AS 'Opener Artist'
            FROM artist AS h
            INNER JOIN headliner ON h.artist_id = headliner.artist_id
            INNER JOIN tour AS t ON t.headliner_id = headliner.headliner_id
            INNER JOIN opener AS op ON t.opener_id = op.opener_id
            INNER JOIN artist AS o ON op.artist_id = o.artist_id WHERE h.artist_first_name = ? AND h.artist_last_name=?"""
            tour_info = pd.read_sql_query(query, conn, params = (artist_first_name,artist_last_name,))

        # close the database connection
        conn.close()

        if tour_info.empty:
            message = 'Check the artist name spelling and try again. This artist might not be in our management.\
            Please refer to our list of managed artists to search for those we represent.'
            return render_template('get_tour.html', message=message)
        else:
            return render_template('get_tour.html', tour_info = tour_info.to_html(index = False))
    else:
        return render_template('get_tour.html')
    
@app.route('/get_discography', methods=['GET', 'POST'])
def get_discography():
    if request.method == 'POST':
        # read the form data
        artist_first_name = request.form['artist_first_name']
        artist_last_name = request.form['artist_last_name']
        album_or_single = request.form.getlist('album_or_single')
        single_ranking = request.form.get('ranking')

        db_file = os.path.join(PARENT_DIR, "artist_management.db")
        # connect to the database
        conn = sqlite3.connect(db_file)

        # create a cursor object
        cursor = conn.cursor()

        # if no last name
        if (artist_last_name == ''):
            if len(album_or_single) == 0:
                # Handle case where no junk food was selected
                message = 'No selection was made. Please choose if you want to see artist albums and/or singles,'
                return render_template('get_discography.html', message=message)
            elif len(album_or_single)==1 and 'album' in album_or_single:
                query = """SELECT artist_first_name || ' ' || artist_last_name AS 'Artist', album_name as "Album", album_release_date AS 'Album Release Date'
                FROM artist
                INNER JOIN album ON album.artist_id = artist.artist_id
                WHERE artist_first_name = ?"""
                album_single_info = pd.read_sql_query(query, conn, params = (artist_first_name,))
                no_singles_to_rank = 'The above single box was not selected, so there are no rankings to display. Edit your form answers to get the ranking of artist singles.'
            elif len(album_or_single)==1 and 'single' in album_or_single:
                if single_ranking == 'no':
                    query = """SELECT artist_first_name || ' ' || artist_last_name AS 'Artist', album_name AS "Album", song_name AS "Singles", single_release AS
                    'Single Release Date'
                    FROM artist
                    INNER JOIN album ON album.artist_id = artist.artist_id
                    LEFT JOIN single ON album.album_id = single.album_id
                    WHERE artist_first_name = ?"""
                    album_single_info = pd.read_sql_query(query, conn, params = (artist_first_name,))
                    no_singles_to_rank = ' '
                else:
                    query = """SELECT artist_first_name || ' ' || artist_last_name AS 'Artist', album_name AS "Album", song_name AS "Singles", single_release AS
                    'Single Release Date', highest_US_ranking AS 'Highest Billboard Ranking'
                    FROM artist
                    INNER JOIN album ON album.artist_id = artist.artist_id
                    LEFT JOIN single ON album.album_id = single.album_id
                    WHERE artist_first_name = ?"""
                    album_single_info = pd.read_sql_query(query, conn, params = (artist_first_name,))
                    no_singles_to_rank = ' '
            else:   
                if single_ranking == 'no':
                    query = """SELECT artist_first_name || ' ' || artist_last_name AS 'Artist', album_name AS "Album", album_release_date AS 'Album Release Date', song_name AS "Singles", single_release AS
                    'Single Release Date'
                    FROM artist
                    INNER JOIN album ON album.artist_id = artist.artist_id
                    LEFT JOIN single ON album.album_id = single.album_id
                    WHERE artist_first_name = ?"""
                    album_single_info = pd.read_sql_query(query, conn, params = (artist_first_name,))
                    no_singles_to_rank = ' '
                else:
                    query = """SELECT artist_first_name || ' ' || artist_last_name AS 'Artist', album_name AS "Album", album_release_date AS 'Album Release Date', song_name AS "Singles", single_release AS
                    'Single Release Date', highest_US_ranking AS 'Highest Billboard Ranking'
                    FROM artist
                    INNER JOIN album ON album.artist_id = artist.artist_id
                    LEFT JOIN single ON album.album_id = single.album_id
                    WHERE artist_first_name = ?"""
                    album_single_info = pd.read_sql_query(query, conn, params = (artist_first_name,))
                    no_singles_to_rank = ' '
        else: # assumes we will ALWAYS have a first name
            # retrieve the artist information from the artist and single and album tables
            if len(album_or_single) == 0:
                # Handle case where no junk food was selected
                message = 'No selection was made. Please choose if you want to see artist albums and/or singles,'
                return render_template('get_discography.html', message=message)
            elif len(album_or_single)==1 and 'album' in album_or_single:
                query = """SELECT artist_first_name || ' ' || artist_last_name AS 'Artist', album_name as "Album", album_release_date AS 'Album Release Date'
                FROM artist
                INNER JOIN album ON album.artist_id = artist.artist_id
                WHERE artist_first_name = ? AND artist_last_name =?"""
                album_single_info = pd.read_sql_query(query, conn, params = (artist_first_name, artist_last_name,))
                no_singles_to_rank = 'The above single box was not selected, so there are no rankings to display. Edit your form answers to get the ranking of artist singles.'
            elif len(album_or_single)==1 and 'single' in album_or_single:
                if single_ranking == 'no':
                    query = """SELECT artist_first_name || ' ' || artist_last_name AS 'Artist', album_name AS "Album", song_name AS "Singles", single_release AS
                    'Single Release Date'
                    FROM artist
                    INNER JOIN album ON album.artist_id = artist.artist_id
                    LEFT JOIN single ON album.album_id = single.album_id
                    WHERE artist_first_name = ? AND artist_last_name =?"""
                    album_single_info = pd.read_sql_query(query, conn, params = (artist_first_name,artist_last_name,))
                    no_singles_to_rank = ' '
                else:
                    query = """SELECT artist_first_name || ' ' || artist_last_name AS 'Artist', album_name AS "Album", song_name AS "Singles", single_release AS
                    'Single Release Date', highest_US_ranking AS 'Highest Billboard Ranking'
                    FROM artist
                    INNER JOIN album ON album.artist_id = artist.artist_id
                    LEFT JOIN single ON album.album_id = single.album_id
                    WHERE artist_first_name = ? AND artist_last_name =?"""
                    album_single_info = pd.read_sql_query(query, conn, params = (artist_first_name,artist_last_name,))
                    no_singles_to_rank = ' '
            else:   
                if single_ranking == 'no':
                    query = """SELECT artist_first_name || ' ' || artist_last_name AS 'Artist', album_name AS "Album",album_release_date AS 'Album Release Date', song_name AS "Singles", single_release AS
                    'Single Release Date'
                    FROM artist
                    INNER JOIN album ON album.artist_id = artist.artist_id
                    LEFT JOIN single ON album.album_id = single.album_id
                    WHERE artist_first_name = ? AND artist_last_name =?"""
                    album_single_info = pd.read_sql_query(query, conn, params = (artist_first_name,artist_last_name,))
                    no_singles_to_rank = ' '
                else:
                    query = """SELECT artist_first_name || ' ' || artist_last_name AS 'Artist', album_name AS "Album", album_release_date AS 'Album Release Date', song_name AS "Singles", single_release AS
                    'Single Release Date', highest_US_ranking AS 'Highest Billboard Ranking'
                    FROM artist
                    INNER JOIN album ON album.artist_id = artist.artist_id
                    LEFT JOIN single ON album.album_id = single.album_id
                    WHERE artist_first_name = ? AND artist_last_name =?"""
                    album_single_info = pd.read_sql_query(query, conn, params = (artist_first_name,artist_last_name,))
                    no_singles_to_rank = ' '

        # close the database connection
        conn.close()

        return render_template('get_discography.html', album_single_info = album_single_info.to_html(index = False),no_singles_to_rank=no_singles_to_rank)
    else:
        return render_template('get_discography.html')
    
@app.route('/artist_album_chart', methods=['GET', 'POST'])
def artist_album_chart():
    if request.method == 'POST':
        # Establish a connection to the SQLite database
        conn = sqlite3.connect(os.path.join(PARENT_DIR, "artist_management.db"))

        # Create a cursor object to execute SQL queries
        cursor = conn.cursor()

        # Execute the SQL query to retrieve customer gender counts
        cursor.execute("SELECT artist_first_name || ' '|| artist_last_name AS 'Artist', number_of_albums FROM artist GROUP BY artist_first_name")
        rows = cursor.fetchall()

        # Close the cursor and the database connection
        cursor.close()
        conn.close()

        # Extract the data from the retrieved rows
        artists = []
        albums = []

        for row in rows:
            artists.append(row[0])
            albums.append(row[1])

        # Set the bar width
        bar_width = 0.35

        # Create a figure with a specified height
        plt.subplots(figsize=(8, 6))     

        # Create an array of indices for the x-axis
        x = list(range(len(artists)))
        y = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)

        # Plotting the bar chart for product inventory
        plt.bar(x, albums, width=bar_width, label='Number of Albums per Artist', color='#0481aa')
        plt.gcf().set_facecolor('#0481aa')

        # Adding labels and title
        plt.xlabel('Artist', fontsize=8, color = '#ffffff')
        plt.ylabel('No. of Albums', color = '#ffffff')
        plt.title('Artist v Album Distribution', color = '#ffffff')

        # Set the x-axis tick positions and label
        plt.xticks(x, artists, color = '#ffffff')
        plt.yticks(y, color = '#ffffff' )
        plt.xticks(rotation=90)
        plt.tick_params(axis='x', color='#ffffff')
        plt.gcf().subplots_adjust(bottom=0.30)
        plt.tick_params(axis='y', which='major', pad=10, color='#ffffff')

        # Save the chart image to a buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=250)
        buffer.seek(0)

        # Convert the image buffer to base64 string
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Generate the chart image URL
        chart_image = f"data:image/png;base64,{image_base64}"

        # Render the template with the chart image URL
        return render_template('artist_album_chart.html', chart_image=chart_image)

    # Render the template with the initial form
    return render_template('artist_album_chart.html')

@app.route('/artist_grammys', methods=['GET', 'POST'])
def artist_grammys():
    if request.method == 'POST':
        # Establish a connection to the SQLite database
        conn = sqlite3.connect(os.path.join(PARENT_DIR, "artist_management.db"))

        # Create a cursor object to execute SQL queries
        cursor = conn.cursor()

        # Execute the SQL query to retrieve customer gender counts
        cursor.execute("SELECT number_of_grammys_won AS 'Grammys', artist_first_name || ' ' || artist_last_name || ' (' || number_of_grammys_won || ')' as Artist\
                FROM artist WHERE number_of_grammys_won >0")
        rows = cursor.fetchall()

        # Close the cursor and the database connection
        cursor.close()
        conn.close()

        # Extract the data from the retrieved rows
        artist = []
        grammys = []

        for row in rows:
            grammys.append(int(row[0]))
            artist.append(row[1])

        # Set the figure size
        plt.figure(figsize=(7, 7.5))  

        # Create pie chart
        plt.pie(grammys, labels = artist, startangle = 90,rotatelabels=True,labeldistance=1.05, autopct='%1.1f%%')


        plt.legend(loc='lower right', bbox_to_anchor=(1.1, 0.05))

        # Save the chart image to a buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        # Convert the image buffer to base64 string
        image_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Generate the chart image URL
        chart_image1 = f"data:image/png;base64,{image_base64}"

        # Render the template with the chart image URL
        return render_template('artist_grammys.html',chart_image1=chart_image1)

    # Render the template with the initial form
    return render_template('artist_grammys.html')
    
if __name__ == '__main__':
    app.run(debug=True)
