import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";

const Sidebar = () => {
  const [location] = useLocation();

  const isActive = (path: string) => {
    return location === path;
  };

  return (
    <div className="bg-gray-900 text-white w-64 flex-shrink-0 hidden md:flex md:flex-col">
      <div className="p-4 flex items-center border-b border-gray-800">
        <span className="text-2xl font-bold text-white">AdBid</span>
        <span className="ml-2 text-primary text-xs bg-blue-900 px-2 py-1 rounded-full">BETA</span>
      </div>
      
      <div className="py-4 flex-1 overflow-y-auto">
        <div className="px-4 py-2 text-xs uppercase text-gray-400 font-semibold">Publisher Tools</div>
        <Link href="/">
          <a className={cn(
            "flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors",
            isActive("/") && "bg-gray-800 text-white"
          )}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="w-5 h-5" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
            <span className="ml-3">Dashboard</span>
          </a>
        </Link>
        <Link href="/ad-slots">
          <a className={cn(
            "flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors",
            isActive("/ad-slots") && "bg-gray-800 text-white"
          )}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="w-5 h-5" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
              <path d="M16 3L12 7 8 3"></path>
            </svg>
            <span className="ml-3">Ad Slots</span>
          </a>
        </Link>
        <Link href="/analytics">
          <a className={cn(
            "flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors",
            isActive("/analytics") && "bg-gray-800 text-white"
          )}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="w-5 h-5" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <line x1="12" y1="20" x2="12" y2="10"></line>
              <line x1="18" y1="20" x2="18" y2="4"></line>
              <line x1="6" y1="20" x2="6" y2="16"></line>
            </svg>
            <span className="ml-3">Analytics</span>
          </a>
        </Link>
        <Link href="/revenue">
          <a className={cn(
            "flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors",
            isActive("/revenue") && "bg-gray-800 text-white"
          )}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="w-5 h-5" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <line x1="12" y1="1" x2="12" y2="23"></line>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
            </svg>
            <span className="ml-3">Revenue</span>
          </a>
        </Link>
        
        <div className="px-4 py-2 mt-6 text-xs uppercase text-gray-400 font-semibold">Advertiser Tools</div>
        <Link href="/campaigns">
          <a className={cn(
            "flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors",
            isActive("/campaigns") && "bg-gray-800 text-white"
          )}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="w-5 h-5" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            <span className="ml-3">Campaigns</span>
          </a>
        </Link>
        <Link href="/bidding">
          <a className={cn(
            "flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors",
            isActive("/bidding") && "bg-gray-800 text-white"
          )}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="w-5 h-5" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
            </svg>
            <span className="ml-3">Bidding</span>
          </a>
        </Link>
        <Link href="/advertisers">
          <a className={cn(
            "flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors",
            isActive("/advertisers") && "bg-gray-800 text-white"
          )}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="w-5 h-5" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <path d="M20 7h-9"></path>
              <path d="M14 17H5"></path>
              <circle cx="17" cy="17" r="3"></circle>
              <circle cx="7" cy="7" r="3"></circle>
            </svg>
            <span className="ml-3">Advertisers</span>
          </a>
        </Link>
        
        <div className="px-4 py-2 mt-6 text-xs uppercase text-gray-400 font-semibold">Account</div>
        <Link href="/profile">
          <a className={cn(
            "flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors",
            isActive("/profile") && "bg-gray-800 text-white"
          )}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="w-5 h-5" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span className="ml-3">Profile</span>
          </a>
        </Link>
        <Link href="/settings">
          <a className={cn(
            "flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-white transition-colors",
            isActive("/settings") && "bg-gray-800 text-white"
          )}>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="w-5 h-5" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
            </svg>
            <span className="ml-3">Settings</span>
          </a>
        </Link>
      </div>
    </div>
  );
};

export default Sidebar;
