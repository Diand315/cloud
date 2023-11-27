from flask import Flask, render_template, request, session
import mysql.connector
from azure.storage.blob import BlobServiceClient
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

app.secret_key = os.urandom(24)

# Azure MySQL connection settings
mysql_config = {
    'host': 'rockdatabase.mysql.database.azure.com',
    'user': 'grouprock',
    'password': 'Chan911208!',
    'database': 'database'
}

# Azure Storage Blob connection string
blob_connection_string = "DefaultEndpointsProtocol=https;AccountName=gorupcloudblob;AccountKey=LKS0W4wrygKihDYHP8kpERaHcsyF8WYUM78JdvsmodZH5FJ5ddufLZtkh59NOYqYvSPDJL9A99B6+AStuYnFCA==;EndpointSuffix=core.windows.net"
# Create BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)


# Create database connection
conn = mysql.connector.connect(**mysql_config)

# Verify user
def authenticate(username, password):
    cursor = conn.cursor()
    select_query = "SELECT role, nickname FROM users WHERE username = %s AND password = %s"
    data = (username, password)
    cursor.execute(select_query, data)
    result = cursor.fetchone()
    cursor.close()
    if result:
        role = result[0]
        nickname = result[1]
        return role, nickname
    else:
        return None

# adduser
def add_user(username, password, role, nicknme):
    cursor = conn.cursor()
    insert_query = "INSERT INTO users (username, password, role, nickname) VALUES (%s, %s, %s, %s)"
    data = (username, password, role, nicknme)
    cursor.execute(insert_query, data)
    conn.commit()

# Delete Account
def delete_user(id):
    cursor = conn.cursor()
    delete_query = """DELETE FROM users WHERE id = %s """
    data = id
    cursor.execute(delete_query, (data,))
    conn.commit()

# Login interface
@app.route('/', methods=['GET', 'POST'])
def home():
    # Azure Storage Blob connection string
    blob_connection_string = "DefaultEndpointsProtocol=https;AccountName=gorupcloudblob;AccountKey=LKS0W4wrygKihDYHP8kpERaHcsyF8WYUM78JdvsmodZH5FJ5ddufLZtkh59NOYqYvSPDJL9A99B6+AStuYnFCA==;EndpointSuffix=core.windows.net"
    # Create BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_name = "file"
     # Get a reference to the container
    container_client = blob_service_client.get_container_client(container_name)

    # List all blobs in the container
    blobs = container_client.list_blobs()

    # MySQL query to retrieve file information
    cursor = conn.cursor()
    select_query = "SELECT file_name, nickname, date, title, description FROM files"
    cursor.execute(select_query)
    files = cursor.fetchall()

    # Create a dictionary to map file names with blob URLs
    file_mapping = {}
    for blob in blobs:
        for file_data in files:
            if file_data[0] == blob.name:
                blob_client = container_client.get_blob_client(blob)
                file_mapping[file_data[0]] = blob_client.url
                break

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = authenticate(username, password)

        if role:
            role, nickname = role
            session['username'] = username
            session['role'] = role
            session['nickname'] = nickname
            if role == 'admin':
                return render_template('adminhome.html')
            elif role == 'teacher':
                return render_template('teacherhome.html')
        else:
            return render_template('home.html', error='Invalid username or password', file_mapping=file_mapping, files=files)

    return render_template('home.html', file_mapping=file_mapping, files=files)

