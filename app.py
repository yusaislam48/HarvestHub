from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
import mysql.connector
from config import DB_CONFIG  # Your MySQL credentials from config.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, HRFlowable, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

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


## generate report start
@app.route('/generate_report', methods=['GET'])
def generate_report():
    farmer_id = request.args.get('farmer_id')
    harvest_id = request.args.get('harvest_id')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Fetch Farmer Details
    cursor.execute("""
        SELECT f.*, r.region_name
        FROM farmers f
        LEFT JOIN region r ON f.region_id = r.id
        WHERE f.id = %s
    """, (farmer_id,))
    farmer = cursor.fetchone()
    if not farmer:
        return "Error: Farmer not found.", 404

    # Fetch Harvest Details
    cursor.execute("SELECT * FROM harvest_details WHERE id = %s AND farmer_id = %s", (harvest_id, farmer_id))
    harvest = cursor.fetchone()
    if not harvest:
        return "Error: Harvest details not found.", 404

    # Fetch Officer Details
    cursor.execute("""
        SELECT ao.name AS officer_name, ao.region
        FROM area_officers ao
        WHERE ao.region = %s
    """, (farmer['region_id'],))
    officer = cursor.fetchone()
    if not officer:
        officer = {'officer_name': 'Unknown', 'region': farmer['region_name']}

    # Fetch Stage Data
    cursor.execute("""
        SELECT 
            COALESCE(hs.loss_amount, 0) AS harvesting_loss,
            COALESCE(hs.loss_percentage, 0) AS harvesting_percentage,
            COALESCE(hs.loss_reason, 'N/A') AS harvesting_reason,
            COALESCE(ss.loss_amount, 0) AS storage_loss,
            COALESCE(ss.loss_percentage, 0) AS storage_percentage,
            COALESCE(ss.loss_reason, 'N/A') AS storage_reason,
            COALESCE(hnd.loss_amount, 0) AS handling_loss,
            COALESCE(hnd.loss_percentage, 0) AS handling_percentage,
            COALESCE(hnd.loss_reason, 'N/A') AS handling_reason,
            COALESCE(ts.loss_amount, 0) AS transport_loss,
            COALESCE(ts.loss_percentage, 0) AS transport_percentage,
            COALESCE(ts.loss_reason, 'N/A') AS transport_reason,
            h.amount AS total_harvested,
            COALESCE(ts.remaining_amount, ss.remaining_amount, hnd.remaining_amount, hs.remaining_amount, 0) AS total_remaining
        FROM harvest_details h
        LEFT JOIN harvesting_stage hs ON h.id = hs.harvest_id AND h.farmer_id = hs.farmer_id
        LEFT JOIN storage_stage ss ON h.id = ss.harvest_id AND h.farmer_id = ss.farmer_id
        LEFT JOIN handling_stage hnd ON h.id = hnd.harvest_id AND h.farmer_id = hnd.farmer_id
        LEFT JOIN transportation_stage ts ON h.id = ts.harvest_id AND h.farmer_id = ts.farmer_id
        WHERE h.farmer_id = %s AND h.id = %s
    """, (farmer_id, harvest_id))
    stage_data = cursor.fetchone()
    if not stage_data:
        return "Error: Stage data not found.", 404
    
    # Fetch Officer Details
    cursor.execute("""
        SELECT ao.name AS officer_name, ao.region AS officer_region
        FROM area_officers ao
        JOIN region r ON ao.region = r.region_name
        JOIN farmers f ON f.region_id = r.id
        WHERE f.id = %s
    """, (farmer_id,))
    officer = cursor.fetchone()
    if not officer:
        officer = {'officer_name': 'Unknown', 'officer_region': farmer['region_name']}


    total_loss = float(stage_data['total_harvested']) - float(stage_data['total_remaining'])
    overall_loss_percentage = (total_loss / float(stage_data['total_harvested'])) * 100 if stage_data['total_harvested'] else 0

    cursor.close()
    db.close()

    # Generate PDF
    pdf_buffer = BytesIO()
    pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']

    # Title
    elements.append(Paragraph("Farmer Harvest Report", title_style))
    elements.append(Paragraph("<br/><br/>", normal_style))
    
    # Farmer Details
    elements.append(Paragraph("<b>Farmer Details:</b>", normal_style))
    farmer_details = [
        ["Name:", farmer['name']],
        ["Phone:", farmer['phone']],
        ["Address:", farmer['address']],
        ["Region:", farmer['region_name']],
    ]
    elements.append(Table(farmer_details, style=[  
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(Paragraph("<br/><br/>", normal_style))
    
    # Officer Details
    elements.append(Paragraph("<b>Managing Officer:</b> ", normal_style))
    officer_details = [
        ["Officer Name:", officer['officer_name']],
        ["Region:", officer['officer_region']],
    ]
    elements.append(Table(officer_details, style=[
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(Paragraph("<br/><br/>", normal_style))

    # Harvest Details
    elements.append(Paragraph("<b>Harvest Details:</b>  <br/><br/>", normal_style))
    harvest_details = [
        ["Harvest ID:", harvest['id']],
        ["Crop Type:", harvest['crop_type']],
        ["Season:", harvest['season']],
        ["Harvest Date:", harvest['harvest_date']],
        ["Amount Harvested:", f"{harvest['amount']} kg"],
    ]
    elements.append(Table(harvest_details, style=[
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(Paragraph("<br/><br/>", normal_style))
    

    # Stage Data
    elements.append(Paragraph("<b>Stage-Wise Loss Data:</b> <br/><br/>", normal_style))
    
    stage_table = [
        ["Stage", "Loss Amount (kg)", "Loss Percentage (%)", "Loss Reason"],
        ["Harvesting", stage_data['harvesting_loss'], stage_data['harvesting_percentage'], stage_data['harvesting_reason']],
        ["Storage", stage_data['storage_loss'], stage_data['storage_percentage'], stage_data['storage_reason']],
        ["Handling", stage_data['handling_loss'], stage_data['handling_percentage'], stage_data['handling_reason']],
        ["Transportation", stage_data['transport_loss'], stage_data['transport_percentage'], stage_data['transport_reason']],
    ]
    elements.append(Table(stage_table, style=[
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(Paragraph("<br/><br/>", normal_style))
    

    # Summary Data
    elements.append(Paragraph("<b>Summary:</b> ", normal_style))
    summary_data = [
        ["Total Harvested Amount:", f"{stage_data['total_harvested']} kg"],
        ["Total Loss Across All Stages:", f"{total_loss:.2f} kg"],
        ["Total Remaining Amount (Calculated):", f"{stage_data['total_remaining']} kg"],
        ["Overall Loss Percentage (Calculated):", f"{overall_loss_percentage:.2f}%"],
    ]
    elements.append(Table(summary_data, style=[    
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightcoral),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(Paragraph("<br/><br/>", normal_style))

    # Add a horizontal line
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black))

    # Add a closing note
    elements.append(Paragraph(
        "This is an auto-generated report. No signature is required.",
        normal_style
    ))

    # Build PDF
    pdf.build(elements)
    pdf_buffer.seek(0)

    # Return PDF response
    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=farmer_report.pdf'

    pdf_buffer.close()
    return response

## generate report end

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
