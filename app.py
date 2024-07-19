from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import mysql.connector
import logging

app = Flask(__name__)
app.secret_key = '4f3c2d5e6f7a8b9c0d1e2f3g4h5i6j7k'
app.config['SESSION_TYPE'] = 'filesystem'



# ---------------------------------- DATABASE CONNECTION ----------------------------------

db_config = {
    'user': 'root',  
    'password': '', 
    'host': 'localhost',
    'database': 'SaeedBookBank', 
}

def get_db_connection():
    connection = mysql.connector.connect(**db_config)
    return connection



# ------------------------------------- HOMEPAGE ROUTE -------------------------------------

@app.route('/')
def home():
    # Retrieve the Search Query
    search_query = request.args.get('search', '')
    
    # Connect to Database
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
    # Use Search Query to Search Database
    if search_query:
        cursor.execute('''
            SELECT Books.BookID, Books.Title, Books.ISBN, Books.Description, Books.Price, Books.Stock, Books.image_path, Authors.AuthorName, Books.CategoryID
            FROM Books
            INNER JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
            INNER JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
            WHERE Books.Title LIKE %s OR Authors.AuthorName LIKE %s
        ''', (f'%{search_query}%', f'%{search_query}%'))
    else:
        # If No Search Query, Retrieve All Data
        cursor.execute('''
            SELECT Books.BookID, Books.Title, Books.ISBN, Books.Description, Books.Price, Books.Stock, Books.image_path, Authors.AuthorName, Books.CategoryID
            FROM Books
            INNER JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
            INNER JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
        ''')
    
    # Fetch All Books From Executed Query
    books = cursor.fetchall()

    # Fetch All Categories From Executed Query
    cursor.execute('SELECT CategoryID, CategoryName FROM Categories')
    categories = cursor.fetchall()

    # End Database Connection
    cursor.close()
    connection.close()

    # Initialize User-Specific Variables
    first_name = None
    cart_items_count = 0
    is_admin = False

    # Is User Logged In?
    if 'user_id' in session:

        # Get User's Details
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT FirstName, Email FROM Users WHERE UserID = %s', (session['user_id'],))
        user = cursor.fetchone()
        
        # Get User's Cart Items
        cursor.execute('SELECT COUNT(*) AS count FROM Cart WHERE UserID = %s', (session['user_id'],))
        cart_count = cursor.fetchone()
        cart_items_count = cart_count['count'] if cart_count else 0
        
        cursor.close()
        connection.close()
        
        if user:
            first_name = user['FirstName']
            is_admin = user['Email'] == 'admin@sbb.com'

    # Render HTML with Retrieved Data
    return render_template('index.html', books=books, categories=categories, first_name=first_name, cart_items_count=cart_items_count, is_admin=is_admin)



# ------------------------------------- LOGIN ROUTE -------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        logging.info(f'Attempting login with email: {email}')
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM Users WHERE Email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user:
            logging.info(f'User found: {user["Email"]}')
            if check_password_hash(user['Password'], password):
                session['user_id'] = user['UserID']
                logging.info('Login successful')
                return redirect(url_for('home'))
            else:
                logging.warning('Invalid password')
                error = 'Invalid password'
        else:
            logging.warning('User not found')
            error = 'User not found'
        return render_template('login.html', error=error)
    return render_template('login.html')



# ------------------------------------- REGISTER ROUTE -------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        email = request.form['email']
        address = request.form['address']
        city = request.form['city']
        country = request.form['country']
        password = generate_password_hash(request.form['password'])
        pin = request.form['pin']
        logging.info(f'Received registration details: {first_name}, {email}, {address}, {city}, {country}, {pin}')
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute('INSERT INTO Users (FirstName, Email, Address, City, Country, Password, pin) VALUES (%s, %s, %s, %s, %s, %s, %s)', 
                           (first_name, email, address, city, country, password, pin))
            connection.commit()
            cursor.close()
            connection.close()
            logging.info('User registered successfully')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            logging.error(f'Error: {err}')
            error_message = f"An error occurred: {err}"
            return render_template('register.html', error=error_message)
    return render_template('register.html', error=None)



