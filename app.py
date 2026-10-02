from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "library_secret_key"


def get_db_connection():
    conn = sqlite3.connect("library.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            return_date TEXT
        )
    """)

    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    total_books = conn.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    total_members = conn.execute(
        "SELECT COUNT(*) FROM members"
    ).fetchone()[0]

    issued_books = conn.execute(
        "SELECT COUNT(*) FROM issues WHERE return_date IS NULL"
    ).fetchone()[0]

    returned_books = conn.execute(
        "SELECT COUNT(*) FROM issues WHERE return_date IS NOT NULL"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_books=total_books,
        total_members=total_members,
        issued_books=issued_books,
        returned_books=returned_books
    )


@app.route("/books")
def books():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()

    return render_template("books.html", books=books)


@app.route("/add_book", methods=["GET", "POST"])
def add_book():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        title = request.form.get("title")
        author = request.form.get("author")
        category = request.form.get("category")
        quantity = request.form.get("quantity")

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO books (title, author, category, quantity)
            VALUES (?, ?, ?, ?)
        """, (title, author, category, quantity))

        conn.commit()
        conn.close()

        return redirect(url_for("books"))

    return render_template("add_book.html")


@app.route("/members")
def members():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    members = conn.execute("SELECT * FROM members").fetchall()
    conn.close()

    return render_template("members.html", members=members)


@app.route("/add_member", methods=["GET", "POST"])
def add_member():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO members (name, email, phone)
            VALUES (?, ?, ?)
        """, (name, email, phone))

        conn.commit()
        conn.close()

        return redirect(url_for("members"))

    return render_template("add_member.html")


@app.route("/issue_book", methods=["GET", "POST"])
def issue_book():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":

        book_id = request.form.get("book_id")
        member_id = request.form.get("member_id")
        issue_date = request.form.get("issue_date")

        conn.execute("""
            INSERT INTO issues (book_id, member_id, issue_date)
            VALUES (?, ?, ?)
        """, (book_id, member_id, issue_date))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    books = conn.execute(
        "SELECT * FROM books WHERE quantity > 0"
    ).fetchall()

    members = conn.execute(
        "SELECT * FROM members"
    ).fetchall()

    conn.close()

    return render_template(
        "issue_book.html",
        books=books,
        members=members
    )


@app.route("/return_book", methods=["GET", "POST"])
def return_book():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()

    if request.method == "POST":

        issue_id = request.form.get("issue_id")
        return_date = request.form.get("return_date")

        conn.execute("""
            UPDATE issues
            SET return_date = ?
            WHERE id = ?
        """, (return_date, issue_id))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    issues = conn.execute("""
        SELECT issues.id,
               books.title,
               members.name,
               issues.issue_date
        FROM issues
        JOIN books ON issues.book_id = books.id
        JOIN members ON issues.member_id = members.id
        WHERE issues.return_date IS NULL
    """).fetchall()

    conn.close()

    return render_template(
        "return_book.html",
        issues=issues
    )


@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)