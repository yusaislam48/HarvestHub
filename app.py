from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import mysql.connector
from config import DB_CONFIG  # Your MySQL credentials from config.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

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


# Route: Loss Record Page
@app.route('/loss_record', methods=['GET', 'POST'])
def loss_record():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch all farmers for the dropdown
    cursor.execute("SELECT id, name FROM farmers")
    farmers = cursor.fetchall()

    if request.method == 'POST':
        # Get form data
        farmer_id = request.form['farmer_id']
        harvest_id = request.form['harvest_id']
        stage = request.form['stage']
        initial_amount = float(request.form['initial_amount'])
        remaining_amount = float(request.form['remaining_amount'])
        loss_amount = initial_amount - remaining_amount
        loss_percentage = (loss_amount / initial_amount) * 100
        loss_reason = request.form['loss_reason']  # New loss reason field

        # Determine the table and data insertion logic based on the stage
        if stage == 'Harvesting':
            table = 'harvesting_stage'
        elif stage == 'Handling':
            table = 'handling_stage'
        elif stage == 'Storage':
            table = 'storage_stage'
        elif stage == 'Transportation':
            table = 'transportation_stage'
        else:
            table = None

        # Check if the record already exists
        if table:
            cursor.execute(f"""
                SELECT * FROM {table} 
                WHERE farmer_id = %s AND harvest_id = %s
            """, (farmer_id, harvest_id))
            existing_record = cursor.fetchone()

            if existing_record:
                # Redirect with a message indicating the record already exists
                cursor.close()
                db.close()
                return 'Data for this stage already exists. Please update it instead of re-entering.', 400

            # Insert into the relevant table
            cursor.execute(f"""
                INSERT INTO {table} 
                (farmer_id, harvest_id, initial_amount, remaining_amount, loss_amount, loss_percentage, loss_reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (farmer_id, harvest_id, initial_amount, remaining_amount, loss_amount, loss_percentage, loss_reason))
            db.commit()

        cursor.close()
        db.close()

        # Redirect to the loss record page
        return redirect(url_for('loss_record'))

    cursor.close()
    db.close()

    return render_template('lossRecord.html', farmers=farmers)


@app.route('/get_harvest_ids/<int:farmer_id>')
def get_harvest_ids(farmer_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch all harvest IDs for the selected farmer
    cursor.execute("SELECT id FROM harvest_details WHERE farmer_id = %s", (farmer_id,))
    harvest_ids = cursor.fetchall()

    cursor.close()
    db.close()
    return jsonify(harvest_ids)

@app.route('/get_initial_amount', methods=['POST'])
def get_initial_amount():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch the request data
    data = request.json
    farmer_id = data['farmer_id']
    harvest_id = data['harvest_id']
    stage = data['stage']

    try:
        if stage == 'Harvesting':
            # Fetch initial amount for Harvesting stage
            cursor.execute("""
                SELECT amount AS initial_amount
                FROM harvest_details
                WHERE farmer_id = %s AND id = %s
            """, (farmer_id, harvest_id))
        else:
            # Fetch remaining amount from the previous stage
            prev_stage = {
                'Handling': 'harvesting_stage',
                'Storage': 'handling_stage',
                'Transportation': 'storage_stage'
            }.get(stage)

            if prev_stage:
                cursor.execute(f"""
                    SELECT remaining_amount AS initial_amount
                    FROM {prev_stage}
                    WHERE farmer_id = %s AND harvest_id = %s
                """, (farmer_id, harvest_id))
            else:
                initial_amount = None

        initial_amount = cursor.fetchone()

        if initial_amount:
            return jsonify(initial_amount)
        else:
            return jsonify({'initial_amount': None}), 404
    except Exception as e:
        print("Error fetching initial amount:", e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        db.close()



@app.route('/analytics_and_reports', methods=['GET'])
def analytics_and_reports():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch all farmers for the dropdown
    cursor.execute("SELECT id, name FROM farmers")
    farmers = cursor.fetchall()

    cursor.close()
    db.close()

    # Render the Analytics & Reports page with the list of farmers
    return render_template('analyticsAndReports.html', farmers=farmers)
@app.route('/get_loss_data', methods=['POST'])
def get_loss_data():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        data = request.json
        farmer_id = data['farmer_id']
        harvest_id = data['harvest_id']

        # Fetch loss data with priority for remaining_amount
        cursor.execute("""
            SELECT 
                h.amount AS total_harvested,
                COALESCE(ts.remaining_amount, 
                    s.remaining_amount, 
                    hnd.remaining_amount, 
                    hs.remaining_amount, 
                    0) AS total_remaining, -- Priority: transportation > storage > handling > harvesting
                COALESCE(hs.loss_percentage, 0) AS harvesting_loss,
                COALESCE(s.loss_percentage, 0) AS storage_loss,
                COALESCE(hnd.loss_percentage, 0) AS handling_loss,
                COALESCE(ts.loss_percentage, 0) AS transport_loss
            FROM harvest_details h
            LEFT JOIN transportation_stage ts ON h.id = ts.harvest_id AND h.farmer_id = ts.farmer_id
            LEFT JOIN storage_stage s ON h.id = s.harvest_id AND h.farmer_id = s.farmer_id
            LEFT JOIN handling_stage hnd ON h.id = hnd.harvest_id AND h.farmer_id = hnd.farmer_id
            LEFT JOIN harvesting_stage hs ON h.id = hs.harvest_id AND h.farmer_id = hs.farmer_id
            WHERE h.farmer_id = %s AND h.id = %s
        """, (farmer_id, harvest_id))

        result = cursor.fetchone()

        if not result:
            result = {
                'total_harvested': 0,
                'total_remaining': 0,
                'harvesting_loss': 0,
                'storage_loss': 0,
                'handling_loss': 0,
                'transport_loss': 0
            }

        total_harvested = float(result['total_harvested'] or 0)
        total_remaining = float(result['total_remaining'] or 0)
        total_loss = total_harvested - total_remaining

        result.update({
            'total_loss': total_loss
        })

        return jsonify(result)

    except Exception as e:
        print("Error in /get_loss_data:", str(e))
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        db.close()




@app.route('/generate_report', methods=['GET'])
def generate_report():
    farmer_id = request.args.get('farmer_id')
    harvest_id = request.args.get('harvest_id')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch Farmer Details
    cursor.execute("SELECT * FROM farmers WHERE id = %s", (farmer_id,))
    farmer = cursor.fetchone()

    # Fetch Harvest Details
    cursor.execute("SELECT * FROM harvest_details WHERE id = %s AND farmer_id = %s", (harvest_id, farmer_id))
    harvest = cursor.fetchone()

    # Fetch Stage Data
    cursor.execute("""
        SELECT 
            COALESCE(hs.loss_amount, 0) AS harvesting_loss,
            COALESCE(ss.loss_amount, 0) AS storage_loss,
            COALESCE(hnd.loss_amount, 0) AS handling_loss,
            COALESCE(ts.loss_amount, 0) AS transport_loss
        FROM harvest_details h
        LEFT JOIN harvesting_stage hs ON h.id = hs.harvest_id AND h.farmer_id = hs.farmer_id
        LEFT JOIN storage_stage ss ON h.id = ss.harvest_id AND h.farmer_id = ss.farmer_id
        LEFT JOIN handling_stage hnd ON h.id = hnd.harvest_id AND h.farmer_id = hnd.farmer_id
        LEFT JOIN transportation_stage ts ON h.id = ts.harvest_id AND h.farmer_id = ts.farmer_id
        WHERE h.farmer_id = %s AND h.id = %s
    """, (farmer_id, harvest_id))
    stage_data = cursor.fetchone()

    cursor.close()
    db.close()

    # Generate PDF in memory
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.drawString(100, 750, "Farmer Report")
    c.drawString(100, 730, f"Farmer Name: {farmer['name']}")
    c.drawString(100, 710, f"Harvest ID: {harvest['id']}")
    c.drawString(100, 690, f"Harvesting Loss: {stage_data['harvesting_loss']} kg")
    c.drawString(100, 670, f"Storage Loss: {stage_data['storage_loss']} kg")
    c.drawString(100, 650, f"Handling Loss: {stage_data['handling_loss']} kg")
    c.drawString(100, 630, f"Transport Loss: {stage_data['transport_loss']} kg")
    c.save()

    # Set the buffer's position to the beginning
    pdf_buffer.seek(0)

    # Create a Flask response with the PDF
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=report.pdf'

    pdf_buffer.close()
    return response


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
