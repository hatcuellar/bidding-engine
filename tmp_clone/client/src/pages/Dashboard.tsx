import { useQuery } from "@tanstack/react-query";
import { AdSlot, Advertiser } from "@shared/schema";
import { Link } from "wouter";
import { SAMPLE_STATS, formatCPM } from "@/lib/constants";

import StatsCard from "@/components/dashboard/StatsCard";
import BidActivityChart from "@/components/dashboard/BidActivityChart";
import TopAdvertisers from "@/components/dashboard/TopAdvertisers";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AdSlotWithBids } from "@/components/adslots/AdSlotTable";

const Dashboard = () => {
  const { data: adSlots, isLoading: isLoadingAdSlots } = useQuery<AdSlotWithBids[]>({
    queryKey: ['/api/ad-slots'],
  });

  const { data: advertisers, isLoading: isLoadingAdvertisers } = useQuery<Advertiser[]>({
    queryKey: ['/api/advertisers'],
  });

  // Calculate stats from data
  const stats = {
    activeSlots: adSlots?.filter(slot => slot.status === 'active').length || 0,
    avgCpm: adSlots?.reduce((sum, slot) => sum + (slot.currentBid || 0), 0) / 
      (adSlots?.filter(slot => slot.currentBid !== null).length || 1),
    fillRate: adSlots ? 
      (adSlots.filter(slot => slot.currentBid !== null).length / adSlots.length) * 100 : 0,
    activeSlotsTrend: SAMPLE_STATS.activeSlotsTrend, // Sample trend data
    avgCpmTrend: SAMPLE_STATS.avgCpmTrend, // Sample trend data
    fillRateTrend: SAMPLE_STATS.fillRateTrend, // Sample trend data
  };

  const isLoading = isLoadingAdSlots || isLoadingAdvertisers;

  return (
    <div>
      {/* Action Bar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-800">Dashboard</h2>
          <p className="mt-1 text-sm text-gray-600">Welcome to your ad bidding platform control center</p>
        </div>
        <div className="mt-4 md:mt-0 flex flex-col sm:flex-row gap-3">
          <Button variant="outline" className="flex items-center">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-4 w-4 mr-2" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Export Data
          </Button>
          <Link href="/ad-slots">
            <Button className="flex items-center">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-4 w-4 mr-2" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Create New Ad Slot
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {isLoading ? (
          // Loading skeletons for stats cards
          Array(3).fill(0).map((_, idx) => (
            <div key={idx} className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center">
                <Skeleton className="h-12 w-12 rounded-md" />
                <div className="ml-4">
                  <Skeleton className="h-4 w-32 mb-2" />
                  <Skeleton className="h-8 w-24" />
                </div>
              </div>
            </div>
          ))
        ) : (
          <>
            <StatsCard 
              title="Active Ad Slots"
              value={stats.activeSlots}
              trend={stats.activeSlotsTrend}
              icon={
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  className="h-6 w-6 text-primary" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
                  />
                </svg>
              }
              iconBgColor="bg-blue-100"
            />
            
            <StatsCard 
              title="Avg. CPM"
              value={formatCPM(stats.avgCpm)}
              trend={stats.avgCpmTrend}
              icon={
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  className="h-6 w-6 text-secondary" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                  />
                </svg>
              }
              iconBgColor="bg-green-100"
            />
            
            <StatsCard 
              title="Fill Rate"
              value={`${stats.fillRate.toFixed(1)}%`}
              trend={stats.fillRateTrend}
              icon={
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  className="h-6 w-6 text-accent" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" 
                  />
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" 
                  />
                </svg>
              }
              iconBgColor="bg-purple-100"
            />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BidActivityChart />
        <TopAdvertisers />
      </div>
    </div>
  );
};

export default Dashboard;
