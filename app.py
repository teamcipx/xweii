from flask import Flask, request, jsonify, render_template
from supabase import create_client, Client
from datetime import datetime, timezone
import os

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

USER_ID = "1" # Dummy User ID for phone testing

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# ==========================================
# TASK 1: Crypto Exchange (Manual Verify)
# ==========================================
@app.route('/api/crypto/submit', methods=['POST'])
def crypto_submit():
    data = request.json
    supabase.table('crypto_orders').insert({
        "user_id": USER_ID, "order_type": data['type'], 
        "coin": data['coin'], "amount": data['amount']
    }).execute()
    return jsonify({"msg": "Crypto order pending manual review."})

# ==========================================
# TASK 2: Gmail Task Submit (Focus)
# ==========================================
@app.route('/api/gmail/submit', methods=['POST'])
def gmail_submit():
    data = request.json
    supabase.table('gmail_submissions').insert({
        "user_id": USER_ID, "submitted_email": data['email']
    }).execute()
    return jsonify({"msg": "Gmail submitted! Under 6H review."})

# ==========================================
# TASK 3: Sell Social Account
# ==========================================
@app.route('/api/market/submit', methods=['POST'])
def market_submit():
    data = request.json
    supabase.table('market_accounts').insert({
        "user_id": USER_ID, "platform": data['platform'], 
        "account_details": data['details'], "price": data['price']
    }).execute()
    return jsonify({"msg": "Account listed for sale in market."})

# ==========================================
# ADMIN API & AUTO-APPROVE LOGIC
# ==========================================
@app.route('/api/admin/pending', methods=['GET'])
def get_pending():
    crypto = supabase.table('crypto_orders').select('*').eq('status', 'pending').execute().data
    gmail = supabase.table('gmail_submissions').select('*').eq('status', 'pending').execute().data
    return jsonify({"crypto": crypto, "gmail": gmail})

@app.route('/api/admin/action', methods=['POST'])
def admin_action():
    data = request.json
    table = data['table'] # 'crypto_orders' or 'gmail_submissions'
    req_id = data['id']
    action = data['action'] # 'approved' or 'rejected'
    
    supabase.table(table).update({"status": action}).eq('id', req_id).execute()
    
    # If Gmail Approved, add balance
    if table == 'gmail_submissions' and action == 'approved':
        user = supabase.table('users').select('balance').eq('id', USER_ID).execute().data[0]
        new_bal = float(user['balance']) + 2.00 # $2 Reward
        supabase.table('users').update({"balance": new_bal}).eq('id', USER_ID).execute()

    return jsonify({"msg": f"Task {action} successfully!"})

# --- Cron Job: Auto Approve after 6 Hours ---
@app.route('/api/cron_6h', methods=['GET'])
def auto_approve():
    pending = supabase.table('gmail_submissions').select('*').eq('status', 'pending').execute().data
    count = 0
    now = datetime.now(timezone.utc)

    for sub in pending:
        created_time = datetime.fromisoformat(sub['created_at'].replace("Z", "+00:00"))
        diff_hours = (now - created_time).total_seconds() / 3600
        
        if diff_hours >= 6.0: # 6 ঘণ্টা পার হলে
            # Update Status
            supabase.table('gmail_submissions').update({"status": "approved"}).eq('id', sub['id']).execute()
            # Add Balance
            user = supabase.table('users').select('balance').eq('id', sub['user_id']).execute().data[0]
            supabase.table('users').update({"balance": float(user['balance']) + float(sub['reward'])}).eq('id', sub['user_id']).execute()
            count += 1

    return jsonify({"msg": f"{count} accounts auto-approved."})

if __name__ == '__main__':
    app.run(debug=True)
