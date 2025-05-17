import { useQuery } from "@tanstack/react-query";
import { formatCPM } from "@/lib/constants";
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardFooter 
} from "@/components/ui/card";
import { Link } from "wouter";
import { Skeleton } from "@/components/ui/skeleton";
import { Advertiser } from "@shared/schema";

const advertisersWithMetadata = [
  {
    id: 1,
    name: "TechGiant Inc.",
    industry: "Technology",
    logo: "https://images.unsplash.com/photo-1622434641406-a158123450f9?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
    bidAmount: 8.46,
    bidChange: 12.5,
    winRate: 68
  },
  {
    id: 2,
    name: "ShopMart",
    industry: "Retail",
    logo: "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
    bidAmount: 7.21,
    bidChange: 8.3,
    winRate: 54
  },
  {
    id: 3,
    name: "FinSecure",
    industry: "Finance",
    logo: "https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
    bidAmount: 6.88,
    bidChange: -2.1,
    winRate: 42
  },
  {
    id: 4,
    name: "TravelEasy",
    industry: "Travel",
    logo: "https://images.unsplash.com/photo-1517479149777-5f3b1511d5ad?ixlib=rb-1.2.1&auto=format&fit=crop&w=48&h=48&q=80",
    bidAmount: 6.12,
    bidChange: 5.7,
    winRate: 38
  }
];

const TopAdvertisers = () => {
  const { data: advertisers, isLoading } = useQuery({
    queryKey: ['/api/advertisers'],
    select: (data: Advertiser[]) => {
      // In a real application, we would compute bid amounts, win rates, etc. from the API data
      // For now, we'll use our sample data
      return advertisersWithMetadata;
    }
  });

  return (
    <Card className="bg-white shadow-sm rounded-lg overflow-hidden">
      <CardHeader className="p-6 border-b border-gray-200">
        <CardTitle className="text-lg font-medium text-gray-900">Top Advertisers</CardTitle>
        <CardDescription className="mt-1 text-sm text-gray-500">Based on bid volume and win rate</CardDescription>
      </CardHeader>
      
      <CardContent className="p-0">
        <ul className="divide-y divide-gray-200">
          {isLoading ? (
            Array(4).fill(0).map((_, idx) => (
              <li key={idx} className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Skeleton className="h-10 w-10 rounded-full" />
                    <div className="ml-3">
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-3 w-16 mt-1" />
                    </div>
                  </div>
                  <div>
                    <Skeleton className="h-4 w-16" />
                    <Skeleton className="h-3 w-20 mt-1" />
                  </div>
                </div>
              </li>
            ))
          ) : advertisers && advertisers.map((advertiser) => (
            <li key={advertiser.id} className="p-4 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0 h-10 w-10 rounded-full overflow-hidden">
                    <img src={advertiser.logo} alt={`${advertiser.name} logo`} className="h-10 w-10 object-cover" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">{advertiser.name}</p>
                    <p className="text-sm text-gray-500">{advertiser.industry}</p>
                  </div>
                </div>
                <div>
                  <div className="flex items-center text-sm">
                    <span className="font-semibold text-gray-900">{formatCPM(advertiser.bidAmount)}</span>
                    <span className={`ml-2 px-2 py-0.5 rounded text-xs ${advertiser.bidChange >= 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {advertiser.bidChange >= 0 ? '+' : ''}{advertiser.bidChange}%
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">Win rate: {advertiser.winRate}%</div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
      
      <CardFooter className="p-4 bg-gray-50 border-t border-gray-200">
        <Link href="/advertisers" className="text-sm font-medium text-primary hover:text-blue-600">
          View all advertisers
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="ml-1 h-4 w-4 inline" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </CardFooter>
    </Card>
  );
};

export default TopAdvertisers;
