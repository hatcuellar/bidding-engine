from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import json

db = SQLAlchemy()

def initialize_db(app):
    db.init_app(app)

class BrandStrategy(db.Model):
    __tablename__ = 'brand_strategies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    vpi_multiplier = db.Column(db.Float, default=1.0, nullable=False)  # Value Per Impression multiplier
    priority = db.Column(db.Integer, default=0)  # For ordering in UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    brands = db.relationship('Brand', backref='strategy_config', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'vpi_multiplier': self.vpi_multiplier,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Brand(db.Model):
    __tablename__ = 'brands'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(255))
    website = db.Column(db.String(255))
    budget = db.Column(db.Float, default=0)
    strategy_id = db.Column(db.Integer, db.ForeignKey('brand_strategies.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bids = db.relationship('Bid', backref='brand', lazy=True, cascade="all, delete-orphan")
    campaigns = db.relationship('Campaign', backref='brand', lazy=True, cascade="all, delete-orphan")
    performances = db.relationship('Performance', backref='brand', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'industry': self.industry,
            'logo_url': self.logo_url,
            'website': self.website,
            'budget': self.budget,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy_config.name if self.strategy_config else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Partner(db.Model):
    __tablename__ = 'partners'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(255))
    quality_score = db.Column(db.Float, default=0.5)  # 0-1 score for partner quality
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ad_slots = db.relationship('AdSlot', backref='partner', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'website': self.website,
            'quality_score': self.quality_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AdSize(db.Model):
    __tablename__ = 'ad_sizes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # banner, leaderboard, rectangle, etc.
    
    # Relationships
    ad_slots = db.relationship('AdSlot', backref='ad_size', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'type': self.type
        }

class AdSlot(db.Model):
    __tablename__ = 'ad_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    partner_id = db.Column(db.Integer, db.ForeignKey('partners.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    placement = db.Column(db.String(50), nullable=False)  # header, sidebar, footer, etc.
    size_id = db.Column(db.Integer, db.ForeignKey('ad_sizes.id'))
    floor_price = db.Column(db.Float, default=0)  # minimum bid price
    status = db.Column(db.String(20), default='active')  # active, paused, under_review
    placement_score = db.Column(db.Float, default=0.5)  # 0-1 score for placement quality
    content_category = db.Column(db.String(50))  # category of content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bids = db.relationship('Bid', backref='ad_slot', lazy=True, cascade="all, delete-orphan")
    performances = db.relationship('Performance', backref='ad_slot', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        # Get the current highest bid information
        highest_bid = None
        bid_count = 0
        
        for bid in self.bids:
            if bid.status == 'active':
                bid_count += 1
                if highest_bid is None or bid.normalized_value > highest_bid:
                    highest_bid = bid.normalized_value
        
        # Get the ad size information
        size_info = self.ad_size.to_dict() if self.ad_size else None
        
        return {
            'id': self.id,
            'partner_id': self.partner_id,
            'partner_name': self.partner.name if self.partner else None,
            'name': self.name,
            'placement': self.placement,
            'size_id': self.size_id,
            'ad_size': size_info,
            'floor_price': self.floor_price,
            'status': self.status,
            'placement_score': self.placement_score,
            'content_category': self.content_category,
            'current_bid': highest_bid,
            'bidders': bid_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class BidModel(db.Model):
    __tablename__ = 'bid_models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # CPA-Fixed, CPA-Percentage, CPC, CPM
    description = db.Column(db.String(255))
    
    # Relationships
    bids = db.relationship('Bid', backref='model', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class Bid(db.Model):
    __tablename__ = 'bids'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    ad_slot_id = db.Column(db.Integer, db.ForeignKey('ad_slots.id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('bid_models.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # The bid amount
    min_threshold = db.Column(db.Float)  # Minimum threshold defined by brand
    max_threshold = db.Column(db.Float)  # Maximum threshold defined by brand
    normalized_value = db.Column(db.Float)  # Value per impression (calculated)
    status = db.Column(db.String(20), default='pending')  # pending, active, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'brand_id': self.brand_id,
            'brand_name': self.brand.name if self.brand else None,
            'ad_slot_id': self.ad_slot_id,
            'ad_slot_name': self.ad_slot.name if self.ad_slot else None,
            'model_id': self.model_id,
            'model_name': self.model.name if self.model else None,
            'amount': self.amount,
            'min_threshold': self.min_threshold,
            'max_threshold': self.max_threshold,
            'normalized_value': self.normalized_value,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_cpm = db.Column(db.Float, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, paused, completed
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    impressions = db.relationship('AdImpression', backref='campaign', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'brand_id': self.brand_id,
            'name': self.name,
            'target_cpm': self.target_cpm,
            'budget': self.budget,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Performance(db.Model):
    __tablename__ = 'performances'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'))
    ad_slot_id = db.Column(db.Integer, db.ForeignKey('ad_slots.id'))
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    revenue = db.Column(db.Float, default=0)
    ctr = db.Column(db.Float)  # Click-through rate
    cvr = db.Column(db.Float)  # Conversion rate
    aov = db.Column(db.Float)  # Average order value
    device_type = db.Column(db.String(20))  # mobile, desktop, tablet
    date = db.Column(db.Date, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'brand_id': self.brand_id,
            'ad_slot_id': self.ad_slot_id,
            'impressions': self.impressions,
            'clicks': self.clicks,
            'conversions': self.conversions,
            'revenue': self.revenue,
            'ctr': self.ctr,
            'cvr': self.cvr,
            'aov': self.aov,
            'device_type': self.device_type,
            'date': self.date.isoformat() if self.date else None
        }

class AdImpression(db.Model):
    __tablename__ = 'ad_impressions'
    
    id = db.Column(db.Integer, primary_key=True)
    ad_slot_id = db.Column(db.Integer, db.ForeignKey('ad_slots.id'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    revenue = db.Column(db.Float, default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ad_slot_id': self.ad_slot_id,
            'brand_id': self.brand_id,
            'campaign_id': self.campaign_id,
            'impressions': self.impressions,
            'clicks': self.clicks,
            'conversions': self.conversions,
            'revenue': self.revenue,
            'date': self.date.isoformat() if self.date else None
        }

def create_sample_data():
    """Initialize the database with sample data for demo purposes"""
    try:
        # Clear existing data
        db.session.query(AdImpression).delete()
        db.session.query(Performance).delete()
        db.session.query(Bid).delete()
        db.session.query(Campaign).delete()
        db.session.query(AdSlot).delete()
        db.session.query(AdSize).delete()
        db.session.query(Brand).delete()
        db.session.query(Partner).delete()
        db.session.query(BidModel).delete()
        db.session.query(BrandStrategy).delete()
        db.session.commit()
        
        # Create bid models
        bid_models = [
            BidModel(name="CPA-Fixed", description="Fixed cost per acquisition"),
            BidModel(name="CPA-Percentage", description="Percentage of order value"),
            BidModel(name="CPC", description="Cost per click"),
            BidModel(name="CPM", description="Cost per mille (1000 impressions)")
        ]
        db.session.add_all(bid_models)
        db.session.commit()

        # Create brand strategies
        brand_strategies = [
            BrandStrategy(name="Maximize ROI", description="Focus on generating the highest return on investment", vpi_multiplier=1.25, priority=1),
            BrandStrategy(name="Maximize Reach", description="Focus on reaching the largest audience possible", vpi_multiplier=1.1, priority=2),
            BrandStrategy(name="Minimize CPA/CPC", description="Focus on reducing cost per acquisition or click", vpi_multiplier=0.9, priority=3),
            BrandStrategy(name="Even budget pacing", description="Spend budget evenly over campaign duration", vpi_multiplier=1.0, priority=4),
            BrandStrategy(name="Balanced", description="Balance between volume and efficiency", vpi_multiplier=1.0, priority=0)
        ]
        db.session.add_all(brand_strategies)
        db.session.commit()
        
        # Create ad sizes
        ad_sizes = [
            AdSize(name="Leaderboard", width=728, height=90, type="leaderboard"),
            AdSize(name="Medium Rectangle", width=300, height=250, type="rectangle"),
            AdSize(name="Mobile Banner", width=320, height=50, type="banner"),
            AdSize(name="Large Rectangle", width=336, height=280, type="rectangle"),
            AdSize(name="Video", width=640, height=360, type="video")
        ]
        db.session.add_all(ad_sizes)
        db.session.commit()
        
        # Create brands
        brands = [
            Brand(name="TechGiant Inc.", industry="Technology", 
                  logo_url="https://images.unsplash.com/photo-1622434641406-a158123450f9?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
                  website="https://techgiant.example.com", budget=10000, strategy_id=1),  # Maximize ROI
            Brand(name="ShopMart", industry="Retail", 
                  logo_url="https://images.unsplash.com/photo-1600880292203-757bb62b4baf?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
                  website="https://shopmart.example.com", budget=8000, strategy_id=2),  # Maximize Reach
            Brand(name="FinSecure", industry="Finance", 
                  logo_url="https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
                  website="https://finsecure.example.com", budget=12000, strategy_id=3),  # Minimize CPA/CPC
            Brand(name="TravelEasy", industry="Travel", 
                  logo_url="https://images.unsplash.com/photo-1517479149777-5f3b1511d5ad?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
                  website="https://traveleasy.example.com", budget=7500, strategy_id=4)   # Even budget pacing
        ]
        db.session.add_all(brands)
        db.session.commit()
        
        # Create partners
        partners = [
            Partner(name="News Daily", website="newsdaily.example.com", quality_score=0.85),
            Partner(name="Sports Hub", website="sportshub.example.com", quality_score=0.78),
            Partner(name="Tech Review", website="techreview.example.com", quality_score=0.92),
            Partner(name="Fashion Blog", website="fashionblog.example.com", quality_score=0.72)
        ]
        db.session.add_all(partners)
        db.session.commit()
        
        # Create ad slots
        ad_slots = [
            AdSlot(partner_id=1, name="Homepage Banner", placement="Header", size_id=1, 
                   floor_price=3.50, status="active", placement_score=0.9, content_category="News"),
            AdSlot(partner_id=1, name="Article Sidebar", placement="Right Sidebar", size_id=2, 
                   floor_price=2.75, status="active", placement_score=0.8, content_category="News"),
            AdSlot(partner_id=2, name="Game Results Top", placement="Header", size_id=1, 
                   floor_price=4.00, status="active", placement_score=0.85, content_category="Sports"),
            AdSlot(partner_id=2, name="Player Profiles", placement="In-Content", size_id=4, 
                   floor_price=3.25, status="active", placement_score=0.8, content_category="Sports"),
            AdSlot(partner_id=3, name="Review Header", placement="Header", size_id=1, 
                   floor_price=5.00, status="active", placement_score=0.95, content_category="Technology"),
            AdSlot(partner_id=3, name="Product Comparison", placement="In-Content", size_id=2, 
                   floor_price=4.50, status="active", placement_score=0.9, content_category="Technology"),
            AdSlot(partner_id=4, name="Style Guide Top", placement="Header", size_id=1, 
                   floor_price=3.75, status="active", placement_score=0.75, content_category="Fashion"),
            AdSlot(partner_id=4, name="Seasonal Trends", placement="Bottom Bar", size_id=3, 
                   floor_price=2.50, status="active", placement_score=0.7, content_category="Fashion")
        ]
        db.session.add_all(ad_slots)
        db.session.commit()
        
        # Create campaigns for each brand
        start_date = datetime.utcnow()
        campaigns = []
        
        for brand in brands:
            campaign = Campaign(
                brand_id=brand.id,
                name=f"{brand.name} Summer Campaign",
                target_cpm=7.50,
                budget=2000.00,
                status="active",
                start_date=start_date
            )
            campaigns.append(campaign)
        
        db.session.add_all(campaigns)
        db.session.commit()
        
        # Create performance data (historical performance for predictive models)
        performances = []
        for brand in brands:
            for ad_slot in ad_slots:
                # Create realistic CTR/CVR/AOV metrics that vary by placement, content, etc.
                base_ctr = random.uniform(0.005, 0.02)  # Base CTR between 0.5% and 2%
                
                # Adjust CTR based on placement quality and relevance
                placement_factor = ad_slot.placement_score
                ctr = base_ctr * placement_factor
                
                # Conversion rates vary by brand and vertical
                base_cvr = random.uniform(0.02, 0.08)  # Base CVR between 2% and 8%
                
                # Different brands have different conversion rates
                brand_factor = 1.0
                if brand.industry == "Retail" and ad_slot.content_category in ["Fashion", "Sports"]:
                    brand_factor = 1.5  # Retail brands do better on fashion/sports content
                elif brand.industry == "Technology" and ad_slot.content_category == "Technology":
                    brand_factor = 1.8  # Tech brands do much better on tech content
                
                cvr = base_cvr * brand_factor * placement_factor
                
                # Average order values vary by brand
                base_aov = 0
                if brand.industry == "Retail":
                    base_aov = random.uniform(50, 120)
                elif brand.industry == "Technology":
                    base_aov = random.uniform(100, 500)
                elif brand.industry == "Finance":
                    base_aov = random.uniform(200, 1000)
                elif brand.industry == "Travel":
                    base_aov = random.uniform(300, 800)
                
                # Create impression/click/conversion counts
                impressions = random.randint(10000, 50000)
                clicks = int(impressions * ctr)
                conversions = int(clicks * cvr)
                revenue = conversions * base_aov
                
                performance = Performance(
                    brand_id=brand.id,
                    ad_slot_id=ad_slot.id,
                    impressions=impressions,
                    clicks=clicks,
                    conversions=conversions,
                    revenue=revenue,
                    ctr=ctr,
                    cvr=cvr,
                    aov=base_aov,
                    device_type=random.choice(["mobile", "desktop", "tablet"])
                )
                performances.append(performance)
                
        db.session.add_all(performances)
        db.session.commit()
        
        # Create some active bids with different models
        bids = []
        
        # TechGiant CPM bids
        bids.append(Bid(
            brand_id=1, ad_slot_id=5, model_id=4,  # TechGiant CPM bid on Tech Review Header
            amount=8.50, min_threshold=5.0, max_threshold=15.0,
            status="active", normalized_value=0.0085  # $8.50 CPM = $0.0085 per impression
        ))
        
        # ShopMart CPC bids
        bids.append(Bid(
            brand_id=2, ad_slot_id=7, model_id=3,  # ShopMart CPC bid on Style Guide Top
            amount=1.25, min_threshold=0.75, max_threshold=2.0,
            status="active", normalized_value=0.0125  # Value to be calculated by bidding engine
        ))
        
        # FinSecure CPA-Fixed bids
        bids.append(Bid(
            brand_id=3, ad_slot_id=1, model_id=1,  # FinSecure CPA-Fixed bid on Homepage Banner
            amount=45.00, min_threshold=30.0, max_threshold=60.0,
            status="active", normalized_value=0.081  # Value to be calculated by bidding engine
        ))
        
        # TravelEasy CPA-Percentage bids
        bids.append(Bid(
            brand_id=4, ad_slot_id=3, model_id=2,  # TravelEasy CPA-Percentage bid on Game Results Top
            amount=0.08, min_threshold=0.05, max_threshold=0.15,  # 8% of order value
            status="active", normalized_value=0.0152  # Value to be calculated by bidding engine
        ))
        
        db.session.add_all(bids)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample data: {e}")
        return False