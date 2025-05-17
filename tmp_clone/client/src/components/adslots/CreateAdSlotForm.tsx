import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { insertAdSlotSchema } from "@shared/schema";
import { z } from "zod";
import { AdSize } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import { AD_SLOT_PLACEMENTS, AD_SLOT_STATUSES } from "@/lib/constants";

import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface CreateAdSlotFormProps {
  isOpen: boolean;
  onClose: () => void;
}

const formSchema = insertAdSlotSchema.extend({
  publisherId: z.number().default(1), // Default to publisher ID 1 for demo
});

type FormValues = z.infer<typeof formSchema>;

const CreateAdSlotForm = ({ isOpen, onClose }: CreateAdSlotFormProps) => {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: adSizes, isLoading: isLoadingAdSizes } = useQuery<AdSize[]>({
    queryKey: ['/api/ad-sizes'],
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      publisherId: 1, // Default to publisher ID 1 for demo
      name: "",
      website: "",
      placement: "Header",
      floorPrice: 0,
      status: AD_SLOT_STATUSES.ACTIVE,
    },
  });

  const createAdSlotMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      return apiRequest("POST", "/api/ad-slots", values);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/ad-slots'] });
      toast({
        title: "Ad slot created",
        description: "The ad slot has been successfully created.",
      });
      form.reset();
      onClose();
    },
    onError: (error) => {
      toast({
        title: "Error creating ad slot",
        description: error instanceof Error ? error.message : "An unknown error occurred",
        variant: "destructive",
      });
    }
  });

  const onSubmit = (values: FormValues) => {
    createAdSlotMutation.mutate(values);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">Create New Ad Slot</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Homepage Banner" {...field} />
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

            <DialogFooter>
              <Button type="button" variant="outline" onClick={onClose} className="mr-2">
                Cancel
              </Button>
              <Button type="submit" disabled={createAdSlotMutation.isPending || isLoadingAdSizes}>
                {createAdSlotMutation.isPending ? "Creating..." : "Create Ad Slot"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateAdSlotForm;
