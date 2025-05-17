import { useState } from "react";
import { useLocation } from "wouter";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet";
import Sidebar from "./Sidebar";
import { Button } from "@/components/ui/button";

const Header = () => {
  const [location] = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const getPageTitle = () => {
    switch (location) {
      case "/":
        return "Dashboard";
      case "/ad-slots":
        return "Ad Slots";
      case "/advertisers":
        return "Advertisers";
      case "/bidding":
        return "Bidding";
      case "/analytics":
        return "Analytics";
      case "/campaigns":
        return "Campaigns";
      case "/revenue":
        return "Revenue";
      case "/profile":
        return "Profile";
      case "/settings":
        return "Settings";
      default:
        return "Dashboard";
    }
  };

  return (
    <header className="bg-white shadow-sm flex items-center justify-between px-6 py-3">
      <div className="flex items-center md:hidden">
        <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="text-gray-600 hover:text-gray-900">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-6 w-6" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M4 6h16M4 12h16M4 18h16" 
                />
              </svg>
              <span className="sr-only">Open main menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="p-0 bg-gray-900 text-white">
            <Sidebar />
          </SheetContent>
        </Sheet>
      </div>
      
      <div className="flex-1 md:pl-8">
        <h1 className="text-xl font-semibold text-gray-800">{getPageTitle()}</h1>
      </div>
      
      <div className="flex items-center">
        <button className="text-gray-600 hover:text-gray-900 mx-3 relative focus:outline-none">
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-6 w-6" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" 
            />
          </svg>
          <span className="absolute top-0 right-0 h-2 w-2 bg-red-500 rounded-full"></span>
        </button>
        
        <div className="relative">
          <button className="flex items-center focus:outline-none" id="user-menu">
            <img 
              className="h-8 w-8 rounded-full object-cover" 
              src="https://images.unsplash.com/photo-1568602471122-7832951cc4c5?ixlib=rb-4.0.3&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80" 
              alt="User avatar" 
            />
            <span className="ml-2 hidden md:block font-medium">John Smith</span>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="ml-2 h-4 w-4 hidden md:block" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M19 9l-7 7-7-7" 
              />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
