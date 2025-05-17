# Multi-Model Ad Bidding Engine API v1.0.0

A high-performance multi-model ad-bidding engine with FastAPI

## Endpoints

### Bid

#### POST /api/bid/calculate

Calculate Bid

Calculate bid value based on provided parameters.

Request body contains:
- brand_id: ID of the brand/advertiser
- bid_amount: Original bid amount
- bid_type: Type of bid (CPA, CPC, CPM)
- ad_slot: Information about the ad placement

---

#### GET /api/bid/history/{brand_id}

Get Bid History

Get bid history for a specific brand.

Path parameters:
- brand_id: ID of the brand/advertiser

Query parameters:
- limit: Number of records to return (default 10)

---

#### POST /api/bid/strategy

Update Brand Strategy

Create or update brand bidding strategy.

Request body contains:
- brand_id: ID of the brand/advertiser
- vpi_multiplier: Value-per-impression multiplier
- priority: Priority level for the brand
- strategy_config: Additional configuration as JSON

---

#### GET /api/bid/strategy/{brand_id}

Get Brand Strategy

Get strategy configuration for a brand.

Path parameters:
- brand_id: ID of the brand/advertiser

---

### Creatives

#### GET /api/creatives/

List Creatives

List creatives with optional filtering.

Query parameters:
- brand_id: Filter by brand ID
- status: Filter by status (pending, approved, rejected)
- skip: Number of records to skip (pagination)
- limit: Maximum number of records to return

---

#### GET /api/creatives/

List Creatives

List creatives with optional filtering.

Query parameters:
- brand_id: Filter by brand ID
- status: Filter by status (pending, approved, rejected)
- skip: Number of records to skip (pagination)
- limit: Maximum number of records to return

---

#### GET /api/creatives/{creative_id}

Get Creative

Get details of a specific creative.

Path parameters:
- creative_id: ID of the creative

---

#### GET /api/creatives/{creative_id}

Get Creative

Get details of a specific creative.

Path parameters:
- creative_id: ID of the creative

---

#### PATCH /api/creatives/{creative_id}

Update Creative Status

Admin endpoint to approve or reject creatives.

Path parameters:
- creative_id: ID of the creative to update

Request body:
- status: New status ("pending", "approved", or "rejected")
- reject_reason: Optional reason for rejection

---

#### PATCH /api/creatives/{creative_id}

Update Creative Status

Admin endpoint to approve or reject creatives.

Path parameters:
- creative_id: ID of the creative to update

Request body:
- status: New status ("pending", "approved", or "rejected")
- reject_reason: Optional reason for rejection

---

### Health

#### GET /healthz

Health Check

Health check endpoint to verify API and database are operational.
Returns 200 OK if everything is working.

---

### Roas

#### POST /api/roas/performance

Ingest Performance Event

Ingest actual click, impression, and conversion events to update the feature store.

This endpoint receives performance data from the Partnerize platform to update
the historical data used for ROAS predictions. Events are deduplicated based on event_id.

Request body contains:
- event_id: Unique identifier for deduplication
- type: Type of event (impression, click, conversion)
- brand_id: ID of the advertiser
- partner_id: ID of the publisher partner
- ad_slot_id: ID of the ad placement
- timestamp: When the event occurred
- metadata: Additional information about the event
- revenue: Optional revenue amount (for conversions)

---

#### POST /api/roas/retrain

Retrain Roas Model

Trigger retraining of the ROAS prediction model using latest performance data.

This endpoint is typically called by a scheduled job but can also be
manually triggered for immediate retraining.

---

#### GET /api/roas/roas

Get Roas Prediction

Get predicted ROAS (Return on Ad Spend) for a specific brand-partner-slot combination.

This endpoint is used for reporting and forecasting purposes.

Parameters:
- brand_id: ID of the advertiser
- partner_id: ID of the publisher partner
- ad_slot_id: ID of the ad placement
- device_type: Optional device type (0=unknown, 1=desktop, 2=mobile, 3=tablet)
- creative_type: Optional creative type (0=unknown, 1=image, 2=video, 3=native)

---

### Untagged

#### GET /

Root

---

#### GET /guide

Api Guide

---

## Models

### AdSlotInfo

Information about an ad placement slot

---

### BidHistoryEntry

Single bid history entry

---

### BidHistoryResponse

Response model for bid history

---

### BidRequest

Bid request model with all necessary parameters

---

### BidResponse

Response model for bid calculations

---

### BrandStrategyRequest

Request model for updating brand strategy

---

### BrandStrategyResponse

Response model for brand strategy

---

### BrandStrategyResult

Wrapper for brand strategy response

---

### CreativeResponse

Response model for creative assets

---

### CreativeStatusUpdate

Request model for updating creative status (admin use only)

---

### HTTPValidationError

---

### HealthResponse

Health check response model

---

### PerformanceEventRequest

Request model for performance event ingestion

---

### ROASPredictionResponse

Response model for ROAS prediction

---

### ValidationError

---

