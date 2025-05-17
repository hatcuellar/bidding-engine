import { useState } from "react";
import AdSlotTable from "@/components/adslots/AdSlotTable";
import CreateAdSlotForm from "@/components/adslots/CreateAdSlotForm";
import { Button } from "@/components/ui/button";

const AdSlots = () => {
  const [isCreateFormOpen, setIsCreateFormOpen] = useState(false);

  return (
    <>
      {/* Action Bar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-800">Manage Ad Slots</h2>
          <p className="mt-1 text-sm text-gray-600">Create and manage ad slots for your websites and apps</p>
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Filter
          </Button>
          <Button 
            className="flex items-center"
            onClick={() => setIsCreateFormOpen(true)}
          >
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
        </div>
      </div>

      {/* Ad Slots Table */}
      <AdSlotTable onCreateClick={() => setIsCreateFormOpen(true)} />

      {/* Create Ad Slot Form Modal */}
      <CreateAdSlotForm 
        isOpen={isCreateFormOpen} 
        onClose={() => setIsCreateFormOpen(false)} 
      />
    </>
  );
};

export default AdSlots;
