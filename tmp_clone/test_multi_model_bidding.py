"""
Test Script for Multi-Model Predictive Bidding System

This script demonstrates the multi-model predictive bidding system in action.
It initializes the database, creates test data, and runs simulations with
different bidding models (CPA, CPC, CPM) to show how they are normalized and evaluated.
"""

import os
import sys
from flask import Flask
from dotenv import load_dotenv
from models import db, initialize_db, create_sample_data, BidModel, Bid, AdSlot, Brand
from bidding_engine import evaluate_bids, normalize_bid_to_impression_value

# Load environment variables
load_dotenv()

# Create a test Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def reset_database():
    """Reset and initialize the database with sample data"""
    with app.app_context():
        initialize_db(app)
        db.create_all()
        success = create_sample_data()
        return success

def place_test_bids():
    """Place test bids with different models"""
    with app.app_context():
        # Get the first ad slot
        ad_slot = AdSlot.query.first()
        if not ad_slot:
            print("No ad slots found. Make sure database is initialized.")
            return False
        
        # Get brands
        brands = Brand.query.all()
        if not brands or len(brands) < 4:
            print("Not enough brands found. Make sure database is initialized.")
            return False
        
        # Clear any existing bids for this slot
        Bid.query.filter_by(ad_slot_id=ad_slot.id).delete()
        db.session.commit()
        
        # Create test bids with different models
        test_bids = []
        
        # CPA-Fixed model (model_id=1)
        cpa_fixed_bid = Bid(
            brand_id=brands[0].id,
            ad_slot_id=ad_slot.id,
            model_id=1,  # CPA-Fixed
            amount=45.0,  # $45 per acquisition
            min_threshold=0.005,
            max_threshold=0.1,
            status="active"
        )
        test_bids.append(cpa_fixed_bid)
        
        # CPA-Percentage model (model_id=2)
        cpa_percentage_bid = Bid(
            brand_id=brands[1].id,
            ad_slot_id=ad_slot.id,
            model_id=2,  # CPA-Percentage
            amount=0.08,  # 8% of order value
            min_threshold=0.004,
            max_threshold=0.12,
            status="active"
        )
        test_bids.append(cpa_percentage_bid)
        
        # CPC model (model_id=3)
        cpc_bid = Bid(
            brand_id=brands[2].id,
            ad_slot_id=ad_slot.id,
            model_id=3,  # CPC
            amount=1.75,  # $1.75 per click
            min_threshold=0.006,
            max_threshold=0.09,
            status="active"
        )
        test_bids.append(cpc_bid)
        
        # CPM model (model_id=4)
        cpm_bid = Bid(
            brand_id=brands[3].id,
            ad_slot_id=ad_slot.id,
            model_id=4,  # CPM
            amount=12.0,  # $12 per 1000 impressions
            min_threshold=0.007,
            max_threshold=0.11,
            status="active"
        )
        test_bids.append(cpm_bid)
        
        # Save all bids
        db.session.add_all(test_bids)
        db.session.commit()
        
        return True

def evaluate_test_bids():
    """Evaluate the test bids and print results"""
    with app.app_context():
        # Get the first ad slot
        ad_slot = AdSlot.query.first()
        if not ad_slot:
            print("No ad slots found.")
            return False
        
        # Get bids for this slot
        bids = Bid.query.filter_by(ad_slot_id=ad_slot.id, status="active").all()
        if not bids:
            print("No active bids found for this slot.")
            return False
        
        print(f"\n{'-'*80}")
        print(f"EVALUATING BIDS FOR AD SLOT: {ad_slot.name}")
        print(f"Placement: {ad_slot.placement}, Floor Price: ${ad_slot.floor_price}")
        print(f"{'-'*80}")
        
        # Evaluate each bid independently to show the process
        for bid in bids:
            brand = Brand.query.get(bid.brand_id)
            model = BidModel.query.get(bid.model_id)
            
            print(f"\nBrand: {brand.name} ({brand.industry})")
            print(f"Model: {model.name}")
            print(f"Original Bid: ${bid.amount}")
            
            # Get historical performance data
            from bidding_engine import get_historical_performance
            performance = get_historical_performance(brand.id, ad_slot.id)
            
            # Display performance metrics
            if hasattr(performance, 'to_dict'):
                ctr = performance.ctr
                cvr = performance.cvr
                aov = performance.aov
            else:
                ctr = performance.get('ctr', 0)
                cvr = performance.get('cvr', 0)
                aov = performance.get('aov', 0)
                
            print(f"Performance Metrics:")
            print(f" - CTR: {ctr:.4f} ({ctr*100:.2f}%)")
            print(f" - CVR: {cvr:.4f} ({cvr*100:.2f}%)")
            print(f" - AOV: ${aov:.2f}")
            
            # Step 1: Normalize to impression value
            base_value = normalize_bid_to_impression_value(bid, performance)
            print(f"Step 1 - Base value per impression: ${base_value:.6f}")
            
            # Step 2: Apply brand strategy
            from bidding_engine import apply_brand_strategy
            strategy_adjusted = apply_brand_strategy(brand, base_value)
            print(f"Step 2 - After brand strategy ({brand.strategy}): ${strategy_adjusted:.6f}")
            
            # Step 3: Apply quality factors
            from bidding_engine import apply_quality_factors
            quality_adjusted = apply_quality_factors(strategy_adjusted, ad_slot)
            print(f"Step 3 - After quality factors: ${quality_adjusted:.6f}")
            
            # Step 4: Apply thresholds
            final_value = quality_adjusted
            if bid.min_threshold and final_value < bid.min_threshold:
                print(f"Value ${final_value:.6f} below min threshold ${bid.min_threshold:.6f}")
                final_value = 0
            elif bid.max_threshold and final_value > bid.max_threshold:
                print(f"Value ${final_value:.6f} above max threshold ${bid.max_threshold:.6f}")
                final_value = bid.max_threshold
                
            print(f"Final normalized value: ${final_value:.6f}")
        
        # Evaluate all bids together
        print(f"\n{'-'*80}")
        print("FINAL BID EVALUATION AND WINNER DETERMINATION")
        print(f"{'-'*80}")
        
        # Use the bidding engine to evaluate all bids
        bid_values = evaluate_bids(bids, ad_slot)
        
        # Sort by value per impression
        bid_values.sort(key=lambda x: x['value_per_impression'], reverse=True)
        
        # Print results
        for i, bid in enumerate(bid_values):
            print(f"{i+1}. {bid['brand_name']} - {bid['model_name']} - ${bid['original_amount']:.2f} - ${bid['value_per_impression']:.6f}" + 
                  (" (WINNER)" if i == 0 else ""))
        
        return True

def run_test():
    """Run the complete test of the multi-model predictive bidding system"""
    print("MULTI-MODEL PREDICTIVE BIDDING SYSTEM TEST")
    print("==========================================")
    
    print("\nStep 1: Initializing Database...")
    if not reset_database():
        print("Error initializing database. Exiting.")
        return False
    print("Database initialized successfully.")
    
    print("\nStep 2: Placing Test Bids...")
    if not place_test_bids():
        print("Error placing test bids. Exiting.")
        return False
    print("Test bids placed successfully.")
    
    print("\nStep 3: Evaluating Bids...")
    evaluate_test_bids()
    
    print("\nTest completed successfully!")
    return True

if __name__ == "__main__":
    # Run the test
    success = run_test()
    if not success:
        sys.exit(1)