import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from "recharts";

// Sample data for the chart
const generateSampleData = () => {
  const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`);
  const bidData = [4.2, 4.1, 4.0, 3.9, 3.8, 3.9, 4.1, 4.4, 4.8, 5.2, 5.6, 5.8, 5.7, 5.6, 5.5, 5.6, 5.8, 6.0, 6.1, 6.2, 6.0, 5.7, 5.3, 4.8];
  const volumeData = [120, 105, 90, 75, 60, 80, 110, 140, 180, 210, 230, 240, 235, 225, 215, 225, 240, 260, 270, 280, 260, 230, 200, 160];
  
  return hours.map((hour, index) => ({
    hour,
    avgBid: bidData[index],
    bidVolume: volumeData[index]
  }));
};

const BidActivityChart = () => {
  const data = generateSampleData();

  return (
    <Card className="bg-white shadow-sm rounded-lg overflow-hidden">
      <CardHeader className="p-6 border-b border-gray-200">
        <CardTitle className="text-lg font-medium text-gray-900">Real-Time Bid Activity</CardTitle>
        <CardDescription className="mt-1 text-sm text-gray-500">Last 24 hours of bidding activity</CardDescription>
      </CardHeader>
      <CardContent className="p-6">
        <div className="h-[240px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip 
                formatter={(value, name) => {
                  if (name === "avgBid") return [`$${value} CPM`, "Avg Bid"];
                  return [value, "Bid Volume"];
                }}
              />
              <Legend />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="avgBid" 
                stroke="#3B82F6" 
                name="Avg Bid (CPM $)"
                strokeWidth={2} 
                dot={false}
                activeDot={{ r: 6 }}
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="bidVolume" 
                stroke="#8B5CF6" 
                name="Bid Volume"
                strokeWidth={2} 
                dot={false}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
};

export default BidActivityChart;
