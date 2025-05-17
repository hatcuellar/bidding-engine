import { 
  users, type User, type InsertUser,
  advertisers, type Advertiser, type InsertAdvertiser,
  adSizes, type AdSize, type InsertAdSize,
  adSlots, type AdSlot, type InsertAdSlot,
  bids, type Bid, type InsertBid,
  campaigns, type Campaign, type InsertCampaign,
  adImpressions, type AdImpression, type InsertImpression
} from "@shared/schema";

export interface IStorage {
  // User operations
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  // Advertiser operations
  getAdvertiser(id: number): Promise<Advertiser | undefined>;
  getAdvertiserByUserId(userId: number): Promise<Advertiser | undefined>;
  getAllAdvertisers(): Promise<Advertiser[]>;
  createAdvertiser(advertiser: InsertAdvertiser): Promise<Advertiser>;
  updateAdvertiser(id: number, advertiser: Partial<InsertAdvertiser>): Promise<Advertiser | undefined>;
  
  // Ad Size operations
  getAdSize(id: number): Promise<AdSize | undefined>;
  getAllAdSizes(): Promise<AdSize[]>;
  createAdSize(adSize: InsertAdSize): Promise<AdSize>;
  
  // Ad Slot operations
  getAdSlot(id: number): Promise<AdSlot | undefined>;
  getAdSlotsByPublisher(publisherId: number): Promise<AdSlot[]>;
  getAllAdSlots(): Promise<AdSlot[]>;
  createAdSlot(adSlot: InsertAdSlot): Promise<AdSlot>;
  updateAdSlot(id: number, adSlot: Partial<InsertAdSlot>): Promise<AdSlot | undefined>;
  deleteAdSlot(id: number): Promise<boolean>;
  
  // Bid operations
  getBid(id: number): Promise<Bid | undefined>;
  getBidsByAdvertiser(advertiserId: number): Promise<Bid[]>;
  getBidsByAdSlot(adSlotId: number): Promise<Bid[]>;
  createBid(bid: InsertBid): Promise<Bid>;
  updateBid(id: number, bid: Partial<InsertBid>): Promise<Bid | undefined>;
  getHighestBidForAdSlot(adSlotId: number): Promise<Bid | undefined>;
  
  // Campaign operations
  getCampaign(id: number): Promise<Campaign | undefined>;
  getCampaignsByAdvertiser(advertiserId: number): Promise<Campaign[]>;
  createCampaign(campaign: InsertCampaign): Promise<Campaign>;
  updateCampaign(id: number, campaign: Partial<InsertCampaign>): Promise<Campaign | undefined>;
  
  // Ad Impression operations
  getImpressionsByAdSlot(adSlotId: number): Promise<AdImpression[]>;
  getImpressionsByAdvertiser(advertiserId: number): Promise<AdImpression[]>;
  createImpression(impression: InsertImpression): Promise<AdImpression>;
  updateImpression(id: number, impression: Partial<InsertImpression>): Promise<AdImpression | undefined>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private advertisers: Map<number, Advertiser>;
  private adSizes: Map<number, AdSize>;
  private adSlots: Map<number, AdSlot>;
  private bids: Map<number, Bid>;
  private campaigns: Map<number, Campaign>;
  private impressions: Map<number, AdImpression>;
  
  private userId: number;
  private advertiserId: number;
  private adSizeId: number;
  private adSlotId: number;
  private bidId: number;
  private campaignId: number;
  private impressionId: number;

  constructor() {
    this.users = new Map();
    this.advertisers = new Map();
    this.adSizes = new Map();
    this.adSlots = new Map();
    this.bids = new Map();
    this.campaigns = new Map();
    this.impressions = new Map();
    
    this.userId = 1;
    this.advertiserId = 1;
    this.adSizeId = 1;
    this.adSlotId = 1;
    this.bidId = 1;
    this.campaignId = 1;
    this.impressionId = 1;
    
    // Initialize default ad sizes
    this.initializeAdSizes();
  }

  private initializeAdSizes() {
    const defaultSizes: InsertAdSize[] = [
      { name: "Leaderboard", width: 728, height: 90, type: "leaderboard" },
      { name: "Medium Rectangle", width: 300, height: 250, type: "rectangle" },
      { name: "Mobile Banner", width: 320, height: 50, type: "banner" },
      { name: "Large Rectangle", width: 336, height: 280, type: "rectangle" },
      { name: "Video", width: 640, height: 360, type: "video" }
    ];
    
    defaultSizes.forEach(size => {
      this.createAdSize(size);
    });
  }

