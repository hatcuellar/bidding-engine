import type { Express, Request, Response, NextFunction } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { 
  insertUserSchema, 
  insertAdvertiserSchema, 
  insertAdSlotSchema, 
  insertBidSchema,
  insertCampaignSchema,
  insertImpressionSchema
} from "@shared/schema";
import { ZodError } from "zod";
import biddingRouter from "../proxy_bidding_api";

export async function registerRoutes(app: Express): Promise<Server> {
  // Register the bidding router to proxy requests to the Python Flask API
  app.use(biddingRouter);
  
  // Error handling middleware for Zod validation errors
  function handleZodError(err: unknown, res: Response) {
    if (err instanceof ZodError) {
      return res.status(400).json({ 
        message: "Validation error", 
        errors: err.errors 
      });
    }
    console.error("Server error:", err);
    return res.status(500).json({ message: "Internal server error" });
  }

  // User routes
  app.post("/api/users", async (req: Request, res: Response) => {
    try {
      const userData = insertUserSchema.parse(req.body);
      const existingUser = await storage.getUserByUsername(userData.username);
      
      if (existingUser) {
        return res.status(409).json({ message: "Username already exists" });
      }
      
      const user = await storage.createUser(userData);
      return res.status(201).json({ 
        id: user.id, 
        username: user.username,
        email: user.email,
        role: user.role,
        companyName: user.companyName
      });
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.get("/api/users/:id", async (req: Request, res: Response) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ message: "Invalid user ID" });
      }
      
      const user = await storage.getUser(id);
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }
      
      return res.json({ 
        id: user.id, 
        username: user.username,
        email: user.email,
        role: user.role,
        companyName: user.companyName
      });
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  // Advertiser routes
  app.post("/api/advertisers", async (req: Request, res: Response) => {
    try {
      const advertiserData = insertAdvertiserSchema.parse(req.body);
      const advertiser = await storage.createAdvertiser(advertiserData);
      return res.status(201).json(advertiser);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.get("/api/advertisers", async (_req: Request, res: Response) => {
    try {
      const advertisers = await storage.getAllAdvertisers();
      return res.json(advertisers);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.get("/api/advertisers/:id", async (req: Request, res: Response) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ message: "Invalid advertiser ID" });
      }
      
      const advertiser = await storage.getAdvertiser(id);
      if (!advertiser) {
        return res.status(404).json({ message: "Advertiser not found" });
      }
      
      return res.json(advertiser);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.put("/api/advertisers/:id", async (req: Request, res: Response) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ message: "Invalid advertiser ID" });
      }
      
      const advertiserData = insertAdvertiserSchema.partial().parse(req.body);
      const advertiser = await storage.updateAdvertiser(id, advertiserData);
      
      if (!advertiser) {
        return res.status(404).json({ message: "Advertiser not found" });
      }
      
      return res.json(advertiser);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  // Ad Size routes
  app.get("/api/ad-sizes", async (_req: Request, res: Response) => {
    try {
      const adSizes = await storage.getAllAdSizes();
      return res.json(adSizes);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  // Ad Slot routes
  app.post("/api/ad-slots", async (req: Request, res: Response) => {
    try {
      const adSlotData = insertAdSlotSchema.parse(req.body);
      const adSlot = await storage.createAdSlot(adSlotData);
      return res.status(201).json(adSlot);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.get("/api/ad-slots", async (_req: Request, res: Response) => {
    try {
      const adSlots = await storage.getAllAdSlots();
      
      // For each ad slot, get the highest bid
      const adSlotsWithBids = await Promise.all(adSlots.map(async (slot) => {
        const highestBid = await storage.getHighestBidForAdSlot(slot.id);
        const bidCount = (await storage.getBidsByAdSlot(slot.id)).length;
        return {
          ...slot,
          currentBid: highestBid ? highestBid.amount : null,
          bidders: bidCount
        };
      }));
      
      return res.json(adSlotsWithBids);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.get("/api/ad-slots/:id", async (req: Request, res: Response) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ message: "Invalid ad slot ID" });
      }
      
      const adSlot = await storage.getAdSlot(id);
      if (!adSlot) {
        return res.status(404).json({ message: "Ad slot not found" });
      }
      
      // Get the highest bid and bid count for this ad slot
      const highestBid = await storage.getHighestBidForAdSlot(id);
      const bidCount = (await storage.getBidsByAdSlot(id)).length;
      
      return res.json({
        ...adSlot,
        currentBid: highestBid ? highestBid.amount : null,
        bidders: bidCount
      });
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.put("/api/ad-slots/:id", async (req: Request, res: Response) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ message: "Invalid ad slot ID" });
      }
      
      const adSlotData = insertAdSlotSchema.partial().parse(req.body);
      const adSlot = await storage.updateAdSlot(id, adSlotData);
      
      if (!adSlot) {
        return res.status(404).json({ message: "Ad slot not found" });
      }
      
      return res.json(adSlot);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.delete("/api/ad-slots/:id", async (req: Request, res: Response) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ message: "Invalid ad slot ID" });
      }
      
      const deleted = await storage.deleteAdSlot(id);
      if (!deleted) {
        return res.status(404).json({ message: "Ad slot not found" });
      }
      
      return res.status(204).send();
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.get("/api/publishers/:id/ad-slots", async (req: Request, res: Response) => {
    try {
      const publisherId = parseInt(req.params.id);
      if (isNaN(publisherId)) {
        return res.status(400).json({ message: "Invalid publisher ID" });
      }
      
      const adSlots = await storage.getAdSlotsByPublisher(publisherId);
      return res.json(adSlots);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  // Bid routes
  app.post("/api/bids", async (req: Request, res: Response) => {
    try {
      const bidData = insertBidSchema.parse(req.body);
      
      // Check if ad slot exists
      const adSlot = await storage.getAdSlot(bidData.adSlotId);
      if (!adSlot) {
        return res.status(404).json({ message: "Ad slot not found" });
      }
      
      // Check if advertiser exists
      const advertiser = await storage.getAdvertiser(bidData.advertiserId);
      if (!advertiser) {
        return res.status(404).json({ message: "Advertiser not found" });
      }
      
      // Check if bid meets floor price
      if (bidData.amount < adSlot.floorPrice) {
        return res.status(400).json({ message: `Bid must be at least ${adSlot.floorPrice}` });
      }
      
      const bid = await storage.createBid(bidData);
      return res.status(201).json(bid);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.get("/api/bids/ad-slots/:adSlotId", async (req: Request, res: Response) => {
    try {
      const adSlotId = parseInt(req.params.adSlotId);
      if (isNaN(adSlotId)) {
        return res.status(400).json({ message: "Invalid ad slot ID" });
      }
      
      const bids = await storage.getBidsByAdSlot(adSlotId);
      return res.json(bids);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.get("/api/bids/advertisers/:advertiserId", async (req: Request, res: Response) => {
    try {
      const advertiserId = parseInt(req.params.advertiserId);
      if (isNaN(advertiserId)) {
        return res.status(400).json({ message: "Invalid advertiser ID" });
      }
      
      const bids = await storage.getBidsByAdvertiser(advertiserId);
      return res.json(bids);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  // Campaign routes
  app.post("/api/campaigns", async (req: Request, res: Response) => {
    try {
      const campaignData = insertCampaignSchema.parse(req.body);
      
      // Check if advertiser exists
      const advertiser = await storage.getAdvertiser(campaignData.advertiserId);
      if (!advertiser) {
        return res.status(404).json({ message: "Advertiser not found" });
      }
      
      // Ensure budget is available
      if (campaignData.budget > advertiser.budget) {
        return res.status(400).json({ message: "Campaign budget exceeds advertiser budget" });
      }
      
      const campaign = await storage.createCampaign(campaignData);
      
      // Update advertiser budget
      await storage.updateAdvertiser(advertiser.id, {
        budget: advertiser.budget - campaignData.budget
      });
      
      return res.status(201).json(campaign);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.get("/api/campaigns/advertisers/:advertiserId", async (req: Request, res: Response) => {
    try {
      const advertiserId = parseInt(req.params.advertiserId);
      if (isNaN(advertiserId)) {
        return res.status(400).json({ message: "Invalid advertiser ID" });
      }
      
      const campaigns = await storage.getCampaignsByAdvertiser(advertiserId);
      return res.json(campaigns);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  // Ad Impression routes
  app.post("/api/impressions", async (req: Request, res: Response) => {
    try {
      const impressionData = insertImpressionSchema.parse(req.body);
      const impression = await storage.createImpression(impressionData);
      return res.status(201).json(impression);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.get("/api/impressions/ad-slots/:adSlotId", async (req: Request, res: Response) => {
    try {
      const adSlotId = parseInt(req.params.adSlotId);
      if (isNaN(adSlotId)) {
        return res.status(400).json({ message: "Invalid ad slot ID" });
      }
      
      const impressions = await storage.getImpressionsByAdSlot(adSlotId);
      return res.json(impressions);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  app.get("/api/impressions/advertisers/:advertiserId", async (req: Request, res: Response) => {
    try {
      const advertiserId = parseInt(req.params.advertiserId);
      if (isNaN(advertiserId)) {
        return res.status(400).json({ message: "Invalid advertiser ID" });
      }
      
      const impressions = await storage.getImpressionsByAdvertiser(advertiserId);
      return res.json(impressions);
    } catch (err) {
      return handleZodError(err, res);
    }
  });

  // Initialize demo data (for testing and development)
  app.post("/api/init-demo-data", async (_req: Request, res: Response) => {
    try {
      // Create demo users
      const publisher = await storage.createUser({
        username: "demoPublisher",
        password: "password123",
        email: "publisher@example.com",
        role: "publisher",
        companyName: "Demo Publisher"
      });
      
      const advertiserUser = await storage.createUser({
        username: "demoAdvertiser",
        password: "password123",
        email: "advertiser@example.com",
        role: "advertiser",
        companyName: "Demo Advertiser"
      });
      
      // Create demo advertisers
      const techGiant = await storage.createAdvertiser({
        userId: advertiserUser.id,
        name: "TechGiant Inc.",
        industry: "Technology",
        logo: "https://images.unsplash.com/photo-1622434641406-a158123450f9?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
        website: "https://techgiant.example.com",
        budget: 10000
      });
      
      await storage.createAdvertiser({
        userId: advertiserUser.id,
        name: "ShopMart",
        industry: "Retail",
        logo: "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
        website: "https://shopmart.example.com",
        budget: 8000
      });
      
      await storage.createAdvertiser({
        userId: advertiserUser.id,
        name: "FinSecure",
        industry: "Finance",
        logo: "https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
        website: "https://finsecure.example.com",
        budget: 12000
      });
      
      await storage.createAdvertiser({
        userId: advertiserUser.id,
        name: "TravelEasy",
        industry: "Travel",
        logo: "https://images.unsplash.com/photo-1517479149777-5f3b1511d5ad?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
        website: "https://traveleasy.example.com",
        budget: 7500
      });
      
      // Create demo ad slots
      const adSizes = await storage.getAllAdSizes();
      
      const homePageBanner = await storage.createAdSlot({
        publisherId: publisher.id,
        name: "Homepage Banner",
        website: "mysite.com",
        placement: "Header",
        sizeId: adSizes[0].id, // Leaderboard size
        floorPrice: 3.50,
        status: "active"
      });
      
      await storage.createAdSlot({
        publisherId: publisher.id,
        name: "Article Sidebar",
        website: "mysite.com",
        placement: "Right Sidebar",
        sizeId: adSizes[1].id, // Medium Rectangle size
        floorPrice: 2.75,
        status: "active"
      });
      
      await storage.createAdSlot({
        publisherId: publisher.id,
        name: "Mobile App Banner",
        website: "myapp.com",
        placement: "Bottom Bar",
        sizeId: adSizes[2].id, // Mobile Banner size
        floorPrice: 2.00,
        status: "under_review"
      });
      
      await storage.createAdSlot({
        publisherId: publisher.id,
        name: "Video Pre-Roll",
        website: "myvideos.com",
        placement: "Pre-Roll",
        sizeId: adSizes[4].id, // Video size
        floorPrice: 8.00,
        status: "paused"
      });
      
      // Create demo bids
      await storage.createBid({
        advertiserId: techGiant.id,
        adSlotId: homePageBanner.id,
        amount: 6.24,
        status: "accepted"
      });
      
      return res.status(200).json({ message: "Demo data initialized successfully" });
    } catch (err) {
      console.error("Error initializing demo data:", err);
      return res.status(500).json({ message: "Error initializing demo data" });
    }
  });

  const httpServer = createServer(app);
  
  return httpServer;
}
