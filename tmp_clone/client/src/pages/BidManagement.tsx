import BidForm from "@/components/bidding/BidForm";
import BidHistory from "@/components/bidding/BidHistory";

const BidManagement = () => {
  return (
    <div>
      {/* Action Bar */}
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-800">Bidding Management</h2>
        <p className="mt-1 text-sm text-gray-600">Place bids on ad slots and view bid history</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <BidForm />
        </div>
        <div className="lg:col-span-2">
          <BidHistory />
        </div>
      </div>
    </div>
  );
};

export default BidManagement;
