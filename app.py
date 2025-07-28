import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy # type: ignore

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loopin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'replace-this-with-a-secure-random-string'
app.config['APP_NAME'] = 'LoopIn'

db = SQLAlchemy(app)  # Instantiate db properly here

# --------------------
# Data Model
# --------------------
class Update(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)

# Create tables
with app.app_context():
    db.create_all()

authorized_users = ['Kamran Arbaz', 'Drishya CM', 'Abigail Das']

@app.route('/')
def home():
    return render_template('home.html', app_name=app.config['APP_NAME'])

@app.route('/updates')
def show_updates():
    updates = Update.query.order_by(Update.timestamp.desc()).all()
    current_user = session.get('username')
    return render_template('show.html', app_name=app.config['APP_NAME'], updates=updates, current_user=current_user)

@app.route('/post', methods=['GET', 'POST'])
def post_update():
    if request.method == 'POST':
        name = request.form['name']
        message = request.form['message'].strip()

        if name not in authorized_users:
            flash('🚫 You are not authorized to post updates.')
            return redirect(url_for('post_update'))

        session['username'] = name
        new_update = Update(
            id=uuid.uuid4().hex,
            name=name,
            message=message,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(new_update)
        db.session.commit()
        flash('✅ Update posted.')
        return redirect(url_for('show_updates'))

    current_user = session.get('username')
    return render_template('post.html', app_name=app.config['APP_NAME'], authorized_users=authorized_users, current_user=current_user)

@app.route('/edit/<update_id>', methods=['GET', 'POST'])
def edit_update(update_id):
    update = Update.query.get(update_id)
    if not update:
        flash('⚠️ Update not found.')
        return redirect(url_for('show_updates'))

    current_user = session.get('username')
    if update.name != current_user:
        flash('🚫 You can only edit your own updates.')
        return redirect(url_for('show_updates'))

    if request.method == 'POST':
        update.message = request.form['message'].strip()
        update.timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        db.session.commit()
        flash('✏️ Update edited successfully.')
        return redirect(url_for('show_updates'))

    return render_template('edit.html', app_name=app.config['APP_NAME'], update=update)

@app.route('/delete/<update_id>', methods=['POST'])
def delete_update(update_id):
    update = Update.query.get(update_id)
    if not update:
        flash('⚠️ Update not found.')
        return redirect(url_for('show_updates'))

    current_user = session.get('username')
    if update.name != current_user:
        flash('🚫 You can only delete your own updates.')
        return redirect(url_for('show_updates'))

    db.session.delete(update)
    db.session.commit()
    flash('🗑️ Update deleted.')
    return redirect(url_for('show_updates'))

if __name__ == '__main__':
    app.run(debug=True)
