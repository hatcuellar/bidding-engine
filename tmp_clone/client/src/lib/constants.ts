// Ad Slot Statuses
export const AD_SLOT_STATUSES = {
  ACTIVE: "active",
  PAUSED: "paused",
  UNDER_REVIEW: "under_review"
};

// Ad Slot Placements
export const AD_SLOT_PLACEMENTS = [
  "Header",
  "Footer",
  "Sidebar",
  "In-Content",
  "Pre-Roll",
  "Bottom Bar",
  "Right Sidebar"
];

// Bid Statuses
export const BID_STATUSES = {
  PENDING: "pending",
  ACCEPTED: "accepted",
  REJECTED: "rejected"
};

// Ad Size Types
export const AD_SIZE_TYPES = {
  BANNER: "banner",
  LEADERBOARD: "leaderboard",
  RECTANGLE: "rectangle",
  VIDEO: "video"
};

// Format currency amount
export const formatCurrency = (amount: number): string => {
  return `$${amount.toFixed(2)}`;
};

// Format CPM
export const formatCPM = (amount: number): string => {
  return `$${amount.toFixed(2)} CPM`;
};

// Format percentage
export const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

// Calculate percentage change
export const calculatePercentageChange = (current: number, previous: number): number => {
  if (previous === 0) return 0;
  return ((current - previous) / previous) * 100;
};

// Status color mapping
export const STATUS_COLORS = {
  [AD_SLOT_STATUSES.ACTIVE]: "green",
  [AD_SLOT_STATUSES.PAUSED]: "gray",
  [AD_SLOT_STATUSES.UNDER_REVIEW]: "yellow",
  [BID_STATUSES.PENDING]: "blue",
  [BID_STATUSES.ACCEPTED]: "green",
  [BID_STATUSES.REJECTED]: "red"
};

// Sample stats (would normally come from API)
export const SAMPLE_STATS = {
  activeSlots: 24,
  avgCpm: 5.42,
  fillRate: 94.8,
  activeSlotsTrend: 8,
  avgCpmTrend: 12,
  fillRateTrend: -2.1
};
