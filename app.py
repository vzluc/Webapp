
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import re
from email_validator import validate_email, EmailNotValidError
import os
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'geheim'

DATABASE = 'klanten.db'

def connect_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS klanten (
            klantid INTEGER PRIMARY KEY AUTOINCREMENT,
            klantnr TEXT UNIQUE NOT NULL,
            klantnaam TEXT NOT NULL,
            klantadres TEXT,
            klantpostcode TEXT,
            klantgemeente TEXT,
            klantland TEXT,
            klantbtwnr TEXT,
            klanttel TEXT,
            klantmob TEXT,
            klantemail TEXT,
            klantwebsite TEXT,
            klantinfo TEXT,
            Actief BOOLEAN DEFAULT 1
        )""")

def format_text(text):
    return ' '.join(w.capitalize() for w in text.strip().split()) if text else ''

def validate_klant(data):
    errors = []

    # Verplicht veld
    if not data.get('klantnaam'):
        errors.append("Klantnaam is verplicht.")

    # Email validatie
    try:
        validate_email(data.get('klantemail', ''))
    except EmailNotValidError:
        errors.append("Ongeldig e-mailadres.")

    # Btw-nummer validatie (BE-formaat)
    btw = data.get('klantbtwnr', '').replace(' ', '').upper()
    if btw and not re.fullmatch(r'(BE)?0?\d{9}', btw):
        errors.append("Ongeldig Belgisch btw-nummer.")

    return errors

@app.route('/', methods=['GET', 'HEAD'])
def index():
    db = connect_db()
    klanten = db.execute("SELECT * FROM klanten WHERE actief=1 ORDER BY klantnaam").fetchall()
    db.close()
    return render_template('index.html', klanten=klanten)

@app.route('/toevoegen', methods=['GET', 'POST'])
def toevoegen():
    if request.method == 'POST':
        data = {k: format_text(v) for k, v in request.form.items()}
        errors = validate_klant(data)

        if errors:
            for error in errors:
                flash(error)
            return render_template('form.html', klant=data)

        with connect_db() as db:
            db.execute("""INSERT INTO klanten 
                (klantnr, klantnaam, klantadres, klantpostcode, klantgemeente, klantland,
                 klantbtwnr, klanttel, klantmob, klantemail, klantwebsite, klantinfo, actief)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (data['klantnr'], data['klantnaam'], data['klantadres'], data['klantpostcode'],
                 data['klantgemeente'], data['klantland'], data['klantbtwnr'], data['klanttel'],
                 data['klantmob'], data['klantemail'], data['klantwebsite'], data['klantinfo'])
            )
            flash("Klant toegevoegd.")
        return redirect(url_for('index'))
    return render_template('form.html', klant={})

@app.route('/bewerken/<int:klantid>', methods=['GET', 'POST'])
def bewerken(klantid):
    db = connect_db()
    if request.method == 'POST':
        data = {k: format_text(v) for k, v in request.form.items()}
        errors = validate_klant(data)
        if errors:
            for error in errors:
                flash(error)
            data['klantid'] = klantid
            return render_template('form.html', klant=data)
        db.execute("""UPDATE klanten SET
            klantnr=?, klantnaam=?, klantadres=?, klantpostcode=?, klantgemeente=?,
            klantland=?, klantbtwnr=?, klanttel=?, klantmob=?, klantemail=?,
            klantwebsite=?, klantinfo=? WHERE klantid=?""",
            (data['klantnr'], data['klantnaam'], data['klantadres'], data['klantpostcode'],
             data['klantgemeente'], data['klantland'], data['klantbtwnr'], data['klanttel'],
             data['klantmob'], data['klantemail'], data['klantwebsite'], data['klantinfo'],
             klantid)
        )
        db.commit()
        flash("Klant gewijzigd.")
        return redirect(url_for('index'))
    klant = db.execute("SELECT * FROM klanten WHERE klantid=?", (klantid,)).fetchone()
    db.close()
    if klant is None:
        flash("Klant niet gevonden.")
        return redirect(url_for('index'))
    return render_template('form.html', klant=klant)

if __name__ == '__main__':
    # Alleen lokaal draaien
    if not os.path.exists("klanten.db"):
        init_db()
    app.run(debug=True)
else:
    # Render of andere server
    if not os.path.exists("klanten.db"):
        init_db()