# ------------------------------------- LOGOUT ROUTE -------------------------------------

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))



# -------------------------------------- ADD TO CART --------------------------------------

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    # Is User Logged In?
    if 'user_id' not in session:
        return {'success': False, 'message': 'User not logged in'}, 401

    # Get Cart Item Details from Current Session
    book_id = request.form['book_id']
    user_id = session['user_id']
    quantity = int(request.form['quantity'])

    connection = get_db_connection()
    cursor = connection.cursor()

    # Is Item Already in Cart?
    cursor.execute('SELECT Quantity FROM Cart WHERE UserID = %s AND BookID = %s', (user_id, book_id))
    cart_item = cursor.fetchone()

    # Get Current Stock of Book
    cursor.execute('SELECT Stock FROM Books WHERE BookID = %s', (book_id,))
    book = cursor.fetchone()

    if book is None:
        return {'success': False, 'message': 'Book not found'}, 404

    # Update Book Quantity (If Already in Cart)
    if cart_item:
        new_quantity = cart_item[0] + quantity

        # Does Quantity Exceed Stock Levels?
        if new_quantity > book[0]:
            return {'success': False, 'message': 'Not enough stock'}, 400
        cursor.execute('UPDATE Cart SET Quantity = %s WHERE UserID = %s AND BookID = %s', (new_quantity, user_id, book_id))
    
    else:
        # Add to Cart with Desired Quantity
        if quantity > book[0]:
            return {'success': False, 'message': 'Not enough stock'}, 400
        cursor.execute('INSERT INTO Cart (UserID, BookID, Quantity) VALUES (%s, %s, %s)', (user_id, book_id, quantity))

    # Save Changes to Database
    connection.commit()
    cursor.close()
    connection.close()

    return {'success': True, 'quantity': new_quantity if cart_item else quantity}



# -------------------------------- FORGOT / RESET PASSWORD --------------------------------

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        logging.info(f'Password reset request for email: {email}')
        return redirect(url_for('reset_password', email=email))
    return render_template('forgot_password.html')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        pin = request.form['pin']
        new_password = generate_password_hash(request.form['new_password'])
        logging.info(f'Received password reset request for: {email}')
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM Users WHERE Email = %s AND pin = %s', (email, pin))
            user = cursor.fetchone()
            
            if user:
                cursor.execute('UPDATE Users SET Password = %s WHERE Email = %s', (new_password, email))
                connection.commit()
                logging.info('Password reset successfully')
                return redirect(url_for('login'))
            else:
                logging.warning('Invalid email or PIN')
                return 'Invalid email or PIN'
        except mysql.connector.Error as err:
            logging.error(f'Error: {err}')
            return f"An error occurred: {err}"
        finally:
            cursor.close()
            connection.close()

    return render_template('reset_password.html')



# ----------------------------------- CLEAR CART -----------------------------------

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    if 'user_id' not in session:
        return {'success': False, 'message': 'User not logged in'}, 401

    user_id = session['user_id']
    
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('DELETE FROM Cart WHERE UserID = %s', (user_id,))
    connection.commit()
    cursor.close()
    connection.close()

    return {'success': True}



# -------------------------------- GET CART ITEMS ---------------------------------

@app.route('/get_cart_items', methods=['GET'])
def get_cart_items():
    if 'user_id' not in session:
        return {'success': False, 'message': 'User not logged in'}, 401

    user_id = session['user_id']
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('''
        SELECT Books.BookID, Books.Title, Authors.AuthorName, Books.Price, Books.image_path, Cart.Quantity
        FROM Cart
        JOIN Books ON Cart.BookID = Books.BookID
        JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
        JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
        WHERE Cart.UserID = %s
    ''', (user_id,))
    
    cart_items = cursor.fetchall()
    cursor.close()
    connection.close()

    for item in cart_items:
        item['image_path'] = url_for('static', filename=item['image_path'])

    return {'success': True, 'cart_items': cart_items}



