from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "urielangpo"

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root0316'
app.config['MYSQL_DB'] = 'db_authen'
mysql = MySQL(app)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #hashed_password = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        try:
            # Insert the user's credentials into the users table
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            mysql.connection.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        finally:
            cursor.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Query the database for matching username and password
        cursor = mysql.connection.cursor()
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()  # Fetch the user if a match is found
        cursor.close()

        if user:
            session['username'] = user[1]
            session['password'] = user[2]
            session['user_id'] = user[0]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')



@app.route('/dashboard')
def dashboard():
    if 'username' and 'password' not in session :
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/add_tenant', methods=['GET', 'POST'])
def add_tenant(): 

    user_id = session.get('user_id') 
    cursor = mysql.connection.cursor()

    tenants = []
    search_query = ""
    message = ""

    try:
       
        if request.method == 'POST':
            if 'search' in request.form: 
                search_query = request.form['search']
            
                cursor.execute(
                    "SELECT * FROM tenants WHERE user_id = %s AND name LIKE %s",
                    (user_id, '%' + search_query + '%')
                )
            else:  
                name = request.form['name']
                contact_info = request.form['contact_info']
                lease_start = request.form['lease_start']
                lease_end = request.form['lease_end']
                status = request.form['status']

                 # Check if there are any rooms for the user
                cursor.execute("SELECT COUNT(*) FROM rooms WHERE user_id = %s", (user_id,))
                room_count = cursor.fetchone()[0]

                if room_count == 0:
                    message = 'You must add at least one room before adding tenants.', 'danger'

                else:
                    cursor.execute(
                        "INSERT INTO tenants (user_id, name, contact_info, lease_start, lease_end, status) VALUES (%s, %s, %s, %s, %s, %s)",
                        (user_id, name, contact_info, lease_start, lease_end, status)
                    )
                    mysql.connection.commit()
                    flash('Tenant added successfully!', 'success')

        if not search_query:
            cursor.execute("SELECT * FROM tenants WHERE user_id = %s", (user_id,))
        tenants = cursor.fetchall()

    except Exception as e:
        flash(f'An error occurred: {e}', 'danger')
        print(e)
    finally:
        cursor.close()

    return render_template('add_tenant.html', tenants=tenants, search_query=search_query, message=message)



@app.route('/delete_tenant/<int:tenant_id>', methods=['POST'])
def delete_tenant(tenant_id):
    cursor = mysql.connection.cursor()
    try:
        # Delete the tenant with the given ID
        cursor.execute("DELETE FROM rent_payments WHERE tenant_id = %s;", (tenant_id,))
        cursor.execute("DELETE FROM tenants WHERE id = %s", (tenant_id,))
        mysql.connection.commit()
        flash('Tenant deleted successfully!', 'success')
    except Exception as e:
        flash('An error occurred: {}'.format(e), 'danger')
        print(e)
    finally:
        cursor.close()
    return redirect(url_for('add_tenant'))

@app.route('/update_tenant/<int:tenant_id>', methods=['GET', 'POST'])
def update_tenant(tenant_id):
    cursor = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            name = request.form['name']
            contact_info = request.form['contact_info']
            lease_start = request.form['lease_start']
            lease_end = request.form['lease_end']

            # Update tenant details in the database
            cursor.execute(
                "UPDATE tenants SET name = %s, contact_info = %s, lease_start = %s, lease_end = %s WHERE id = %s",
                (name, contact_info, lease_start, lease_end, tenant_id)
            )
            mysql.connection.commit()
            flash('Tenant updated successfully!', 'success')
            return redirect(url_for('add_tenant'))

        # Fetch the tenant's current details for pre-filling the form
        cursor.execute("SELECT * FROM tenants WHERE id = %s", (tenant_id,))
        tenant = cursor.fetchone()
        if not tenant:
            flash('Tenant not found!', 'danger')
            return redirect(url_for('add_tenant'))

    except Exception as e:
        flash('An error occurred: {}'.format(e), 'danger')
        print(e)
    finally:
        cursor.close()

    return render_template('update_tenant.html', tenant=tenant)

