import pandas as pd

class CostModel:
    @staticmethod
    def calculate_costs(pricing_df, current_instance, candidate_instance, hours=None):
        """
        Calculates baseline and simulated costs based on pricing history.
        """
        # Filter for the relevant instances
        curr_pricing = pricing_df[pricing_df['instance_type'] == current_instance]
        cand_pricing = pricing_df[pricing_df['instance_type'] == candidate_instance]
        
        # Calculate historical hourly cost averages (or use total if we want exact sum)
        curr_avg = curr_pricing['hourly_price'].mean()
        cand_avg = cand_pricing['hourly_price'].mean()
        
        if hours is None:
            hours = 730 # default ~1 month
            
        baseline_monthly = curr_avg * hours
        simulated_monthly = cand_avg * hours
        
        savings = baseline_monthly - simulated_monthly
        if baseline_monthly > 0:
            pct_reduction = (savings / baseline_monthly) * 100
        else:
            pct_reduction = 0
            
        return {
            'baseline_monthly_cost': baseline_monthly,
            'simulated_monthly_cost': simulated_monthly,
            'absolute_monthly_saving': savings,
            'cost_reduction_pct': pct_reduction,
            'current_hourly_avg': curr_avg,
            'candidate_hourly_avg': cand_avg
        }