# ----------------------------------- CHECKOUT -----------------------------------

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return {'success': False, 'message': 'User not logged in'}, 401

    user_id = session['user_id']
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('''
        SELECT Books.BookID, Books.Title, Authors.AuthorName, Books.Price, Books.Stock, Cart.Quantity
        FROM Cart
        JOIN Books ON Cart.BookID = Books.BookID
        JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
        JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
        WHERE Cart.UserID = %s
    ''', (user_id,))
    
    cart_items = cursor.fetchall()

    if not cart_items:
        cursor.close()
        connection.close()
        return {'success': False, 'message': 'Cart is empty'}, 400

    # Enough Stock?
    for item in cart_items:
        if item['Quantity'] > item['Stock']:
            cursor.close()
            connection.close()
            return {'success': False, 'message': f'Not enough stock for {item["Title"]}'}, 400

    # Calculate total
    total = sum(item['Price'] * item['Quantity'] for item in cart_items)
    
    # Create new order
    cursor.execute('INSERT INTO Orders (UserID, Total) VALUES (%s, %s)', (user_id, total))
    order_id = cursor.lastrowid

    # Insert order items and update stock
    for item in cart_items:
        cursor.execute('''
            INSERT INTO OrderItems (OrderID, BookID, Quantity, Price)
            VALUES (%s, %s, %s, %s)
        ''', (order_id, item['BookID'], item['Quantity'], item['Price']))

        cursor.execute('''
            UPDATE Books SET Stock = Stock - %s WHERE BookID = %s
        ''', (item['Quantity'], item['BookID']))

    # Clear the cart
    cursor.execute('DELETE FROM Cart WHERE UserID = %s', (user_id,))

    # Get user details
    cursor.execute('SELECT FirstName, Email, Address, City, Country FROM Users WHERE UserID = %s', (user_id,))
    user = cursor.fetchone()
    
    connection.commit()
    cursor.close()
    connection.close()

    return {
        'success': True,
        'order_id': order_id,
        'total': total,
        'items': cart_items,
        'user': user,
        'order_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'payment_method': 'Cash on Delivery'
    }



# ----------------------------------- ADMIN PANEL -----------------------------------

@app.route('/admin_panel')
def admin_panel():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT Email FROM Users WHERE UserID = %s', (session['user_id'],))
    user = cursor.fetchone()
    
    if user['Email'] != 'admin@sbb.com':
        cursor.close()
        connection.close()
        return redirect(url_for('home'))
    
    cursor.execute('SELECT COUNT(*) AS total_users FROM Users')
    total_users = cursor.fetchone()['total_users']
    
    cursor.execute('SELECT COUNT(*) AS total_orders FROM Orders')
    total_orders = cursor.fetchone()['total_orders']
    
    cursor.execute('SELECT SUM(Total) AS total_sales FROM Orders')
    total_sales = cursor.fetchone()['total_sales']
    
    cursor.execute('SELECT UserID, FirstName, Email, CreatedAt FROM Users')
    users = cursor.fetchall()
    
    cursor.execute('SELECT OrderID, UserID, Total, OrderDate FROM Orders')
    orders = cursor.fetchall()
    
    cursor.execute('SELECT BookID, Title, Stock FROM Books')
    books = cursor.fetchall()
    
    cursor.close()
    connection.close()

    for user in users:
        user['CreatedAt'] = user['CreatedAt'].strftime('%B %d, %Y at %I:%M %p')
    for order in orders:
        order['OrderDate'] = order['OrderDate'].strftime('%B %d, %Y at %I:%M %p')
    
    metrics = {
        'total_users': total_users,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'total_books': len(books) 
    }
    
    return render_template('admin_panel.html', metrics=metrics, users=users, orders=orders, books=books)


# Days in Month
def get_days_in_month(year, month):
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day


# SALES BY DAY -----------------------------------

@app.route('/get_sales_by_day')
def get_sales_by_day():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('''
        SELECT DAY(OrderDate) as day, SUM(Total) as total
        FROM Orders
        WHERE MONTH(OrderDate) = MONTH(CURDATE()) AND YEAR(OrderDate) = YEAR(CURDATE())
        GROUP BY DAY(OrderDate)
    ''')
    sales_data = cursor.fetchall()
    cursor.close()
    connection.close()

    # Prepare data for Chart.js
    days_in_month = get_days_in_month(datetime.now().year, datetime.now().month)
    days = list(range(1, days_in_month + 1))
    sales = [0] * days_in_month

    for item in sales_data:
        sales[item['day'] - 1] = item['total']

    data = {
        'labels': [str(day) for day in days],
        'sales': sales
    }
    return jsonify(data)


