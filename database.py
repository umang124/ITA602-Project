import sqlite3


DATABASE_NAME = "car_price.db"


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Prediction History table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,

        fuel_type TEXT,
        aspiration TEXT,
        door_number TEXT,
        car_body TEXT,
        drive_wheel TEXT,
        engine_location TEXT,

        wheelbase REAL,
        carlength REAL,
        carwidth REAL,
        carheight REAL,
        curbweight REAL,

        engine_type TEXT,
        cylinder_number TEXT,
        enginesize REAL,
        fuel_system TEXT,

        boreratio REAL,
        stroke REAL,
        compression_ratio REAL,

        horsepower INTEGER,
        peakrpm INTEGER,
        citympg INTEGER,
        highwaympg INTEGER,

        predicted_price REAL,

        prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


# -------------------------
# USER FUNCTIONS
# -------------------------

def register_user(username, email, password):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO users (username, email, password)
        VALUES (?, ?, ?)
        """, (username, email, password))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def get_user(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    )

    user = cursor.fetchone()
    conn.close()

    return user


# -------------------------
# PREDICTION FUNCTIONS
# -------------------------

def save_prediction(
    user_id,
    fuel_type,
    aspiration,
    door_number,
    car_body,
    drive_wheel,
    engine_location,
    wheelbase,
    carlength,
    carwidth,
    carheight,
    curbweight,
    engine_type,
    cylinder_number,
    enginesize,
    fuel_system,
    boreratio,
    stroke,
    compression_ratio,
    horsepower,
    peakrpm,
    citympg,
    highwaympg,
    predicted_price
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO prediction_history (
        user_id,
        fuel_type,
        aspiration,
        door_number,
        car_body,
        drive_wheel,
        engine_location,
        wheelbase,
        carlength,
        carwidth,
        carheight,
        curbweight,
        engine_type,
        cylinder_number,
        enginesize,
        fuel_system,
        boreratio,
        stroke,
        compression_ratio,
        horsepower,
        peakrpm,
        citympg,
        highwaympg,
        predicted_price
    )
    VALUES (
        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
    )
    """, (
        user_id,
        fuel_type,
        aspiration,
        door_number,
        car_body,
        drive_wheel,
        engine_location,
        wheelbase,
        carlength,
        carwidth,
        carheight,
        curbweight,
        engine_type,
        cylinder_number,
        enginesize,
        fuel_system,
        boreratio,
        stroke,
        compression_ratio,
        horsepower,
        peakrpm,
        citympg,
        highwaympg,
        float(predicted_price)
    ))

    conn.commit()
    conn.close()


def get_prediction_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM prediction_history
    WHERE user_id = ?
    ORDER BY prediction_date DESC
    """, (user_id,))

    data = cursor.fetchall()
    conn.close()

    return data


def delete_prediction(prediction_id, user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM prediction_history
        WHERE id = ? AND user_id = ?
        """,
        (prediction_id, user_id)
    )

    conn.commit()
    conn.close()

def get_prediction_stats(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        COUNT(*) AS total_predictions,
        AVG(predicted_price) AS average_price,
        MAX(predicted_price) AS highest_price,
        MIN(predicted_price) AS lowest_price
    FROM prediction_history
    WHERE user_id = ?
    """, (user_id,))

    stats = cursor.fetchone()

    conn.close()

    return stats


def get_prediction_chart_data(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT prediction_date, predicted_price
    FROM prediction_history
    WHERE user_id = ?
    ORDER BY prediction_date ASC
    """, (user_id,))

    data = cursor.fetchall()

    conn.close()

    return data