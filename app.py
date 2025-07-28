import os
import json
import uuid
import shutil
import pytz # type: ignore
IST = pytz.timezone('Asia/Kolkata')

from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-random-string'
app.config['APP_NAME'] = 'LoopIn'

# where we'll store the updates
UPDATES_FILE = os.path.join(app.root_path, 'updates.json')
BACKUP_FILE = os.path.join(app.root_path, 'updates_backup.json')

if not os.path.exists(UPDATES_FILE):
    os.makedirs(os.path.dirname(UPDATES_FILE), exist_ok=True)
    shutil.copy(BACKUP_FILE, UPDATES_FILE)
    print("✅ Restored updates.json from backup")

# Load updates from /var/data/updates.json
def load_updates():
    # If the file doesn't exist, create it with an empty list
    if not os.path.exists(UPDATES_FILE):
        os.makedirs(os.path.dirname(UPDATES_FILE), exist_ok=True)
        with open(UPDATES_FILE, 'w') as f:
            json.dump([], f, indent=2)
        return []

    # Load the file, handle bad JSON gracefully
    try:
        with open(UPDATES_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

# Save updates to /var/data/updates.json
def save_updates(updates_list):
    os.makedirs(os.path.dirname(UPDATES_FILE), exist_ok=True)
    with open(UPDATES_FILE, 'w') as f:
        json.dump(updates_list, f, indent=2)

@app.route('/sync-backup')
def sync_backup():
    try:
        with open(UPDATES_FILE, 'r') as src, open(BACKUP_FILE, 'w') as dest:
            dest.write(src.read())
        return "✅ Backup synced successfully."
    except Exception as e:
        return f"❌ Backup failed: {e}"

# who’s allowed to post
authorized_users = ['Kamran Arbaz', 'Drishya CM', 'Abigail Das']

@app.route('/')
def home():
    return render_template('home.html', app_name=app.config['APP_NAME'])


@app.route('/updates')
def show_updates():
    updates = load_updates()
    current_user = session.get('username')
    return render_template(
        'show.html',
        app_name=app.config['APP_NAME'],
        updates=updates,
        current_user=current_user
    )

@app.route('/post', methods=['GET', 'POST'])
def post_update():
    if request.method == 'POST':
        name = request.form['name']
        message = request.form['message'].strip()

        if name not in authorized_users:
            flash('🚫 You are not authorized to post updates.')
            return redirect(url_for('post_update'))

        # remember who’s posting
        session['username'] = name

        # load existing, prepend new, save
        updates = load_updates()
        updates.insert(0, {
            'id': uuid.uuid4().hex,
            'name': name,
            'message': message,
            'timestamp': datetime.now(IST).strftime('%d/%m/%Y, %H:%M:%S')
        })
        save_updates(updates)

        flash('✅ Update posted.')
        return redirect(url_for('show_updates'))

    current_user = session.get('username')
    return render_template(
        'post.html',
        app_name=app.config['APP_NAME'],
        authorized_users=authorized_users,
        current_user=current_user
    )


@app.route('/edit/<update_id>', methods=['GET', 'POST'])
def edit_update(update_id):
    updates = load_updates()
    # find the update
    update = next((u for u in updates if u['id'] == update_id), None)
    if not update:
        flash('⚠️ Update not found.')
        return redirect(url_for('show_updates'))

    current_user = session.get('username')
    if update['name'] != current_user:
        flash('🚫 You can only edit your own updates.')
        return redirect(url_for('show_updates'))

    if request.method == 'POST':
        update['message'] = request.form['message'].strip()
        update['timestamp'] = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        save_updates(updates)
        flash('✏️ Update edited successfully.')
        return redirect(url_for('show_updates'))

    return render_template(
        'edit.html',
        app_name=app.config['APP_NAME'],
        update=update
    )


@app.route('/delete/<update_id>', methods=['POST'])
def delete_update(update_id):
    updates = load_updates()
    update = next((u for u in updates if u['id'] == update_id), None)
    if not update:
        flash('⚠️ Update not found.')
        return redirect(url_for('show_updates'))

    current_user = session.get('username')
    if update['name'] != current_user:
        flash('🚫 You can only delete your own updates.')
        return redirect(url_for('show_updates'))

    # remove & persist
    updates.remove(update)
    save_updates(updates)
    flash('🗑️ Update deleted.')
    return redirect(url_for('show_updates'))


if __name__ == '__main__':
    app.run(debug=True)
