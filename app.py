from flask import Flask, render_template, request, redirect, url_for, session
import pyodbc
import math
import os  

app = Flask(_name_)
app.secret_key = 'clave_secreta_segura'  # Necesario para usar sesiones

conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=BIGDATA;"
    "Trusted_Connection=yes;"
)

# 🟢 Login
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        return redirect(url_for('index'))
    return render_template("home.html")

# 🔴 Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# 📁 Página para listar tablas
@app.route('/tablas')
def index():
    if 'username' not in session:
        return redirect(url_for('home'))

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        tables = [row[0] for row in cursor.fetchall()]
        return render_template('index.html', tables=tables, username=session['username'])
    except Exception as e:
        return f"Error: {e}"

# 📄 Visualización de cada tabla
@app.route('/tabla/<name>')
def show_table(name):
    if 'username' not in session:
        return redirect(url_for('home'))

    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    limit = 20
    offset = (page - 1) * limit

    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    query_base = f"SELECT * FROM [{name}]"
    count_query = f"SELECT COUNT(*) FROM [{name}]"

    if search:
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?", name)
        cols = [row[0] for row in cursor.fetchall()]
        like_conditions = " OR ".join([f"{col} LIKE ?" for col in cols])
        like_values = [f"%{search}%"] * len(cols)
        query_base += f" WHERE {like_conditions}"
        count_query += f" WHERE {like_conditions}"

        cursor.execute(count_query, *like_values)
        total_rows = cursor.fetchone()[0]

        query_base += f" ORDER BY 1 OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
        cursor.execute(query_base, *like_values)
    else:
        cursor.execute(count_query)
        total_rows = cursor.fetchone()[0]

        query_base += f" ORDER BY 1 OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
        cursor.execute(query_base)

    data = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    total_pages = math.ceil(total_rows / limit)

    return render_template("table.html", table=name, columns=columns, data=data, page=page, total_pages=total_pages, search=search, username=session['username'])

# 🔗 Informe Power BI
@app.route('/informe')
def informe():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template("informe.html", username=session['username'])

if _name_ == "_main_":
    port = int(os.environ.get("PORT", 10000))
    app.run(debug=False,host="0.0.0.0",port=port)
