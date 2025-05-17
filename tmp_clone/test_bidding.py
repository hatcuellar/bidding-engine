"""
Test Script for Bidding Rules and Coexistence Safeguards

This script tests the rules and safeguards for different bidding models,
including how CPA, CPC, and CPM models can coexist and interact.
"""

import os
from flask import Flask
from dotenv import load_dotenv
from models import db, initialize_db, Brand, AdSlot, Bid, BidModel, Campaign, Performance

# Load environment variables
load_dotenv()

# Create a test Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def initialize_demo_data():
    """Initialize demo data in the database"""
    with app.app_context():
        initialize_db(app)
        from models import create_sample_data
        create_sample_data()
        print("Demo data initialized successfully.")

def get_ad_slots():
    """Get all ad slots"""
    with app.app_context():
        slots = AdSlot.query.all()
        print(f"Found {len(slots)} ad slots:")
        for slot in slots:
            print(f"  - {slot.id}: {slot.name} ({slot.placement}) - Floor: ${slot.floor_price}")
        return slots

def get_brands():
    """Get all brands"""
    with app.app_context():
        brands = Brand.query.all()
        print(f"Found {len(brands)} brands:")
        for brand in brands:
            print(f"  - {brand.id}: {brand.name} ({brand.industry}) - Budget: ${brand.budget}")
        return brands

def place_bid(brand_id, ad_slot_id, model_id, amount, min_threshold=None, max_threshold=None):
    """Place a bid with the specified parameters"""
    with app.app_context():
        # Get the model name for display
        model = BidModel.query.get(model_id)
        model_name = model.name if model else f"Model #{model_id}"
        
        # Create the bid
        bid = Bid(
            brand_id=brand_id,
            ad_slot_id=ad_slot_id,
            model_id=model_id,
            amount=amount,
            min_threshold=min_threshold,
            max_threshold=max_threshold,
            status="active"
        )
        
        db.session.add(bid)
        db.session.commit()
        
        print(f"Placed bid: Brand #{brand_id}, Slot #{ad_slot_id}, {model_name}, Amount: ${amount}")
        return bid

def evaluate_bids(ad_slot_id):
    """Evaluate all bids for an ad slot"""
    with app.app_context():
        # Get the ad slot
        ad_slot = AdSlot.query.get(ad_slot_id)
        if not ad_slot:
            print(f"No ad slot found with ID {ad_slot_id}")
            return None
        
        # Get all active bids for this slot
        bids = Bid.query.filter_by(ad_slot_id=ad_slot_id, status="active").all()
        if not bids:
            print(f"No active bids found for slot {ad_slot_id}")
            return None
        
        # Import the bidding engine evaluation function
        from bidding_engine import evaluate_bids as engine_evaluate_bids
        
        # Evaluate bids
        results = engine_evaluate_bids(bids, ad_slot)
        
        # Print results
        print_bid_results(results)
        
        return results

def print_bid_results(results):
    """Pretty print bid evaluation results"""
    if not results:
        print("No bid evaluation results to display.")
        return
    
    print("\n" + "="*80)
    print("BID EVALUATION RESULTS")
    print("="*80)
    
    # Sort by value_per_impression (highest first)
    sorted_results = sorted(results, key=lambda x: x['value_per_impression'], reverse=True)
    
    for i, result in enumerate(sorted_results):
        winner = " (WINNER)" if i == 0 else ""
        print(f"{i+1}. {result['brand_name']} - {result['model_name']}")
        print(f"   Original bid: ${result['original_amount']:.2f}")
        print(f"   Value per impression: ${result['value_per_impression']:.6f}{winner}")
        
        # Show performance metrics if available
        if 'performance_metrics' in result:
            metrics = result['performance_metrics']
            print(f"   Performance: CTR {metrics.get('ctr', 0)*100:.2f}%, " +
                  f"CVR {metrics.get('cvr', 0)*100:.2f}%, " +
                  f"AOV ${metrics.get('aov', 0):.2f}")
        
        print()
    
    print("="*80)

def test_multi_model_bidding():
    """Test the multi-model predictive bidding system"""
    # Initialize demo data
    initialize_demo_data()
    
    # Get ad slots and brands
    slots = get_ad_slots()
    brands = get_brands()
    
    if not slots or not brands:
        print("Error: No slots or brands available for testing.")
        return
    
    # For simplicity, let's use the first ad slot
    ad_slot_id = slots[0].id
    
    # Clean up any existing bids for this slot
    with app.app_context():
        Bid.query.filter_by(ad_slot_id=ad_slot_id).delete()
        db.session.commit()
    
    # Place bids with different models
    place_bid(brands[0].id, ad_slot_id, 1, 45.0, 0.005, 0.1)  # CPA-Fixed
    place_bid(brands[1].id, ad_slot_id, 2, 0.08, 0.004, 0.12)  # CPA-Percentage
    place_bid(brands[2].id, ad_slot_id, 3, 1.75, 0.006, 0.09)  # CPC
    place_bid(brands[3].id, ad_slot_id, 4, 12.0, 0.007, 0.11)  # CPM
    
    # Evaluate the bids
    evaluate_bids(ad_slot_id)

if __name__ == "__main__":
    test_multi_model_bidding()