from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from config import DB_CONFIG  # Your MySQL credentials from config.py

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random string for production use

# Database connection function
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Route: Home/Login Page
@app.route('/')
def login():
    return render_template('login.html')

# Route: Handle Login
@app.route('/login', methods=['POST'])
def handle_login():
    email = request.form['email']
    password = request.form['password']

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM area_officers WHERE email = %s AND password = %s", (email, password))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if user:
        session['user_id'] = user['id']
        session['name'] = user['name']
        return redirect(url_for('profile'))
    return 'Invalid credentials, please try again.'

# Route: Profile Page
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch Area Officer's Data
    cursor.execute("SELECT * FROM area_officers WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()

    # Debug: Print user's region
    print("Area Officer Region:", user['region'])

    # Calculate Total Farmers in the Area Officer's Region
    cursor.execute("""
        SELECT COUNT(*) AS total_farmers
        FROM farmers
        JOIN region ON farmers.region_id = region.id
        WHERE region.region_name = %s
    """, (user['region'],))
    total_farmers = cursor.fetchone()['total_farmers']

    # Debug: Print total farmers result
    print("Total Farmers Count:", total_farmers)

    cursor.close()
    db.close()

    # Add Total Farmers to User Dictionary
    user['total_farmers'] = total_farmers

    return render_template('areaOfficersProfile.html', user=user)

# Route: Add New Farmer Page
@app.route('/add_new_farmer', methods=['GET', 'POST'])
def add_new_farmer():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch regions for the dropdown
    cursor.execute("SELECT id, region_name FROM region")
    regions = cursor.fetchall()

    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        # farm_id = request.form['farm_id']
        location = request.form['location']  # Region ID from dropdown
        area = request.form['area']

        # Insert data into the database (no farmer_id field)
        cursor.execute("""
            INSERT INTO farmers (name, phone, address, region_id, area)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, phone, address, location, area))
        db.commit()

        cursor.close()
        db.close()

        # Redirect to Harvesting Details
        return redirect(url_for('harvesting_details'))

    cursor.close()
    db.close()

    return render_template('addNewFarmer.html', regions=regions)




# Route: Harvesting Details Page
@app.route('/harvesting_details', methods=['GET', 'POST'])
def harvesting_details():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch farmers for the dropdown
    cursor.execute("SELECT id, name FROM farmers")
    farmers = cursor.fetchall()

    # Fetch crops for the dropdown
    cursor.execute("SELECT crop_id, crop_name FROM crops")
    crops = cursor.fetchall()

    # Fetch seasons for the dropdown
    cursor.execute("SELECT id, season_name FROM seasons")
    seasons = cursor.fetchall()

    if request.method == 'POST':
        # Get form data
        farmer_id = request.form['farmer_id']
        harvest_id = request.form['harvest_id']
        amount = request.form['amount']
        crop_type = request.form['crop_type']
        crop_id = request.form['crop_id']
        season = request.form['season']
        harvest_date = request.form['harvest_date']

        # Insert into the database
        cursor.execute("""
            INSERT INTO harvest_details (farmer_id, harvest_id, amount, crop_type, crop_id, season, harvest_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (farmer_id, harvest_id, amount, crop_type, crop_id, season, harvest_date))
        db.commit()

        # Redirect to the Profile Page
        cursor.close()
        db.close()
        return redirect(url_for('profile'))

    cursor.close()
    db.close()

    return render_template('harvestingDetails.html', farmers=farmers, crops=crops, seasons=seasons)


# Route: Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Error Handler: 404 Page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
