import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: string | number;
  trend?: number;
  icon: React.ReactNode;
  iconBgColor: string;
}

const StatsCard = ({ title, value, trend, icon, iconBgColor }: StatsCardProps) => {
  const trendDirection = trend ? (trend > 0 ? "up" : "down") : null;
  const trendColor = trendDirection === "up" ? "text-green-600" : "text-red-600";
  
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center">
        <div className={cn(
          "flex-shrink-0 h-12 w-12 rounded-md flex items-center justify-center",
          iconBgColor
        )}>
          {icon}
        </div>
        <div className="ml-4">
          <h3 className="text-sm font-medium text-gray-500">{title}</h3>
          <div className="flex items-end">
            <p className="text-2xl font-semibold text-gray-900">{value}</p>
            {trend !== undefined && (
              <span className={cn("ml-2 text-sm flex items-center", trendColor)}>
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  className="h-4 w-4 mr-1" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d={trendDirection === "up" ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"} 
                  />
                </svg>
                {Math.abs(trend)}%
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatsCard;