@app.route('/search.html', methods=['GET', 'POST'])
def search_page():
    if request.method == 'POST':
        search_name = request.form.get('searchname')

        # MySQL query to retrieve matching file information
        cursor = conn.cursor()
        select_query = "SELECT nickname, DATE_FORMAT(date, '%Y-%m-%d'), title, description, file_name FROM files WHERE nickname LIKE %s OR title LIKE %s OR description LIKE %s"
        cursor.execute(select_query, ('%'+search_name+'%', '%'+search_name+'%', '%'+search_name+'%'))
        results = cursor.fetchall()
        cursor.close()

        # Azure Storage Blob connection string
        blob_connection_string = "DefaultEndpointsProtocol=https;AccountName=gorupcloudblob;AccountKey=LKS0W4wrygKihDYHP8kpERaHcsyF8WYUM78JdvsmodZH5FJ5ddufLZtkh59NOYqYvSPDJL9A99B6+AStuYnFCA==;EndpointSuffix=core.windows.net"
        # Create BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
        container_name = "file"

        # Get a reference to the container
        container_client = blob_service_client.get_container_client(container_name)

        # Create a list to store the final result
        final_results = []

        # Iterate over the MySQL results
        for result in results:
            nickname = result[0]
            date = result[1]
            title = result[2]
            description = result[3]
            file_name = result[4]

            # Get the Blob URL based on the file name
            blob_client = container_client.get_blob_client(file_name)
            blob_url = blob_client.url

            # Create a dictionary with MySQL and Blob information
            file_info = {
                "nickname": nickname,
                "date": date,
                "title": title,
                "description": description,
                "blob_url": blob_url
            }

            # Add the dictionary to the final results list
            final_results.append(file_info)

        if 'username' in session and 'password' in session:
            username = session['username']
            password = session['password']
            role = authenticate(username, password)

            if role:
                role, nickname = role
                session['username'] = username
                session['role'] = role
                session['nickname'] = nickname

                if role == 'admin':
                    return render_template('adminhome.html')
                elif role == 'teacher':
                    return render_template('teacherhome.html')

        return render_template('search.html', final_results=final_results)
    else:
        return render_template('search.html')
    
# home page
@app.route('/home.html')
def home_page():
    # Azure Storage Blob connection string
    blob_connection_string = "DefaultEndpointsProtocol=https;AccountName=gorupcloudblob;AccountKey=LKS0W4wrygKihDYHP8kpERaHcsyF8WYUM78JdvsmodZH5FJ5ddufLZtkh59NOYqYvSPDJL9A99B6+AStuYnFCA==;EndpointSuffix=core.windows.net"
    # Create BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_name = "file"

    # Get a reference to the container
    container_client = blob_service_client.get_container_client(container_name)

    # List all blobs in the container
    blobs = container_client.list_blobs()

    # MySQL query to retrieve file information
    cursor = conn.cursor()
    select_query = "SELECT file_name, nickname, date, title, description FROM files"
    cursor.execute(select_query)
    files = cursor.fetchall()
    cursor.close()

    # Create a dictionary to map file names with blob URLs
    file_mapping = {}
    for blob in blobs:
        for file_data in files:
            if file_data[0] == blob.name:
                blob_client = container_client.get_blob_client(blob)
                file_mapping[file_data[0]] = blob_client.url
                break

    return render_template('home.html', file_mapping=file_mapping, files=files)

# admin page
@app.route('/adminhome.html')
def adminhome_page():
    # Azure Storage Blob connection string
    blob_connection_string = "DefaultEndpointsProtocol=https;AccountName=gorupcloudblob;AccountKey=LKS0W4wrygKihDYHP8kpERaHcsyF8WYUM78JdvsmodZH5FJ5ddufLZtkh59NOYqYvSPDJL9A99B6+AStuYnFCA==;EndpointSuffix=core.windows.net"
    # Create BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_name = "file"

    # Get a reference to the container
    container_client = blob_service_client.get_container_client(container_name)

    # List all blobs in the container
    blobs = container_client.list_blobs()

    # MySQL query to retrieve file information
    cursor = conn.cursor()
    select_query = "SELECT file_name, nickname, date, title, description FROM files"
    cursor.execute(select_query)
    files = cursor.fetchall()
    cursor.close()

    # Create a dictionary to map file names with blob URLs
    file_mapping = {}
    for blob in blobs:
        for file_data in files:
            if file_data[0] == blob.name:
                blob_client = container_client.get_blob_client(blob)
                file_mapping[file_data[0]] = blob_client.url
                break

    return render_template('adminhome.html', file_mapping=file_mapping, files=files)


