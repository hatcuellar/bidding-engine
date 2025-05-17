from flask import Flask, render_template, jsonify, request
import os
from dotenv import load_dotenv
from models import db, initialize_db, Brand, Partner, AdSlot, BidModel, Bid, Performance, create_sample_data
from bidding_engine import evaluate_bids, normalize_bid_to_impression_value

# Load environment variables
load_dotenv()

# Create Flask application
app = Flask(__name__)

# Database configuration - using PostgreSQL as MySQL isn't available in the environment
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
with app.app_context():
    initialize_db(app)
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/brands', methods=['GET'])
def get_brands():
    with app.app_context():
        brands = Brand.query.all()
        return jsonify([brand.to_dict() for brand in brands])

@app.route('/api/brands', methods=['POST'])
def create_brand():
    data = request.json
    with app.app_context():
        new_brand = Brand(
            name=data['name'],
            industry=data['industry'],
            logo_url=data.get('logo_url'),
            website=data.get('website'),
            budget=data.get('budget', 0),
            strategy=data.get('strategy', 'Balanced')
        )
        db.session.add(new_brand)
        db.session.commit()
        return jsonify(new_brand.to_dict()), 201

@app.route('/api/partners', methods=['GET'])
def get_partners():
    with app.app_context():
        partners = Partner.query.all()
        return jsonify([partner.to_dict() for partner in partners])

@app.route('/api/ad_sizes', methods=['GET'])
def get_ad_sizes():
    with app.app_context():
        from models import AdSize
        ad_sizes = AdSize.query.all()
        return jsonify([ad_size.to_dict() for ad_size in ad_sizes])

@app.route('/api/ad_slots', methods=['GET'])
def get_ad_slots():
    with app.app_context():
        ad_slots = AdSlot.query.all()
        return jsonify([ad_slot.to_dict() for ad_slot in ad_slots])

@app.route('/api/ad_slots/<int:slot_id>', methods=['GET'])
def get_ad_slot(slot_id):
    with app.app_context():
        ad_slot = AdSlot.query.get_or_404(slot_id)
        return jsonify(ad_slot.to_dict())

@app.route('/api/bids', methods=['POST'])
def place_bid():
    data = request.json
    with app.app_context():
        new_bid = Bid(
            brand_id=data['brand_id'],
            ad_slot_id=data['ad_slot_id'],
            model_id=data['model_id'],
            amount=data['amount'],
            min_threshold=data.get('min_threshold'),
            max_threshold=data.get('max_threshold'),
            status='active'  # Set to active by default
        )
        db.session.add(new_bid)
        db.session.commit()
        
        # Calculate the normalized value for this bid
        ad_slot = AdSlot.query.get(data['ad_slot_id'])
        performance = Performance.query.filter_by(
            brand_id=data['brand_id'], 
            ad_slot_id=data['ad_slot_id']
        ).first()
        
        if performance:
            # Update the normalized value based on the bid model
            normalized_value = normalize_bid_to_impression_value(new_bid, performance)
            new_bid.normalized_value = normalized_value
            db.session.commit()
        
        return jsonify(new_bid.to_dict()), 201

@app.route('/api/bids/ad_slots/<int:slot_id>', methods=['GET'])
def get_bids_for_slot(slot_id):
    with app.app_context():
        bids = Bid.query.filter_by(ad_slot_id=slot_id).all()
        return jsonify([bid.to_dict() for bid in bids])

@app.route('/api/evaluate_bids/<int:slot_id>', methods=['GET'])
def evaluate_ad_slot_bids(slot_id):
    with app.app_context():
        # Get all active bids for this slot
        bids = Bid.query.filter_by(ad_slot_id=slot_id, status='active').all()
        
        if not bids:
            return jsonify({"message": "No active bids for this slot"}), 404
        
        # Get the slot
        slot = AdSlot.query.get_or_404(slot_id)
        
        # Evaluate bids using our predictive engine
        bid_values = evaluate_bids(bids, slot)
        
        # If there are evaluated bids, find the winning bid
        if bid_values:
            winning_bid = max(bid_values, key=lambda x: x['value_per_impression'])
            
            return jsonify({
                "winning_bid": winning_bid,
                "all_bids": bid_values
            })
        else:
            return jsonify({"message": "No valid bids for this slot"}), 404

@app.route('/api/init_demo_data', methods=['POST'])
def init_demo_data():
    with app.app_context():
        success = create_sample_data()
        if success:
            return jsonify({"message": "Demo data initialized successfully"})
        else:
            return jsonify({"message": "Error initializing demo data"}), 500

if __name__ == '__main__':
    # Use environment variables or default values
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8080))  # Changed to port 8080 to avoid conflict
    debug = os.environ.get('DEBUG', 'True').lower() in ['true', '1', 't']
    
    app.run(host=host, port=port, debug=debug)