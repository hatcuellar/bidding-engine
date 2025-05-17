import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bid, Advertiser, AdSlot } from "@shared/schema";
import { formatCPM, BID_STATUSES } from "@/lib/constants";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { AdSlotWithBids } from "@/components/adslots/AdSlotTable";

// Extended type for UI display with advertiser and ad slot info
type ExtendedBid = Bid & {
  advertiser?: Advertiser;
  adSlot?: AdSlot;
};

const BidHistory = () => {
  const [selectedAdSlotId, setSelectedAdSlotId] = useState<number | null>(null);
  
  const { data: adSlots, isLoading: isLoadingAdSlots } = useQuery<AdSlotWithBids[]>({
    queryKey: ['/api/ad-slots'],
  });

  const { data: advertisers, isLoading: isLoadingAdvertisers } = useQuery<Advertiser[]>({
    queryKey: ['/api/advertisers'],
  });

  // In a real app, we'd fetch bids for a specific ad slot
  // For demo purposes, we'll create a sample bid history
  const [bids, setBids] = useState<ExtendedBid[]>([]);
  
  // Initialize with some sample bids for demonstration
  useEffect(() => {
    if (adSlots && advertisers) {
      // Create sample bid history
      const sampleBids: ExtendedBid[] = [];
      
      for (let i = 0; i < 8; i++) {
        const adSlot = adSlots[i % adSlots.length];
        const advertiser = advertisers[i % advertisers.length];
        
        if (adSlot && advertiser) {
          sampleBids.push({
            id: i + 1,
            advertiserId: advertiser.id,
            adSlotId: adSlot.id,
            amount: adSlot.currentBid ? adSlot.currentBid - (Math.random() * 2) : 5 + (Math.random() * 5),
            status: Object.values(BID_STATUSES)[i % 3],
            createdAt: new Date(Date.now() - (i * 3600000)), // Hours ago
            advertiser,
            adSlot,
          });
        }
      }
      
      setBids(sampleBids);
    }
  }, [adSlots, advertisers]);

  // Filter bids by selected ad slot
  const filteredBids = selectedAdSlotId 
    ? bids.filter(bid => bid.adSlotId === selectedAdSlotId)
    : bids;
  
  const isLoading = isLoadingAdSlots || isLoadingAdvertisers;

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case BID_STATUSES.ACCEPTED:
        return "bg-green-100 text-green-800";
      case BID_STATUSES.REJECTED:
        return "bg-red-100 text-red-800";
      case BID_STATUSES.PENDING:
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case BID_STATUSES.ACCEPTED:
        return "Accepted";
      case BID_STATUSES.REJECTED:
        return "Rejected";
      case BID_STATUSES.PENDING:
        return "Pending";
      default:
        return status;
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-40 mb-2" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <Skeleton className="h-10 w-48" />
          </div>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead><Skeleton className="h-4 w-24" /></TableHead>
                  <TableHead><Skeleton className="h-4 w-24" /></TableHead>
                  <TableHead><Skeleton className="h-4 w-24" /></TableHead>
                  <TableHead><Skeleton className="h-4 w-24" /></TableHead>
                  <TableHead><Skeleton className="h-4 w-24" /></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Array(4).fill(0).map((_, idx) => (
                  <TableRow key={idx}>
                    <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                    <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Bid History</CardTitle>
        <CardDescription>
          View recent bids placed across all ad slots
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <select 
            className="px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
            value={selectedAdSlotId || ""}
            onChange={(e) => setSelectedAdSlotId(e.target.value ? parseInt(e.target.value) : null)}
          >
            <option value="">All Ad Slots</option>
            {adSlots?.map((slot) => (
              <option key={slot.id} value={slot.id}>
                {slot.name} - {slot.website}
              </option>
            ))}
          </select>
        </div>
        
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Advertiser</TableHead>
                <TableHead>Ad Slot</TableHead>
                <TableHead>Bid Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredBids.length > 0 ? (
                filteredBids.map((bid) => (
                  <TableRow key={bid.id} className="hover:bg-gray-50">
                    <TableCell>
                      <div className="flex items-center">
                        {bid.advertiser?.logo ? (
                          <img 
                            src={bid.advertiser.logo} 
                            alt={`${bid.advertiser.name} logo`} 
                            className="h-8 w-8 rounded-full mr-2 object-cover" 
                          />
                        ) : (
                          <div className="h-8 w-8 bg-primary/10 rounded-full mr-2 flex items-center justify-center">
                            <span className="text-primary font-medium">
                              {bid.advertiser?.name?.charAt(0) || 'A'}
                            </span>
                          </div>
                        )}
                        <span className="font-medium text-sm">
                          {bid.advertiser?.name || `Advertiser #${bid.advertiserId}`}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {bid.adSlot?.name || `Ad Slot #${bid.adSlotId}`}
                      </div>
                      <div className="text-xs text-gray-500">
                        {bid.adSlot?.website || 'Unknown website'}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium text-green-600">
                        {formatCPM(bid.amount)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusBadgeColor(bid.status)}>
                        {getStatusLabel(bid.status)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm text-gray-500">
                        {new Date(bid.createdAt).toLocaleTimeString([], { 
                          hour: '2-digit', 
                          minute: '2-digit',
                          hour12: true 
                        })}
                      </div>
                      <div className="text-xs text-gray-400">
                        {new Date(bid.createdAt).toLocaleDateString()}
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-6 text-gray-500">
                    No bid history found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default BidHistory;