@app.route('/adminsearch.html', methods=['GET', 'POST'])
def adminsearch_page():
    if request.method == 'POST':
        search_name = request.form.get('searchname')

        # MySQL query to retrieve matching file information
        cursor = conn.cursor()
        select_query = "SELECT nickname, DATE_FORMAT(date, '%Y-%m-%d'), title, description, file_name FROM files WHERE nickname LIKE %s OR title LIKE %s OR description LIKE %s"
        cursor.execute(select_query, ('%'+search_name+'%', '%'+search_name+'%', '%'+search_name+'%'))
        results = cursor.fetchall()
        cursor.close()

        # Azure Storage Blob connection string
        blob_connection_string = "DefaultEndpointsProtocol=https;AccountName=gorupcloudblob;AccountKey=LKS0W4wrygKihDYHP8kpERaHcsyF8WYUM78JdvsmodZH5FJ5ddufLZtkh59NOYqYvSPDJL9A99B6+AStuYnFCA==;EndpointSuffix=core.windows.net"
        # Create BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
        container_name = "file"

        # Get a reference to the container
        container_client = blob_service_client.get_container_client(container_name)

        # Create a list to store the final result
        final_results = []

        # Iterate over the MySQL results
        for result in results:
            nickname = result[0]
            date = result[1]
            title = result[2]
            description = result[3]
            file_name = result[4]

            # Get the Blob URL based on the file name
            blob_client = container_client.get_blob_client(file_name)
            blob_url = blob_client.url

            # Create a dictionary with MySQL and Blob information
            file_info = {
                "nickname": nickname,
                "date": date,
                "title": title,
                "description": description,
                "blob_url": blob_url
            }

            # Add the dictionary to the final results list
            final_results.append(file_info)

        return render_template('adminsearch.html', final_results=final_results)
    else:
        return render_template('adminsearch.html')

@app.route('/adminuploaddate.html', methods=['GET', 'POST'])
def adminuploaddate_page():

    cursor = conn.cursor()
    # Azure Storage Blob connection string
    blob_connection_string = "DefaultEndpointsProtocol=https;AccountName=gorupcloudblob;AccountKey=LKS0W4wrygKihDYHP8kpERaHcsyF8WYUM78JdvsmodZH5FJ5ddufLZtkh59NOYqYvSPDJL9A99B6+AStuYnFCA==;EndpointSuffix=core.windows.net"
    # Create BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_name = "file"

    nickname = session.get('nickname')
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        file = request.files.get('file')

        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        blob_name = secure_filename(file.filename)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(file, overwrite=True)

        insert_query = "INSERT INTO files (file_name, title, description, date, nickname) VALUES (%s, %s, %s, %s, %s)"
        insert_values = (file.filename, title, description, current_date, nickname)
        cursor.execute(insert_query, insert_values)
        conn.commit()

        return render_template('adminuploaddate.html')

    return render_template('adminuploaddate.html')

@app.route('/adminregister.html', methods=['GET', 'POST'])
def adminregister_page():
    # Get the account list
    cursor = conn.cursor()
    select_query = "SELECT username, password, nickname, role, id FROM users"
    cursor.execute(select_query)
    users = cursor.fetchall()

    # Account
    if request.method == 'POST':
        # Register Account
        if 'Register' in request.form:
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']
            nickname = request.form['nickname']
            add_user(username, password, role, nickname)

        cursor.close()
    return render_template('adminregister.html', users=users)

# Delete Account
@app.route('/delete_user', methods=['POST'])
def delete_user():
    # Get the account list
    cursor = conn.cursor()
    select_query = "SELECT username, password, nickname, role, id FROM users"
    cursor.execute(select_query)
    users = cursor.fetchall()
    
    # Get selected user ID
    id = request.form['id']

    # Execute delete query
    cursor = conn.cursor()
    delete_query = "DELETE FROM users WHERE id = %s"
    cursor.execute(delete_query, (id,))

    # Commit changes
    conn.commit()

     # Return to admin page with updated account list
    return render_template('adminregister.html', users=users)