  // User operations
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.userId++;
    const createdAt = new Date();
    const user: User = { ...insertUser, id, createdAt };
    this.users.set(id, user);
    return user;
  }
  
  // Advertiser operations
  async getAdvertiser(id: number): Promise<Advertiser | undefined> {
    return this.advertisers.get(id);
  }
  
  async getAdvertiserByUserId(userId: number): Promise<Advertiser | undefined> {
    return Array.from(this.advertisers.values()).find(
      (advertiser) => advertiser.userId === userId,
    );
  }
  
  async getAllAdvertisers(): Promise<Advertiser[]> {
    return Array.from(this.advertisers.values());
  }
  
  async createAdvertiser(insertAdvertiser: InsertAdvertiser): Promise<Advertiser> {
    const id = this.advertiserId++;
    const createdAt = new Date();
    const advertiser: Advertiser = { ...insertAdvertiser, id, createdAt };
    this.advertisers.set(id, advertiser);
    return advertiser;
  }
  
  async updateAdvertiser(id: number, advertiserUpdate: Partial<InsertAdvertiser>): Promise<Advertiser | undefined> {
    const advertiser = this.advertisers.get(id);
    if (!advertiser) return undefined;
    
    const updatedAdvertiser = { ...advertiser, ...advertiserUpdate };
    this.advertisers.set(id, updatedAdvertiser);
    return updatedAdvertiser;
  }
  
  // Ad Size operations
  async getAdSize(id: number): Promise<AdSize | undefined> {
    return this.adSizes.get(id);
  }
  
  async getAllAdSizes(): Promise<AdSize[]> {
    return Array.from(this.adSizes.values());
  }
  
  async createAdSize(insertAdSize: InsertAdSize): Promise<AdSize> {
    const id = this.adSizeId++;
    const adSize: AdSize = { ...insertAdSize, id };
    this.adSizes.set(id, adSize);
    return adSize;
  }
  
  // Ad Slot operations
  async getAdSlot(id: number): Promise<AdSlot | undefined> {
    return this.adSlots.get(id);
  }
  
  async getAdSlotsByPublisher(publisherId: number): Promise<AdSlot[]> {
    return Array.from(this.adSlots.values()).filter(
      (adSlot) => adSlot.publisherId === publisherId,
    );
  }
  
  async getAllAdSlots(): Promise<AdSlot[]> {
    return Array.from(this.adSlots.values());
  }
  
  async createAdSlot(insertAdSlot: InsertAdSlot): Promise<AdSlot> {
    const id = this.adSlotId++;
    const createdAt = new Date();
    const adSlot: AdSlot = { ...insertAdSlot, id, createdAt };
    this.adSlots.set(id, adSlot);
    return adSlot;
  }
  
  async updateAdSlot(id: number, adSlotUpdate: Partial<InsertAdSlot>): Promise<AdSlot | undefined> {
    const adSlot = this.adSlots.get(id);
    if (!adSlot) return undefined;
    
    const updatedAdSlot = { ...adSlot, ...adSlotUpdate };
    this.adSlots.set(id, updatedAdSlot);
    return updatedAdSlot;
  }
  
  async deleteAdSlot(id: number): Promise<boolean> {
    return this.adSlots.delete(id);
  }
  
  // Bid operations
  async getBid(id: number): Promise<Bid | undefined> {
    return this.bids.get(id);
  }
  
  async getBidsByAdvertiser(advertiserId: number): Promise<Bid[]> {
    return Array.from(this.bids.values()).filter(
      (bid) => bid.advertiserId === advertiserId,
    );
  }
  
  async getBidsByAdSlot(adSlotId: number): Promise<Bid[]> {
    return Array.from(this.bids.values()).filter(
      (bid) => bid.adSlotId === adSlotId,
    );
  }
  
  async createBid(insertBid: InsertBid): Promise<Bid> {
    const id = this.bidId++;
    const createdAt = new Date();
    const bid: Bid = { ...insertBid, id, createdAt };
    this.bids.set(id, bid);
    return bid;
  }
  
  async updateBid(id: number, bidUpdate: Partial<InsertBid>): Promise<Bid | undefined> {
    const bid = this.bids.get(id);
    if (!bid) return undefined;
    
    const updatedBid = { ...bid, ...bidUpdate };
    this.bids.set(id, updatedBid);
    return updatedBid;
  }
  
  async getHighestBidForAdSlot(adSlotId: number): Promise<Bid | undefined> {
    const bids = await this.getBidsByAdSlot(adSlotId);
    if (bids.length === 0) return undefined;
    
    return bids.reduce((highest, current) => {
      return current.amount > highest.amount ? current : highest;
    }, bids[0]);
  }
  
  // Campaign operations
  async getCampaign(id: number): Promise<Campaign | undefined> {
    return this.campaigns.get(id);
  }
  
  async getCampaignsByAdvertiser(advertiserId: number): Promise<Campaign[]> {
    return Array.from(this.campaigns.values()).filter(
      (campaign) => campaign.advertiserId === advertiserId,
    );
  }
  
  async createCampaign(insertCampaign: InsertCampaign): Promise<Campaign> {
    const id = this.campaignId++;
    const createdAt = new Date();
    const campaign: Campaign = { ...insertCampaign, id, createdAt };
    this.campaigns.set(id, campaign);
    return campaign;
  }
  
  async updateCampaign(id: number, campaignUpdate: Partial<InsertCampaign>): Promise<Campaign | undefined> {
    const campaign = this.campaigns.get(id);
    if (!campaign) return undefined;
    
    const updatedCampaign = { ...campaign, ...campaignUpdate };
    this.campaigns.set(id, updatedCampaign);
    return updatedCampaign;
  }
  
  // Ad Impression operations
  async getImpressionsByAdSlot(adSlotId: number): Promise<AdImpression[]> {
    return Array.from(this.impressions.values()).filter(
      (impression) => impression.adSlotId === adSlotId,
    );
  }
  
  async getImpressionsByAdvertiser(advertiserId: number): Promise<AdImpression[]> {
    return Array.from(this.impressions.values()).filter(
      (impression) => impression.advertiserId === advertiserId,
    );
  }
  
  async createImpression(insertImpression: InsertImpression): Promise<AdImpression> {
    const id = this.impressionId++;
    const impression: AdImpression = { ...insertImpression, id };
    this.impressions.set(id, impression);
    return impression;
  }
  
  async updateImpression(id: number, impressionUpdate: Partial<InsertImpression>): Promise<AdImpression | undefined> {
    const impression = this.impressions.get(id);
    if (!impression) return undefined;
    
    const updatedImpression = { ...impression, ...impressionUpdate };
    this.impressions.set(id, updatedImpression);
    return updatedImpression;
  }
}

// Initialize and export storage instance
export const storage = new MemStorage();