@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    cursor = mysql.connection.cursor()
    user_id = session.get('user_id')

    # Initialize variables
    rooms = []
    rm_name = {}
    keys = []
    name_t = []
    limits = {}

    try:
        if request.method == 'POST':
            # Get room details from the form
            room_name = request.form['room_name']
            room_capacity = int(request.form['room_capacity'])

            # Insert the room into the database
            cursor.execute(
                "INSERT INTO rooms (user_id, room_name, room_capacity) VALUES (%s, %s, %s)", 
                (user_id, room_name, room_capacity)
            )
            mysql.connection.commit()

            flash('Room added successfully!', 'success')

        # Fetch all rooms for the logged-in user
        cursor.execute("SELECT * FROM rooms WHERE user_id = %s", (user_id,))
        rooms = cursor.fetchall()

        # Fetch all tenants for the logged-in user
        cursor.execute("SELECT * FROM tenants WHERE user_id = %s", (user_id,))
        tenant_name = cursor.fetchall()

        # Prepare room limits and tenant allocations
        for room in rooms:
            rm_name[room[2]] = []  # Initialize room with an empty list
            limits[room[2]] = room[3]  # Store room capacity
        
        keys = list(rm_name.keys())  # Update keys after populating `rm_name`

        for tenant in tenant_name:
            name_t.append(tenant[2])  # Collect tenant names

        # Allocate tenants to rooms
        i = 0
        for room in keys:
            while len(rm_name[room]) < limits[room] and i < len(name_t):
                rm_name[room].append(name_t[i])
                i += 1

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    finally:
        cursor.close()

    return render_template(
        'room_manage.html', 
        rooms=rooms, 
        rm_name=rm_name, 
        keys=keys
    )




@app.route('/delete_room/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    cursor = mysql.connection.cursor()
    user_id = session.get('user_id')  # Ensure the user owns the room
    try:
        # Delete the room from the database
        cursor.execute("DELETE FROM rooms WHERE id = %s AND user_id = %s", (room_id, user_id))
        mysql.connection.commit()
        flash('Room deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    finally:
        cursor.close()
    return redirect(url_for('add_room'))

from datetime import datetime

from datetime import datetime

@app.route('/tenant_payment', methods=['GET', 'POST'])
def tenant_payments():
    user_id = session.get('user_id')  # Get the logged-in user's ID
    cursor = mysql.connection.cursor()
    tenants = []
    search_query = ""

    try:
        # Search tenants
        if request.method == 'POST':
            if 'search' in request.form:
                search_query = request.form['search']
                cursor.execute(
                    "SELECT * FROM tenants WHERE user_id = %s AND name LIKE %s",
                    (user_id, '%' + search_query + '%')
                )
            elif 'make_payment' in request.form:
                tenant_id = request.form['tenant_id']
                payment_date = datetime.now().date()

                # Update tenant status to Paid
                cursor.execute(
                    "UPDATE tenants SET status = 'Paid' WHERE id = %s", (tenant_id,)
                )
                # Insert payment record
                cursor.execute(
                    "INSERT INTO rent_payments (tenant_id, payment_date, amount_paid) VALUES (%s, %s, %s)",
                    (tenant_id, payment_date, request.form['amount_paid'])
                )
                mysql.connection.commit()
                flash('Payment recorded successfully!', 'success')

        # Get tenants with their status
        if not search_query:
            cursor.execute("SELECT * FROM tenants WHERE user_id = %s", (user_id,))
        tenants = cursor.fetchall()

        # Update tenant status based on lease dates
        for tenant in tenants:
            tenant_id, lease_start, lease_end, status = tenant[0], tenant[4], tenant[5], tenant[6]
            current_date = datetime.now().date()

            if current_date > lease_end:  # If lease has ended, mark as Unpaid
                cursor.execute(
                    "UPDATE tenants SET status = 'Unpaid' WHERE id = %s", (tenant_id,)
                )
            elif current_date >= lease_start and status != 'Paid':
                cursor.execute(
                    "UPDATE tenants SET status = 'Paid' WHERE id = %s", (tenant_id,)
                )
        mysql.connection.commit()

    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    finally:
        cursor.close()

    return render_template('tenant_payment.html', tenants=tenants, search_query=search_query)

if __name__ == "__main__":
    app.run(debug=True)