# USERS REGISTERED BY DAY -----------------------------------

@app.route('/get_users_registered_by_day')
def get_users_registered_by_day():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('''
        SELECT DAY(CreatedAt) as day, COUNT(UserID) as count
        FROM Users
        WHERE MONTH(CreatedAt) = MONTH(CURDATE()) AND YEAR(CreatedAt) = YEAR(CURDATE())
        GROUP BY DAY(CreatedAt)
    ''')
    users_data = cursor.fetchall()
    cursor.close()
    connection.close()

    # Prepare data for Chart.js
    days_in_month = get_days_in_month(datetime.now().year, datetime.now().month)
    days = list(range(1, days_in_month + 1))
    users = [0] * days_in_month

    for item in users_data:
        users[item['day'] - 1] = item['count']

    data = {
        'labels': [str(day) for day in days],
        'users': users
    }
    return jsonify(data)


# ORDERS BY DAY -----------------------------------

@app.route('/get_orders_placed_by_day')
def get_orders_placed_by_day():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('''
        SELECT DAY(OrderDate) as day, COUNT(OrderID) as count
        FROM Orders
        WHERE MONTH(OrderDate) = MONTH(CURDATE()) AND YEAR(OrderDate) = YEAR(CURDATE())
        GROUP BY DAY(OrderDate)
    ''')
    orders_data = cursor.fetchall()
    cursor.close()
    connection.close()

    # Prepare data for Chart.js
    days_in_month = get_days_in_month(datetime.now().year, datetime.now().month)
    days = list(range(1, days_in_month + 1))
    orders = [0] * days_in_month

    for item in orders_data:
        orders[item['day'] - 1] = item['count']

    data = {
        'labels': [str(day) for day in days],
        'orders': orders
    }
    return jsonify(data)


# BOOKS INVENTORY BY DAY -----------------------------------

@app.route('/get_books_by_category')
def get_books_by_category():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('''
        SELECT Categories.CategoryName, COUNT(Books.BookID) as count
        FROM Books
        JOIN Categories ON Books.CategoryID = Categories.CategoryID
        GROUP BY Categories.CategoryName
    ''')
    books_data = cursor.fetchall()
    cursor.close()
    connection.close()

    # Prepare data for Chart.js
    categories = [item['CategoryName'] for item in books_data]
    counts = [item['count'] for item in books_data]

    data = {
        'labels': categories,
        'counts': counts
    }
    return jsonify(data)



# ----------------------------------- ORDERS -----------------------------------


@app.route('/get_orders', methods=['GET'])
def get_orders():
    if 'user_id' not in session:
        return {'success': False, 'message': 'User not logged in'}, 401

    user_id = session['user_id']
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('''
        SELECT OrderID, Total, OrderDate
        FROM Orders
        WHERE UserID = %s
        ORDER BY OrderDate DESC
    ''', (user_id,))
    
    orders = cursor.fetchall()

    # Fetch items for each order
    for order in orders:
        cursor.execute('''
            SELECT Books.Title, Authors.AuthorName, OrderItems.Quantity, OrderItems.Price
            FROM OrderItems
            JOIN Books ON OrderItems.BookID = Books.BookID
            JOIN BookAuthors ON Books.BookID = BookAuthors.BookID
            JOIN Authors ON BookAuthors.AuthorID = Authors.AuthorID
            WHERE OrderItems.OrderID = %s
        ''', (order['OrderID'],))
        order['items'] = cursor.fetchall()

    cursor.close()
    connection.close()

    # Format OrderDate
    for order in orders:
        order['OrderDate'] = order['OrderDate'].strftime('%B %d, %Y at %I:%M %p')

    return {'success': True, 'orders': orders}



# --------------------------------- MAIN PROGRAM ---------------------------------


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)
