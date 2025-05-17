import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AdSize } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";
import { formatCPM } from "@/lib/constants";
import { useToast } from "@/hooks/use-toast";
import { AdSlotWithBids } from "./AdSlotTable";
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogFooter 
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { 
  Form, 
  FormControl, 
  FormField, 
  FormItem, 
  FormLabel, 
  FormMessage 
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertAdSlotSchema } from "@shared/schema";
import { z } from "zod";
import { AD_SLOT_PLACEMENTS, AD_SLOT_STATUSES } from "@/lib/constants";

interface AdSlotModalProps {
  adSlot: AdSlotWithBids;
  isOpen: boolean;
  onClose: () => void;
  mode: "view" | "edit";
}

const AdSlotModal = ({ adSlot, isOpen, onClose, mode }: AdSlotModalProps) => {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  const { data: adSizes } = useQuery<AdSize[]>({
    queryKey: ['/api/ad-sizes'],
  });
  
  const getStatusLabel = (status: string) => {
    switch (status) {
      case "active":
        return "Active";
      case "paused":
        return "Paused";
      case "under_review":
        return "Under Review";
      default:
        return status;
    }
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "text-green-600";
      case "paused":
        return "text-gray-600";
      case "under_review":
        return "text-yellow-600";
      default:
        return "text-gray-600";
    }
  };
  
  // Form setup for edit mode
  const formSchema = insertAdSlotSchema.partial().extend({
    id: z.number(),
  });
  
  type FormValues = z.infer<typeof formSchema>;
  
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      id: adSlot.id,
      name: adSlot.name,
      website: adSlot.website,
      placement: adSlot.placement,
      sizeId: adSlot.sizeId,
      floorPrice: adSlot.floorPrice,
      status: adSlot.status,
    },
  });
  
  const updateAdSlotMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const { id, ...rest } = values;
      return apiRequest("PUT", `/api/ad-slots/${id}`, rest);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/ad-slots'] });
      toast({
        title: "Ad slot updated",
        description: "The ad slot has been successfully updated.",
      });
      onClose();
    },
    onError: (error) => {
      toast({
        title: "Error updating ad slot",
        description: error instanceof Error ? error.message : "An unknown error occurred",
        variant: "destructive",
      });
    }
  });
  
  const onSubmit = (values: FormValues) => {
    updateAdSlotMutation.mutate(values);
  };
  
  if (mode === "view") {
    // View mode content
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle className="text-lg font-medium text-gray-900">
              Ad Slot Details: {adSlot.name}
            </DialogTitle>
          </DialogHeader>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 py-4">
            <div>
              <div className="mb-6">
                <h4 className="text-md font-medium text-gray-700 mb-2">Ad Slot Details</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-gray-500">Size</div>
                    <div className="text-sm font-medium">
                      {adSlot.adSize ? `${adSlot.adSize.width} x ${adSlot.adSize.height} px` : "Unknown"}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Type</div>
                    <div className="text-sm font-medium">{adSlot.adSize?.type || "Unknown"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Placement</div>
                    <div className="text-sm font-medium">{adSlot.placement}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Website</div>
                    <div className="text-sm font-medium">{adSlot.website}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Status</div>
                    <div className={`text-sm font-medium ${getStatusColor(adSlot.status)}`}>
                      {getStatusLabel(adSlot.status)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Created</div>
                    <div className="text-sm font-medium">
                      {new Date(adSlot.createdAt).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="text-md font-medium text-gray-700 mb-2">Current Bidding</h4>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex justify-between items-center mb-3">
                    <div className="text-sm font-medium text-gray-900">Current Highest Bid</div>
                    <div className="text-lg font-semibold text-green-600">
                      {adSlot.currentBid ? formatCPM(adSlot.currentBid) : "No bids"}
                    </div>
                  </div>
                  <div className="flex justify-between items-center mb-3">
                    <div className="text-sm font-medium text-gray-900">Number of Bidders</div>
                    <div className="text-sm font-medium">{adSlot.bidders}</div>
                  </div>
                  <div className="flex justify-between items-center mb-3">
                    <div className="text-sm font-medium text-gray-900">Bid Updated</div>
                    <div className="text-sm font-medium">recently</div>
                  </div>
                  <div className="flex justify-between items-center">
                    <div className="text-sm font-medium text-gray-900">Floor Price</div>
                    <div className="text-sm font-medium">{formatCPM(adSlot.floorPrice)}</div>
                  </div>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="text-md font-medium text-gray-700 mb-2">Live Preview</h4>
              <div className="bg-gray-100 rounded-lg p-4 flex flex-col items-center">
                <div className="bg-white border border-gray-300 w-full h-24 flex items-center justify-center mb-4">
                  <div className="text-sm text-gray-500">
                    <svg 
                      xmlns="http://www.w3.org/2000/svg" 
                      className="h-5 w-5 inline mr-2" 
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
                    Ad Preview {adSlot.adSize ? `(${adSlot.adSize.width} x ${adSlot.adSize.height})` : ""}
                  </div>
                </div>
                <div className="text-sm text-gray-500 mb-4">This is how your ad slot appears on your website</div>
                <Button variant="default">
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    className="h-4 w-4 mr-2" 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" 
                    />
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" 
                    />
                  </svg>
                  View on Website
                </Button>
              </div>
              
              <div className="mt-6">
                <h4 className="text-md font-medium text-gray-700 mb-2">Recent Performance</h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm font-medium text-gray-900">Impressions (24h)</div>
                    <div className="text-sm font-medium">24,856</div>
                  </div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm font-medium text-gray-900">Clicks (24h)</div>
                    <div className="text-sm font-medium">128</div>
                  </div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm font-medium text-gray-900">CTR</div>
                    <div className="text-sm font-medium">0.51%</div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-gray-900">Revenue (24h)</div>
                    <div className="text-sm font-medium text-green-600">$155.21</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <DialogFooter className="bg-gray-50 py-4 px-6 -mx-6 -mb-6 mt-6 border-t border-gray-200">
            <Button variant="outline" className="mr-3" onClick={onClose}>
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-4 w-4 mr-2" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M6 18L18 6M6 6l12 12" 
                />
              </svg>
              Close
            </Button>
            <Button variant="outline" className="mr-3">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-4 w-4 mr-2" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" 
                />
              </svg>
              Edit Ad Slot
            </Button>
            <Button variant="default">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-4 w-4 mr-2" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" 
                />
              </svg>
              View Detailed Analytics
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  } else {
    // Edit mode content
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-lg font-medium text-gray-900">
              Edit Ad Slot: {adSlot.name}
            </DialogTitle>
          </DialogHeader>
          
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Ad slot name" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="website"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Website</FormLabel>
                      <FormControl>
                        <Input placeholder="example.com" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="placement"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Placement</FormLabel>
                      <Select 
                        onValueChange={field.onChange} 
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select placement" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {AD_SLOT_PLACEMENTS.map((placement) => (
                            <SelectItem key={placement} value={placement}>
                              {placement}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="sizeId"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Ad Size</FormLabel>
                      <Select 
                        onValueChange={(value) => field.onChange(parseInt(value))} 
                        defaultValue={field.value?.toString()}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select ad size" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {adSizes?.map((size) => (
                            <SelectItem key={size.id} value={size.id.toString()}>
                              {size.name} ({size.width} x {size.height})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="floorPrice"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Floor Price (CPM $)</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          step="0.01" 
                          min="0" 
                          placeholder="0.00" 
                          {...field}
                          onChange={(e) => field.onChange(parseFloat(e.target.value))}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                
                <FormField
                  control={form.control}
                  name="status"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Status</FormLabel>
                      <Select 
                        onValueChange={field.onChange} 
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select status" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value={AD_SLOT_STATUSES.ACTIVE}>Active</SelectItem>
                          <SelectItem value={AD_SLOT_STATUSES.PAUSED}>Paused</SelectItem>
                          <SelectItem value={AD_SLOT_STATUSES.UNDER_REVIEW}>Under Review</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              
              <DialogFooter>
                <Button type="button" variant="outline" onClick={onClose} className="mr-2">
                  Cancel
                </Button>
                <Button type="submit" disabled={updateAdSlotMutation.isPending}>
                  {updateAdSlotMutation.isPending ? "Saving..." : "Save Changes"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    );
  }
};

export default AdSlotModal;
