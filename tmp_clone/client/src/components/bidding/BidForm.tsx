import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertBidSchema } from "@shared/schema";
import { AdSlotWithBids } from "@/components/adslots/AdSlotTable";
import { Advertiser } from "@shared/schema";
import { z } from "zod";
import { apiRequest } from "@/lib/queryClient";
import { formatCPM } from "@/lib/constants";
import { useToast } from "@/hooks/use-toast";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormDescription,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

// Extend the schema to make advertiserId required
const formSchema = insertBidSchema.extend({
  advertiserId: z.number({
    required_error: "Please select an advertiser",
  }),
  adSlotId: z.number({
    required_error: "Please select an ad slot",
  }),
  amount: z.number({
    required_error: "Please enter a bid amount",
  }).min(0.01, "Bid amount must be greater than 0"),
});

type FormValues = z.infer<typeof formSchema>;

const BidForm = () => {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: advertisers, isLoading: isLoadingAdvertisers } = useQuery<Advertiser[]>({
    queryKey: ['/api/advertisers'],
  });

  const { data: adSlots, isLoading: isLoadingAdSlots } = useQuery<AdSlotWithBids[]>({
    queryKey: ['/api/ad-slots'],
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      advertiserId: undefined,
      adSlotId: undefined,
      amount: undefined,
      status: "pending",
    },
  });

  const selectedAdSlotId = form.watch("adSlotId");
  const selectedAdSlot = adSlots?.find(slot => slot.id === selectedAdSlotId);

  const createBidMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      return apiRequest("POST", "/api/bids", values);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/ad-slots'] });
      toast({
        title: "Bid placed",
        description: "Your bid has been successfully placed.",
      });
      form.reset();
    },
    onError: (error) => {
      toast({
        title: "Error placing bid",
        description: error instanceof Error ? error.message : "An unknown error occurred",
        variant: "destructive",
      });
    }
  });

  const onSubmit = (values: FormValues) => {
    createBidMutation.mutate(values);
  };

  const isLoading = isLoadingAdvertisers || isLoadingAdSlots;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-72" />
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-10 w-full" />
          </div>
        </CardContent>
        <CardFooter>
          <Skeleton className="h-10 w-full" />
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Place a Bid</CardTitle>
        <CardDescription>
          Submit a bid for an ad slot. Higher bids have a better chance of winning the auction.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="advertiserId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Advertiser</FormLabel>
                  <Select 
                    onValueChange={(value) => field.onChange(parseInt(value))} 
                    defaultValue={field.value?.toString()}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select an advertiser" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {advertisers?.map((advertiser) => (
                        <SelectItem key={advertiser.id} value={advertiser.id.toString()}>
                          {advertiser.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    Select the advertiser account for this bid
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="adSlotId"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Ad Slot</FormLabel>
                  <Select 
                    onValueChange={(value) => field.onChange(parseInt(value))} 
                    defaultValue={field.value?.toString()}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select an ad slot" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {adSlots?.map((adSlot) => (
                        <SelectItem key={adSlot.id} value={adSlot.id.toString()}>
                          {adSlot.name} - {adSlot.website}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    Select the ad slot you want to bid on
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="amount"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Bid Amount (CPM $)</FormLabel>
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
                  {selectedAdSlot && (
                    <FormDescription className="flex justify-between">
                      <span>
                        Floor price: {formatCPM(selectedAdSlot.floorPrice)}
                      </span>
                      {selectedAdSlot.currentBid && (
                        <span className="font-medium text-green-600">
                          Current highest bid: {formatCPM(selectedAdSlot.currentBid)}
                        </span>
                      )}
                    </FormDescription>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button 
              type="submit" 
              className="w-full" 
              disabled={createBidMutation.isPending}
            >
              {createBidMutation.isPending ? "Placing Bid..." : "Place Bid"}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
};

export default BidForm;
