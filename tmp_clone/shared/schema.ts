import { pgTable, text, serial, integer, boolean, timestamp, doublePrecision } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// User schema for authentication (extended from original)
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  email: text("email").notNull(),
  role: text("role").notNull().default("publisher"), // 'publisher' or 'advertiser'
  companyName: text("company_name"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Advertiser schema
export const advertisers = pgTable("advertisers", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").notNull().references(() => users.id),
  name: text("name").notNull(),
  industry: text("industry").notNull(),
  logo: text("logo"),
  website: text("website"),
  budget: doublePrecision("budget").notNull().default(0),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Ad slot sizes and formats
export const adSizes = pgTable("ad_sizes", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  width: integer("width").notNull(),
  height: integer("height").notNull(),
  type: text("type").notNull(), // 'banner', 'leaderboard', 'rectangle', etc.
});

// Ad slots schema
export const adSlots = pgTable("ad_slots", {
  id: serial("id").primaryKey(),
  publisherId: integer("publisher_id").notNull().references(() => users.id),
  name: text("name").notNull(),
  website: text("website").notNull(),
  placement: text("placement").notNull(), // 'header', 'sidebar', 'footer', etc.
  sizeId: integer("size_id").references(() => adSizes.id),
  floorPrice: doublePrecision("floor_price").notNull().default(0), // minimum bid price
  status: text("status").notNull().default("active"), // 'active', 'paused', 'under_review'
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Bids schema
export const bids = pgTable("bids", {
  id: serial("id").primaryKey(),
  advertiserId: integer("advertiser_id").notNull().references(() => advertisers.id),
  adSlotId: integer("ad_slot_id").notNull().references(() => adSlots.id),
  amount: doublePrecision("amount").notNull(), // CPM bid amount
  status: text("status").notNull().default("pending"), // 'pending', 'accepted', 'rejected'
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Ad campaigns
export const campaigns = pgTable("campaigns", {
  id: serial("id").primaryKey(),
  advertiserId: integer("advertiser_id").notNull().references(() => advertisers.id),
  name: text("name").notNull(),
  targetCPM: doublePrecision("target_cpm").notNull(),
  budget: doublePrecision("budget").notNull(),
  status: text("status").notNull().default("active"), // 'active', 'paused', 'completed'
  startDate: timestamp("start_date").notNull(),
  endDate: timestamp("end_date"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Ad impressions and performance
export const adImpressions = pgTable("ad_impressions", {
  id: serial("id").primaryKey(),
  adSlotId: integer("ad_slot_id").notNull().references(() => adSlots.id),
  advertiserId: integer("advertiser_id").notNull().references(() => advertisers.id),
  campaignId: integer("campaign_id").references(() => campaigns.id),
  impressions: integer("impressions").notNull().default(0),
  clicks: integer("clicks").notNull().default(0),
  revenue: doublePrecision("revenue").notNull().default(0),
  date: timestamp("date").defaultNow().notNull(),
});

// Create insert schemas
export const insertUserSchema = createInsertSchema(users).omit({
  id: true,
  createdAt: true,
});

export const insertAdvertiserSchema = createInsertSchema(advertisers).omit({
  id: true,
  createdAt: true,
});

export const insertAdSizeSchema = createInsertSchema(adSizes).omit({
  id: true,
});

export const insertAdSlotSchema = createInsertSchema(adSlots).omit({
  id: true,
  createdAt: true,
});

export const insertBidSchema = createInsertSchema(bids).omit({
  id: true,
  createdAt: true,
});

export const insertCampaignSchema = createInsertSchema(campaigns).omit({
  id: true,
  createdAt: true,
});

export const insertImpressionSchema = createInsertSchema(adImpressions).omit({
  id: true,
});

// Create insert types
export type InsertUser = z.infer<typeof insertUserSchema>;
export type InsertAdvertiser = z.infer<typeof insertAdvertiserSchema>;
export type InsertAdSize = z.infer<typeof insertAdSizeSchema>;
export type InsertAdSlot = z.infer<typeof insertAdSlotSchema>;
export type InsertBid = z.infer<typeof insertBidSchema>;
export type InsertCampaign = z.infer<typeof insertCampaignSchema>;
export type InsertImpression = z.infer<typeof insertImpressionSchema>;

// Create select types
export type User = typeof users.$inferSelect;
export type Advertiser = typeof advertisers.$inferSelect;
export type AdSize = typeof adSizes.$inferSelect;
export type AdSlot = typeof adSlots.$inferSelect;
export type Bid = typeof bids.$inferSelect;
export type Campaign = typeof campaigns.$inferSelect;
export type AdImpression = typeof adImpressions.$inferSelect;