# teacher page
@app.route('/teacherhome.html')
def teacherhome_page():
        # Azure Storage Blob connection string
    blob_connection_string = "DefaultEndpointsProtocol=https;AccountName=gorupcloudblob;AccountKey=LKS0W4wrygKihDYHP8kpERaHcsyF8WYUM78JdvsmodZH5FJ5ddufLZtkh59NOYqYvSPDJL9A99B6+AStuYnFCA==;EndpointSuffix=core.windows.net"
    # Create BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_name = "file"

    # Get a reference to the container
    container_client = blob_service_client.get_container_client(container_name)

    # List all blobs in the container
    blobs = container_client.list_blobs()

    # MySQL query to retrieve file information
    cursor = conn.cursor()
    select_query = "SELECT file_name, nickname, date, title, description FROM files"
    cursor.execute(select_query)
    files = cursor.fetchall()
    cursor.close()

    # Create a dictionary to map file names with blob URLs
    file_mapping = {}
    for blob in blobs:
        for file_data in files:
            if file_data[0] == blob.name:
                blob_client = container_client.get_blob_client(blob)
                file_mapping[file_data[0]] = blob_client.url
                break

    return render_template('teacherhome.html', file_mapping=file_mapping, files=files)

@app.route('/teachersearch.html', methods=['GET', 'POST'])
def teachersearch_page():
    if request.method == 'POST':
        search_name = request.form.get('searchname')

        # MySQL query to retrieve matching file information
        cursor = conn.cursor()
        select_query = "SELECT nickname, DATE_FORMAT(date, '%Y-%m-%d'), title, description, file_name FROM files WHERE nickname LIKE %s OR title LIKE %s OR description LIKE %s"
        cursor.execute(select_query, ('%'+search_name+'%', '%'+search_name+'%', '%'+search_name+'%'))
        results = cursor.fetchall()
        cursor.close()

        # Azure Storage Blob connection string
        blob_connection_string = "DefaultEndpointsProtocol=https;AccountName=gorupcloudblob;AccountKey=LKS0W4wrygKihDYHP8kpERaHcsyF8WYUM78JdvsmodZH5FJ5ddufLZtkh59NOYqYvSPDJL9A99B6+AStuYnFCA==;EndpointSuffix=core.windows.net"
        # Create BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
        container_name = "file"

        # Get a reference to the container
        container_client = blob_service_client.get_container_client(container_name)

        # Create a list to store the final result
        final_results = []

        # Iterate over the MySQL results
        for result in results:
            nickname = result[0]
            date = result[1]
            title = result[2]
            description = result[3]
            file_name = result[4]

            # Get the Blob URL based on the file name
            blob_client = container_client.get_blob_client(file_name)
            blob_url = blob_client.url

            # Create a dictionary with MySQL and Blob information
            file_info = {
                "nickname": nickname,
                "date": date,
                "title": title,
                "description": description,
                "blob_url": blob_url
            }

            # Add the dictionary to the final results list
            final_results.append(file_info)

        return render_template('teachersearch.html', final_results=final_results)
    else:
        return render_template('teachersearch.html')
    
@app.route('/teacheruploaddate.html', methods=['GET', 'POST'])
def teacheruploaddate_page():

    cursor = conn.cursor()
    # Azure Storage Blob connection string
    blob_connection_string = "DefaultEndpointsProtocol=https;AccountName=gorupcloudblob;AccountKey=LKS0W4wrygKihDYHP8kpERaHcsyF8WYUM78JdvsmodZH5FJ5ddufLZtkh59NOYqYvSPDJL9A99B6+AStuYnFCA==;EndpointSuffix=core.windows.net"
    # Create BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_name = "file"

    nickname = session.get('nickname')
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        file = request.files.get('file')

        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        blob_name = secure_filename(file.filename)
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(file, overwrite=True)

        insert_query = "INSERT INTO files (file_name, title, description, date, nickname) VALUES (%s, %s, %s, %s, %s)"
        insert_values = (file.filename, title, description, current_date, nickname)
        cursor.execute(insert_query, insert_values)
        conn.commit()

        return render_template('teacheruploaddate.html')

    return render_template('teacheruploaddate.html')



if __name__ == '__main__':
    app.debug = True
    app.run()