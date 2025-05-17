import { AdSlot, AdSize, Advertiser, Bid, Campaign, AdImpression } from "@shared/schema";

// Extended types for UI components

// Bid with associated advertiser and ad slot info
export interface ExtendedBid extends Bid {
  advertiser?: Advertiser;
  adSlot?: AdSlot;
}

// Ad slot with bid information
export interface AdSlotWithBids extends AdSlot {
  currentBid?: number | null;
  bidCount?: number;
  adSize?: AdSize;
}

// Advertiser with performance metrics
export interface AdvertiserWithMetrics extends Advertiser {
  bidCount?: number;
  winRate?: number;
  avgBid?: number;
}

// Campaign with performance metrics
export interface CampaignWithMetrics extends Campaign {
  impressions?: number;
  clicks?: number;
  ctr?: number;
  spend?: number;
}

// Chart data types
export interface ChartDataPoint {
  name: string;
  value: number;
  color?: string;
}

export interface TimeSeriesDataPoint {
  timestamp: string | Date;
  [key: string]: number | string | Date;
}

// Dashboard stats
export interface DashboardStats {
  activeSlots: number;
  avgCpm: number;
  fillRate: number;
  activeSlotsTrend: number;
  avgCpmTrend: number;
  fillRateTrend: number;
}

// Notification type
export interface Notification {
  id: string;
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  type: 'info' | 'success' | 'warning' | 'error';
}
