# For simplicity, just use autoregressive (AR) component
        forecast = []
        for i in range(periods):
            if i < len(historical_values):
                # For overlap periods, use actual values
                forecast.append(historical_values[i])
            else:
                # Use AR model for prediction
                prediction = 0
                for j in range(1, p + 1):
                    if i - j >= 0:
                        if i - j < len(historical_values):
                            prediction += values[i - j]  # Use original values if available
                        else:
                            diff_prediction = forecast[i - j]  # Use previous predictions
                            for _ in range(d):
                                # "Integrate" the differenced values back
                                if i - j - 1 >= 0:
                                    diff_prediction = diff_prediction + forecast[i - j - 1]
                            prediction += diff_prediction
                
                if p > 0:
                    prediction /= p  # Average of the last p values
                
                # For simplicity, we're not implementing the MA component
                
                # Apply differencing in reverse to get the actual forecast
                if d > 0 and i > 0:
                    prev_value = forecast[i - 1]
                    forecast.append(prev_value + prediction)
                else:
                    forecast.append(prediction)
        
        return forecast
    
    def _forecast_with_ai(self,
                         historical_data: List[Dict[str, Any]],
                         forecast_type: str,
                         forecast_units: str,
                         periods: int,
                         parameters: Dict[str, Any]) -> List[float]:
        """Forecast using AI engine."""
        # Extract historical values and dates
        historical_values = [period["value"] for period in historical_data]
        historical_dates = [period["label"] for period in historical_data]
        
        # Prepare prompt for AI
        prompt = f"""
Analyze the following historical {forecast_type} data and forecast for {periods} {forecast_units}(s) into the future.

Historical data:
"""
        
        for i, (date, value) in enumerate(zip(historical_dates, historical_values)):
            prompt += f"{date}: {value:.2f}\n"
        
        prompt += f"""
Based on this data, please forecast the next {periods} {forecast_units}(s).
Consider trends, seasonality, and any patterns in the data.
Return your forecast as a JSON array of numeric values only.
"""
        
        # Get forecast from AI
        response = self.ai_engine.get_agent_response(
            agent_type="finance",
            prompt=prompt,
            context={"task": "forecasting"}
        )
        
        # Parse AI response
        try:
            # Extract JSON array from possibly larger text
            json_match = re.search(r'(\[[\s\S]*\])', response)
            if json_match:
                forecast_values = json.loads(json_match.group(1))
            else:
                # Fallback: try to parse the entire text as JSON
                forecast_values = json.loads(response)
            
            # Ensure we have the right number of periods
            if len(forecast_values) < periods:
                # Pad with last value if not enough values returned
                last_value = forecast_values[-1] if forecast_values else 0
                forecast_values += [last_value] * (periods - len(forecast_values))
            elif len(forecast_values) > periods:
                # Truncate if too many values returned
                forecast_values = forecast_values[:periods]
                
        except (json.JSONDecodeError, ValueError):
            # Fallback to linear regression if AI response cannot be parsed
            logger.error("Failed to parse AI forecast response - falling back to linear regression")
            forecast_values = self._forecast_linear_regression(historical_values, periods)
        
        return forecast_values
    
    def create_budget(self,
                     name: str,
                     fiscal_year: str,
                     budget_type: str,
                     periods: List[Dict[str, Any]],
                     parameters: Optional[Dict[str, Any]] = None,
                     notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a budget.
        
        Args:
            name: Budget name
            fiscal_year: Fiscal year (YYYY)
            budget_type: Type of budget (operational, capital, project, etc.)
            periods: List of budget periods with amounts and accounts
            parameters: Optional budget parameters and settings
            notes: Optional notes about the budget
            
        Returns:
            Budget details
        """
        # Validate fiscal year
        try:
            year = int(fiscal_year)
            if year < 1900 or year > 2100:
                raise ValueError()
        except ValueError:
            raise ValueError(f"Invalid fiscal year: {fiscal_year}. Expected YYYY")
        
        # Validate periods
        if not periods:
            raise ValueError("No budget periods provided")
        
        # Set default parameters
        if not parameters:
            parameters = {}
        
        # Validate accounts in periods
        account_ids = set()
        for period in periods:
            if "accounts" in period:
                for account_entry in period["accounts"]:
                    account_id = account_entry.get("account_id")
                    if account_id:
                        account = self.neural_fabric.get_node(account_id)
                        if not account or account.node_type != "account":
                            raise ValueError(f"Invalid account ID in period: {account_id}")
                        account_ids.add(account_id)
        
        # Create budget properties
        budget_properties = {
            "name": name,
            "fiscal_year": fiscal_year,
            "budget_type": budget_type,
            "periods": periods,
            "parameters": parameters,
            "created_at": datetime.now().isoformat(),
            "status": "draft",
            "version": 1,
            "account_ids": list(account_ids)
        }
        
        if notes:
            budget_properties["notes"] = notes
        
        # Create budget node
        budget_id = self.neural_fabric.create_node(
            node_type="budget",
            properties=budget_properties
        )
        
        # Connect budget to accounts
        for account_id in account_ids:
            self.neural_fabric.connect_nodes(
                source_id=budget_id,
                target_id=account_id,
                relation_type="budgets"
            )
        
        # Publish event
        self.event_bus.publish(
            event_type="budget.created",
            payload={
                "budget_id": budget_id,
                "name": name,
                "fiscal_year": fiscal_year,
                "budget_type": budget_type
            }
        )
        
        logger.info(f"Created {budget_type} budget: {name} (ID: {budget_id})")
        
        # Return budget details
        return {
            "budget_id": budget_id,
            "name": name,
            "fiscal_year": fiscal_year,
            "budget_type": budget_type,
            "periods": len(periods),
            "status": "draft",
            "version": 1
        }
    
    def analyze_variance(self,
                        reference_id: str,
                        reference_type: str,
                        start_date: str,
                        end_date: str,
                        parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze variance between actual and budgeted/forecasted values.
        
        Args:
            reference_id: ID of the budget or forecast to compare against
            reference_type: Type of reference ('budget' or 'forecast')
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)
            parameters: Optional analysis parameters
            
        Returns:
            Variance analysis results
        """
        # Validate dates
        try:
            analysis_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            analysis_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")
        
        # Set default parameters
        if not parameters:
            parameters = {}
        
        # Validate reference
        reference_node = self.neural_fabric.get_node(reference_id)
        if not reference_node or reference_node.node_type != reference_type:
            raise ValueError(f"Invalid {reference_type} ID: {reference_id}")
        
        # Get reference data
        reference_data = None
        if reference_type == "budget":
            reference_data = reference_node.properties.get("periods", [])
        elif reference_type == "forecast":
            reference_data = reference_node.properties.get("forecast_data", [])
        else:
            raise ValueError(f"Unsupported reference type: {reference_type}")
        
        if not reference_data:
            raise ValueError(f"No data found in {reference_type}")
        
        # Get account IDs
        account_ids = reference_node.properties.get("account_ids", [])
        
        # Get actual data for the same period and accounts
        actual_data = self._get_actual_data(
            account_ids,
            analysis_start,
            analysis_end,
            parameters.get("time_unit", "month")
        )
        
        # Compare actual vs reference
        variance_results = self._calculate_variance(
            actual_data,
            reference_data,
            reference_type,
            parameters
        )
        
        # Create variance analysis properties
        analysis_properties = {
            "reference_id": reference_id,
            "reference_type": reference_type,
            "reference_name": reference_node.properties.get("name"),
            "start_date": start_date,
            "end_date": end_date,
            "parameters": parameters,
            "variance_data": variance_results,
            "created_at": datetime.now().isoformat()
        }
        
        # Create analysis node
        analysis_id = self.neural_fabric.create_node(
            node_type="variance_analysis",
            properties=analysis_properties
        )
        
        # Connect analysis to reference
        self.neural_fabric.connect_nodes(
            source_id=analysis_id,
            target_id=reference_id,
            relation_type="analyzes"
        )
        
        # Publish event
        self.event_bus.publish(
            event_type="variance.analyzed",
            payload={
                "analysis_id": analysis_id,
                "reference_id": reference_id,
                "reference_type": reference_type,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        logger.info(f"Analyzed variance against {reference_type} ID {reference_id}")
        
        # Return analysis results
        return {
            "analysis_id": analysis_id,
            "reference_id": reference_id,
            "reference_type": reference_type,
            "reference_name": reference_node.properties.get("name"),
            "start_date": start_date,
            "end_date": end_date,
            "results": variance_results
        }
    
    def _get_actual_data(self,
                        account_ids: List[str],
                        start_date: date,
                        end_date: date,
                        time_unit: str) -> List[Dict[str, Any]]:
        """Get actual financial data for accounts in a period."""
        # This is similar to _get_historical_data but formats the result differently
        transactions = self.neural_fabric.query_nodes(
            node_type="transaction",
            limit=10000
        )
        
        # Filter transactions by date
        date_filtered_transactions = []
        for tx in transactions:
            tx_date_str = tx.properties.get("date")
            if tx_date_str:
                try:
                    tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d").date()
                    if start_date <= tx_date <= end_date:
                        date_filtered_transactions.append(tx)
                except ValueError:
                    continue
        
        # Group transactions by time periods
        return self._group_transactions_by_period(
            date_filtered_transactions,
            account_ids,
            start_date,
            end_date,
            time_unit
        )
    
    def _calculate_variance(self,
                           actual_data: List[Dict[str, Any]],
                           reference_data: List[Dict[str, Any]],
                           reference_type: str,
                           parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate variance between actual and reference data."""
        # Get variance threshold for highlighting significant variances
        threshold = parameters.get("variance_threshold", 0.1)  # Default 10%
        
        # Match periods between actual and reference data
        matched_periods = []
        total_actual = 0
        total_reference = 0
        
        for actual_period in actual_data:
            actual_start = actual_period.get("start_date")
            actual_end = actual_period.get("end_date")
            actual_value = actual_period.get("value", 0)
            
            # Find matching reference period
            matching_ref = None
            for ref_period in reference_data:
                ref_start = ref_period.get("start_date")
                ref_end = ref_period.get("end_date")
                
                # Check for date overlap
                if (actual_start and ref_start and actual_end and ref_end and
                    not (actual_end < ref_start or actual_start > ref_end)):
                    matching_ref = ref_period
                    break
            
            if matching_ref:
                ref_value = matching_ref.get("value", 0)
                
                # Calculate variance
                variance = actual_value - ref_value
                if ref_value != 0:
                    variance_pct = (variance / abs(ref_value)) * 100
                else:
                    variance_pct = 0 if variance == 0 else 100
                
                # Determine if variance is significant
                is_significant = abs(variance_pct) >= threshold * 100
                
                matched_periods.append({
                    "period": actual_period.get("label"),
                    "start_date": actual_start,
                    "end_date": actual_end,
                    "actual": actual_value,
                    "reference": ref_value,
                    "variance": variance,
                    "variance_percentage": variance_pct,
                    "is_significant": is_significant,
                    "is_favorable": variance > 0 if reference_type == "forecast" else variance < 0
                })
                
                total_actual += actual_value
                total_reference += ref_value
        
        # Calculate overall variance
        overall_variance = total_actual - total_reference
        if total_reference != 0:
            overall_variance_pct = (overall_variance / abs(total_reference)) * 100
        else:
            overall_variance_pct = 0 if overall_variance == 0 else 100
        
        # Analyze patterns in the variance
        increasing_trend = all(
            matched_periods[i]["variance"] > matched_periods[i-1]["variance"] 
            for i in range(1, len(matched_periods))
        ) if len(matched_periods) > 1 else False
        
        decreasing_trend = all(
            matched_periods[i]["variance"] < matched_periods[i-1]["variance"] 
            for i in range(1, len(matched_periods))
        ) if len(matched_periods) > 1 else False
        
        # Generate insights
        insights = []
        if abs(overall_variance_pct) >= threshold * 100:
            if overall_variance > 0:
                insights.append(f"Overall performance is {overall_variance_pct:.1f}% above {reference_type}")
            else:
                insights.append(f"Overall performance is {abs(overall_variance_pct):.1f}% below {reference_type}")
        
        if increasing_trend:
            insights.append("Variance is showing an increasing trend")
        elif decreasing_trend:
            insights.append("Variance is showing a decreasing trend")
        
        # Count significant variances
        significant_count = sum(1 for p in matched_periods if p["is_significant"])
        if significant_count > 0:
            insights.append(f"Found {significant_count} periods with significant variance")
        
        return {
            "periods": matched_periods,
            "overall": {
                "actual": total_actual,
                "reference": total_reference,
                "variance": overall_variance,
                "variance_percentage": overall_variance_pct
            },
            "insights": insights
        }
    
    def run_scenario(self,
                    name: str,
                    base_id: str,
                    base_type: str,
                    adjustments: List[Dict[str, Any]],
                    parameters: Optional[Dict[str, Any]] = None,
                    notes: Optional[str] = None) -> Dict[str, Any]:
        """Run a what-if scenario analysis.
        
        Args:
            name: Scenario name
            base_id: ID of the base forecast or budget
            base_type: Type of base ('forecast' or 'budget')
            adjustments: List of adjustments to apply
            parameters: Optional scenario parameters
            notes: Optional notes about the scenario
            
        Returns:
            Scenario analysis results
        """
        # Validate base
        base_node = self.neural_fabric.get_node(base_id)
        if not base_node or base_node.node_type != base_type:
            raise ValueError(f"Invalid {base_type} ID: {base_id}")
        
        # Set default parameters
        if not parameters:
            parameters = {}
        
        # Get base data
        base_data = None
        if base_type == "forecast":
            base_data = base_node.properties.get("forecast_data", [])
        elif base_type == "budget":
            base_data = base_node.properties.get("periods", [])
        else:
            raise ValueError(f"Unsupported base type: {base_type}")
        
        if not base_data:
            raise ValueError(f"No data found in base {base_type}")
        
        # Apply adjustments to create scenario data
        scenario_data = self._apply_scenario_adjustments(
            base_data,
            adjustments,
            parameters
        )
        
        # Create scenario properties
        scenario_properties = {
            "name": name,
            "base_id": base_id,
            "base_type": base_type,
            "base_name": base_node.properties.get("name"),
            "adjustments": adjustments,
            "parameters": parameters,
            "scenario_data": scenario_data,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        if notes:
            scenario_properties["notes"] = notes
        
        # Create scenario node
        scenario_id = self.neural_fabric.create_node(
            node_type="scenario",
            properties=scenario_properties
        )
        
        # Connect scenario to base
        self.neural_fabric.connect_nodes(
            source_id=scenario_id,
            target_id=base_id,
            relation_type="based_on"
        )
        
        # Publish event
        self.event_bus.publish(
            event_type="scenario.created",
            payload={
                "scenario_id": scenario_id,
                "name": name,
                "base_id": base_id,
                "base_type": base_type
            }
        )
        
        logger.info(f"Created scenario: {name} (ID: {scenario_id})")
        
        # Return scenario details
        return {
            "scenario_id": scenario_id,
            "name": name,
            "base_id": base_id,
            "base_type": base_type,
            "base_name": base_node.properties.get("name"),
            "adjustments_applied": len(adjustments),
            "status": "active"
        }
    
    def _apply_scenario_adjustments(self,
                                  base_data: List[Dict[str, Any]],
                                  adjustments: List[Dict[str, Any]],
                                  parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply adjustments to base data for scenario analysis."""
        # Deep copy base data to avoid modifying original
        scenario_data = []
        for period in base_data:
            scenario_data.append(period.copy())
        
        # Apply each adjustment
        for adjustment in adjustments:
            adjustment_type = adjustment.get("type")
            target = adjustment.get("target")
            value = adjustment.get("value")
            
            if not adjustment_type or not target or value is None:
                continue
            
            # Determine which periods to adjust
            target_periods = []
            if target == "all":
                target_periods = list(range(len(scenario_data)))
            elif target.startswith("period:"):
                try:
                    period_idx = int(target.split(":")[1])
                    if 0 <= period_idx < len(scenario_data):
                        target_periods = [period_idx]
                except ValueError:
                    pass
            elif target.startswith("range:"):
                try:
                    start, end = target.split(":")[1].split("-")
                    start_idx = int(start)
                    end_idx = int(end)
                    target_periods = list(range(start_idx, min(end_idx + 1, len(scenario_data))))
                except (ValueError, IndexError):
                    pass
            elif target.startswith("date:"):
                date_str = target.split(":")[1]
                try:
                    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    for i, period in enumerate(scenario_data):
                        try:
                            period_start = datetime.strptime(period.get("start_date", ""), "%Y-%m-%d").date()
                            period_end = datetime.strptime(period.get("end_date", ""), "%Y-%m-%d").date()
                            if period_start <= target_date <= period_end:
                                target_periods.append(i)
                                break
                        except ValueError:
                            continue
                except ValueError:
                    pass
            
            # Apply adjustment to targeted periods
            for period_idx in target_periods:
                if 0 <= period_idx < len(scenario_data):
                    current_value = scenario_data[period_idx].get("value", 0)
                    
                    if adjustment_type == "absolute":
                        # Set to specific value
                        scenario_data[period_idx]["value"] = value
                    elif adjustment_type == "relative":
                        # Add or subtract amount
                        scenario_data[period_idx]["value"] = current_value + value
                    elif adjustment_type == "percentage":
                        # Apply percentage change
                        scenario_data[period_idx]["value"] = current_value * (1 + value / 100)
                    elif adjustment_type == "multiply":
                        # Multiply by factor
                        scenario_data[period_idx]["value"] = current_value * value
                    elif adjustment_type == "growth":
                        # Apply compound growth over periods
                        previous_periods = max(period_idx, 0)
                        if previous_periods > 0:
                            base_value = scenario_data[0].get("value", 0)
                            scenario_data[period_idx]["value"] = base_value * ((1 + value / 100) ** (period_idx + 1))
                    
                    # Mark as scenario data
                    scenario_data[period_idx]["is_scenario"] = True
                    scenario_data[period_idx]["adjustment_applied"] = {
                        "type": adjustment_type,
                        "value": value
                    }
        
        return scenario_data
    
    def predict_metric(self,
                      metric_name: str,
                      parameters: Dict[str, Any],
                      historical_data: Optional[List[Dict[str, Any]]] = None,
                      notes: Optional[str] = None) -> Dict[str, Any]:
        """Predict a business metric based on various factors.
        
        Args:
            metric_name: Name of the metric to predict
            parameters: Parameters for prediction
            historical_data: Optional historical data for the metric
            notes: Optional notes about the prediction
            
        Returns:
            Metric prediction results
        """
        if not self.ai_engine:
            raise ValueError("AI engine is required for metric prediction")
        
        # Validate parameters
        required_params = ["start_date", "end_date", "prediction_units"]
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Get or create historical data if not provided
        if not historical_data:
            historical_data = self._gather_metric_historical_data(
                metric_name,
                parameters
            )
        
        # Predict metric
        prediction_result = self._predict_metric_values(
            metric_name,
            historical_data,
            parameters
        )
        
        # Create prediction properties
        prediction_properties = {
            "metric_name": metric_name,
            "parameters": parameters,
            "historical_data": historical_data,
            "prediction_data": prediction_result,
            "created_at": datetime.now().isoformat()
        }
        
        if notes:
            prediction_properties["notes"] = notes
        
        # Create prediction node
        prediction_id = self.neural_fabric.create_node(
            node_type="metric_prediction",
            properties=prediction_properties
        )
        
        # Publish event
        self.event_bus.publish(
            event_type="metric.predicted",
            payload={
                "prediction_id": prediction_id,
                "metric_name": metric_name,
                "start_date": parameters.get("start_date"),
                "end_date": parameters.get("end_date")
            }
        )
        
        logger.info(f"Predicted metric: {metric_name} (ID: {prediction_id})")
        
        # Return prediction details
        return {
            "prediction_id": prediction_id,
            "metric_name": metric_name,
            "start_date": parameters.get("start_date"),
            "end_date": parameters.get("end_date"),
            "prediction_data": prediction_result
        }
    
    def _gather_metric_historical_data(self, metric_name: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gather historical data for a metric."""
        # Implementation depends on the metric type
        if metric_name == "revenue":
            # Get revenue accounts
            revenue_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"type": "revenue"}
            )
            account_ids = [acct.id for acct in revenue_accounts]
            
            # Calculate start date for historical data
            end_date = datetime.strptime(parameters.get("start_date"), "%Y-%m-%d").date()
            historical_periods = parameters.get("historical_periods", 12)
            time_unit = parameters.get("prediction_units")
            
            # Get historical data
            return self._get_historical_data(
                account_ids,
                "revenue",
                end_date,
                historical_periods,
                time_unit
            )
            
        elif metric_name == "expenses":
            # Similar to revenue but with expense accounts
            expense_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"type": "expense"}
            )
            account_ids = [acct.id for acct in expense_accounts]
            
            end_date = datetime.strptime(parameters.get("start_date"), "%Y-%m-%d").date()
            historical_periods = parameters.get("historical_periods", 12)
            time_unit = parameters.get("prediction_units")
            
            return self._get_historical_data(
                account_ids,
                "expense",
                end_date,
                historical_periods,
                time_unit
            )
            
        elif metric_name == "customer_acquisition":
            # Would need to implement customer data gathering
            # Mock implementation for now
            return self._mock_historical_data(metric_name, parameters)
            
        elif metric_name == "customer_retention":
            # Mock implementation for now
            return self._mock_historical_data(metric_name, parameters)
            
        else:
            # Generic implementation for unknown metrics
            return self._mock_historical_data(metric_name, parameters)
    
    def _mock_historical_data(self, metric_name: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create mock historical data for demonstration purposes."""
        historical_periods = parameters.get("historical_periods", 12)
        time_unit = parameters.get("prediction_units", "month")
        end_date = datetime.strptime(parameters.get("start_date", "2023-01-01"), "%Y-%m-%d").date()
        
        # Calculate start date based on time unit and periods
        if time_unit == "day":
            start_date = end_date - timedelta(days=historical_periods)
        elif time_unit == "week":
            start_date = end_date - timedelta(weeks=historical_periods)
        elif time_unit == "month":
            # Approximate months as 30.44 days
            start_date = end_date - timedelta(days=int(30.44 * historical_periods))
        elif time_unit == "quarter":
            # Approximate quarters as 91.31 days
            start_date = end_date - timedelta(days=int(91.31 * historical_periods))
        elif time_unit == "year":
            start_date = end_date - timedelta(days=365 * historical_periods)
        else:
            raise ValueError(f"Invalid time unit: {time_unit}")
        
        # Generate random but plausible historical data
        historical_data = []
        current_date = start_date
        base_value = random.uniform(1000, 10000)
        trend = random.uniform(0.01, 0.05)  # Positive trend
        seasonal_factor = random.uniform(0.1, 0.3)  # Seasonal variation
        
        for i in range(historical_periods):
            if time_unit == "day":
                period_end = current_date
                next_date = current_date + timedelta(days=1)
            elif time_unit == "week":
                period_end = current_date + timedelta(days=6)
                next_date = current_date + timedelta(weeks=1)
            elif time_unit == "month":
                # Calculate last day of month
                if current_date.month == 12:
                    period_end = date(current_date.year, 12, 31)
                    next_date = date(current_date.year + 1, 1, 1)
                else:
                    next_month = current_date.month + 1
                    next_date = date(current_date.year, next_month, 1)
                    period_end = next_date - timedelta(days=1)
            elif time_unit == "quarter":
                # Calculate last day of quarter
                quarter = (current_date.month - 1) // 3 + 1
                if quarter == 4:
                    period_end = date(current_date.year, 12, 31)
                    next_date = date(current_date.year + 1, 1, 1)
                else:
                    next_quarter_month = quarter * 3 + 1
                    next_date = date(current_date.year, next_quarter_month, 1)
                    period_end = next_date - timedelta(days=1"""
Forecasting Agent for NeuroERP.

This agent manages financial forecasting, predictive modeling, budget planning,
scenario analysis, and AI-driven financial insights.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import json
from datetime import datetime, date, timedelta
import re
import math
import random

from ...core.config import Config
from ...core.event_bus import EventBus
from ...core.neural_fabric import NeuralFabric
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ForecastingAgent(BaseAgent):
    """AI Agent for financial forecasting and predictive analytics."""
    
    def __init__(self, name: str = "Forecasting Agent", ai_engine=None, vector_store=None):
        """Initialize the forecasting agent.
        
        Args:
            name: Name of the agent
            ai_engine: AI engine for advanced processing
            vector_store: Vector store for semantic search
        """
        super().__init__(name=name, agent_type="finance.forecasting", ai_engine=ai_engine, vector_store=vector_store)
        
        self.config = Config()
        self.event_bus = EventBus()
        self.neural_fabric = NeuralFabric()
        
        # Register agent skills
        self._register_skills()
        
        # Subscribe to relevant events
        self._subscribe_to_events()
        
        logger.info(f"Initialized {name}")
    
    def _register_skills(self):
        """Register agent-specific skills."""
        self.register_skill("create_forecast", self.create_forecast)
        self.register_skill("create_budget", self.create_budget)
        self.register_skill("analyze_variance", self.analyze_variance)
        self.register_skill("run_scenario", self.run_scenario)
        self.register_skill("predict_metric", self.predict_metric)
        self.register_skill("analyze_trends", self.analyze_trends)
        self.register_skill("optimize_cashflow", self.optimize_cashflow)
        self.register_skill("evaluate_investment", self.evaluate_investment)
        self.register_skill("generate_insights", self.generate_insights)
    
    def _subscribe_to_events(self):
        """Subscribe to relevant system events."""
        self.event_bus.subscribe("transaction.recorded", self._handle_transaction)
        self.event_bus.subscribe("invoice.created", self._handle_invoice)
        self.event_bus.subscribe("period.closed", self._handle_period_close)
        self.event_bus.subscribe("forecast.created", self._handle_forecast)
        self.event_bus.subscribe("budget.created", self._handle_budget)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results.
        
        Args:
            input_data: Input data with action and parameters
            
        Returns:
            Processing results
        """
        action = input_data.get("action", "")
        parameters = input_data.get("parameters", {})
        
        # Log the requested action
        logger.info(f"Processing {action} with parameters: {parameters}")
        
        # Dispatch to appropriate skill
        try:
            if action == "create_forecast":
                return {"success": True, "result": self.create_forecast(**parameters)}
            elif action == "create_budget":
                return {"success": True, "result": self.create_budget(**parameters)}
            elif action == "analyze_variance":
                return {"success": True, "result": self.analyze_variance(**parameters)}
            elif action == "run_scenario":
                return {"success": True, "result": self.run_scenario(**parameters)}
            elif action == "predict_metric":
                return {"success": True, "result": self.predict_metric(**parameters)}
            elif action == "analyze_trends":
                return {"success": True, "result": self.analyze_trends(**parameters)}
            elif action == "optimize_cashflow":
                return {"success": True, "result": self.optimize_cashflow(**parameters)}
            elif action == "evaluate_investment":
                return {"success": True, "result": self.evaluate_investment(**parameters)}
            elif action == "generate_insights":
                return {"success": True, "result": self.generate_insights(**parameters)}
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [skill["name"] for skill in self.skills]
                }
        except Exception as e:
            logger.error(f"Error processing {action}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def create_forecast(self,
                       name: str,
                       start_date: str,
                       end_date: str,
                       forecast_type: str,
                       forecast_units: str,
                       account_ids: Optional[List[str]] = None,
                       parameters: Optional[Dict[str, Any]] = None,
                       notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a financial forecast.
        
        Args:
            name: Forecast name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            forecast_type: Type of forecast (revenue, expense, income, cashflow)
            forecast_units: Unit of time (day, week, month, quarter, year)
            account_ids: Optional list of account IDs to include
            parameters: Optional forecast parameters and settings
            notes: Optional notes about the forecast
            
        Returns:
            Forecast details
        """
        # Validate dates
        try:
            forecast_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            forecast_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")
        
        if forecast_start >= forecast_end:
            raise ValueError("End date must be after start date")
        
        # Set default parameters
        if not parameters:
            parameters = {}
        
        # Default forecast method
        forecast_method = parameters.get("method", "time_series")
        
        # Validate accounts if provided
        if account_ids:
            for account_id in account_ids:
                account = self.neural_fabric.get_node(account_id)
                if not account or account.node_type != "account":
                    raise ValueError(f"Invalid account ID: {account_id}")
        else:
            # If no accounts specified, get appropriate accounts based on forecast type
            account_ids = self._get_accounts_for_forecast_type(forecast_type)
        
        # Get historical data for accounts
        historical_data = self._get_historical_data(
            account_ids,
            forecast_type,
            forecast_start,
            parameters.get("historical_periods", 12),
            forecast_units
        )
        
        # Generate forecast based on method
        forecast_data = self._generate_forecast(
            historical_data,
            forecast_type,
            forecast_units,
            forecast_start,
            forecast_end,
            forecast_method,
            parameters
        )
        
        # Create forecast properties
        forecast_properties = {
            "name": name,
            "forecast_type": forecast_type,
            "start_date": start_date,
            "end_date": end_date,
            "forecast_units": forecast_units,
            "method": forecast_method,
            "account_ids": account_ids,
            "parameters": parameters,
            "forecast_data": forecast_data,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        if notes:
            forecast_properties["notes"] = notes
        
        # Create forecast node
        forecast_id = self.neural_fabric.create_node(
            node_type="forecast",
            properties=forecast_properties
        )
        
        # Connect forecast to accounts
        for account_id in account_ids:
            self.neural_fabric.connect_nodes(
                source_id=forecast_id,
                target_id=account_id,
                relation_type="forecasts"
            )
        
        # Publish event
        self.event_bus.publish(
            event_type="forecast.created",
            payload={
                "forecast_id": forecast_id,
                "name": name,
                "forecast_type": forecast_type,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        
        logger.info(f"Created {forecast_type} forecast: {name} (ID: {forecast_id})")
        
        # Return forecast details
        return {
            "forecast_id": forecast_id,
            "name": name,
            "forecast_type": forecast_type,
            "start_date": start_date,
            "end_date": end_date,
            "forecast_units": forecast_units,
            "periods": len(forecast_data),
            "method": forecast_method
        }
    
    def _get_accounts_for_forecast_type(self, forecast_type: str) -> List[str]:
        """Get appropriate account IDs based on forecast type."""
        account_ids = []
        
        if forecast_type == "revenue":
            # Get revenue accounts
            revenue_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"type": "revenue"}
            )
            account_ids = [acct.id for acct in revenue_accounts]
            
        elif forecast_type == "expense":
            # Get expense accounts
            expense_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"type": "expense"}
            )
            account_ids = [acct.id for acct in expense_accounts]
            
        elif forecast_type == "income":
            # Get both revenue and expense accounts
            income_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"type": ["revenue", "expense"]}
            )
            account_ids = [acct.id for acct in income_accounts]
            
        elif forecast_type == "cashflow":
            # Get cash accounts
            cash_accounts = self.neural_fabric.query_nodes(
                node_type="account",
                filters={"is_bank_account": True}
            )
            
            if not cash_accounts:
                # Fallback to accounts named "Cash"
                cash_accounts = self.neural_fabric.query_nodes(
                    node_type="account",
                    filters={"name": "Cash"}
                )
                
            account_ids = [acct.id for acct in cash_accounts]
        
        if not account_ids:
            raise ValueError(f"No accounts found for forecast type: {forecast_type}")
            
        return account_ids
    
    def _get_historical_data(self, 
                            account_ids: List[str], 
                            data_type: str,
                            end_date: date,
                            periods: int,
                            time_unit: str) -> List[Dict[str, Any]]:
        """Get historical data for accounts."""
        # Calculate start date based on time unit and periods
        if time_unit == "day":
            start_date = end_date - timedelta(days=periods)
        elif time_unit == "week":
            start_date = end_date - timedelta(weeks=periods)
        elif time_unit == "month":
            # Approximate months as 30.44 days
            start_date = end_date - timedelta(days=int(30.44 * periods))
        elif time_unit == "quarter":
            # Approximate quarters as 91.31 days
            start_date = end_date - timedelta(days=int(91.31 * periods))
        elif time_unit == "year":
            start_date = end_date - timedelta(days=365 * periods)
        else:
            raise ValueError(f"Invalid time unit: {time_unit}")
        
        # Get transactions in the date range
        transactions = self.neural_fabric.query_nodes(
            node_type="transaction",
            limit=10000  # High limit to get enough historical data
        )
        
        # Filter transactions by date
        date_filtered_transactions = []
        for tx in transactions:
            tx_date_str = tx.properties.get("date")
            if tx_date_str:
                try:
                    tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d").date()
                    if start_date <= tx_date <= end_date:
                        date_filtered_transactions.append(tx)
                except ValueError:
                    continue
        
        # Group transactions by time periods
        period_data = self._group_transactions_by_period(
            date_filtered_transactions,
            account_ids,
            start_date,
            end_date,
            time_unit
        )
        
        return period_data
    
    def _group_transactions_by_period(self,
                                     transactions: List[Any],
                                     account_ids: List[str],
                                     start_date: date,
                                     end_date: date,
                                     time_unit: str) -> List[Dict[str, Any]]:
        """Group transactions by time periods."""
        # Generate period boundaries
        periods = []
        current_date = start_date
        
        while current_date <= end_date:
            if time_unit == "day":
                period_end = current_date
                next_date = current_date + timedelta(days=1)
            elif time_unit == "week":
                period_end = current_date + timedelta(days=6)
                next_date = current_date + timedelta(weeks=1)
            elif time_unit == "month":
                # Calculate last day of month
                if current_date.month == 12:
                    period_end = date(current_date.year, 12, 31)
                    next_date = date(current_date.year + 1, 1, 1)
                else:
                    next_month = current_date.month + 1
                    next_date = date(current_date.year, next_month, 1)
                    period_end = next_date - timedelta(days=1)
            elif time_unit == "quarter":
                # Calculate last day of quarter
                quarter = (current_date.month - 1) // 3 + 1
                if quarter == 4:
                    period_end = date(current_date.year, 12, 31)
                    next_date = date(current_date.year + 1, 1, 1)
                else:
                    next_quarter_month = quarter * 3 + 1
                    next_date = date(current_date.year, next_quarter_month, 1)
                    period_end = next_date - timedelta(days=1)
            elif time_unit == "year":
                period_end = date(current_date.year, 12, 31)
                next_date = date(current_date.year + 1, 1, 1)
            
            # Ensure period end is not beyond the overall end date
            if period_end > end_date:
                period_end = end_date
            
            periods.append({
                "start": current_date,
                "end": period_end,
                "transactions": [],
                "total": 0.0
            })
            
            current_date = next_date
            if current_date > end_date:
                break
        
        # Group transactions into periods
        for tx in transactions:
            tx_date_str = tx.properties.get("date")
            try:
                tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d").date()
                
                # Find which period this transaction belongs to
                for period in periods:
                    if period["start"] <= tx_date <= period["end"]:
                        # Get transaction entries that affect the target accounts
                        entries = self.neural_fabric.get_connected_nodes(
                            node_id=tx.id,
                            relation_type="part_of_inverse"
                        )
                        
                        if "part_of_inverse" in entries:
                            for entry in entries["part_of_inverse"]:
                                entry_account_id = entry.properties.get("account_id")
                                if entry_account_id in account_ids:
                                    # Add to period total
                                    amount = entry.properties.get("amount", 0)
                                    entry_type = entry.properties.get("type")
                                    
                                    # Determine if amount should be positive or negative
                                    # based on account type and entry type
                                    account = self.neural_fabric.get_node(entry_account_id)
                                    if account:
                                        account_type = account.properties.get("type")
                                        
                                        # Determine if this entry increases or decreases the account
                                        # For revenue and liability, credit increases
                                        # For asset and expense, debit increases
                                        is_increase_entry = (
                                            (entry_type == "debit" and account_type in ["asset", "expense"]) or
                                            (entry_type == "credit" and account_type in ["revenue", "liability", "equity"])
                                        )
                                        
                                        if is_increase_entry:
                                            period["total"] += amount
                                        else:
                                            period["total"] -= amount
                                    
                                    # Store transaction reference
                                    period["transactions"].append({
                                        "id": tx.id,
                                        "date": tx_date_str,
                                        "amount": amount,
                                        "account_id": entry_account_id,
                                        "entry_type": entry_type,
                                        "description": tx.properties.get("description")
                                    })
                        
                        break
            except ValueError:
                continue
        
        # Convert to format suitable for forecasting
        result = []
        for i, period in enumerate(periods):
            label = self._format_period_label(period["start"], period["end"], time_unit)
            result.append({
                "period": i,
                "label": label,
                "start_date": period["start"].isoformat(),
                "end_date": period["end"].isoformat(),
                "value": period["total"],
                "transaction_count": len(period["transactions"])
            })
        
        return result
    
    def _format_period_label(self, start: date, end: date, time_unit: str) -> str:
        """Format a period label based on time unit."""
        if time_unit == "day":
            return start.strftime("%Y-%m-%d")
        elif time_unit == "week":
            return f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
        elif time_unit == "month":
            return start.strftime("%b %Y")
        elif time_unit == "quarter":
            quarter = (start.month - 1) // 3 + 1
            return f"Q{quarter} {start.year}"
        elif time_unit == "year":
            return str(start.year)
        else:
            return f"{start.isoformat()} to {end.isoformat()}"
    
    def _generate_forecast(self,
                          historical_data: List[Dict[str, Any]],
                          forecast_type: str,
                          forecast_units: str,
                          start_date: date,
                          end_date: date,
                          method: str,
                          parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate forecast based on historical data and method."""
        # Check if we have enough historical data
        if len(historical_data) < 2:
            raise ValueError("Not enough historical data for forecasting")
        
        # Extract historical values
        historical_values = [period["value"] for period in historical_data]
        
        # Calculate number of periods to forecast
        if forecast_units == "day":
            forecast_periods = (end_date - start_date).days + 1
        elif forecast_units == "week":
            forecast_periods = ((end_date - start_date).days // 7) + 1
        elif forecast_units == "month":
            forecast_periods = ((end_date.year - start_date.year) * 12 + end_date.month - start_date.month) + 1
        elif forecast_units == "quarter":
            forecast_periods = ((end_date.year - start_date.year) * 4 + (end_date.month - 1) // 3 - (start_date.month - 1) // 3) + 1
        elif forecast_units == "year":
            forecast_periods = (end_date.year - start_date.year) + 1
        else:
            raise ValueError(f"Invalid forecast units: {forecast_units}")
        
        # Choose forecasting method
        if method == "moving_average":
            window = parameters.get("window_size", 3)
            forecast = self._forecast_moving_average(historical_values, forecast_periods, window)
        elif method == "exponential_smoothing":
            alpha = parameters.get("alpha", 0.3)
            forecast = self._forecast_exponential_smoothing(historical_values, forecast_periods, alpha)
        elif method == "linear_regression":
            forecast = self._forecast_linear_regression(historical_values, forecast_periods)
        elif method == "seasonal":
            # Season length depends on time unit
            if forecast_units == "month":
                season_length = 12  # Monthly data: 12 months in a year
            elif forecast_units == "quarter":
                season_length = 4   # Quarterly data: 4 quarters in a year
            else:
                season_length = parameters.get("season_length", 4)
                
            forecast = self._forecast_seasonal(historical_values, forecast_periods, season_length)
        elif method == "arima":
            # For simplicity, we'll implement a basic version
            # In a real system, this would use a proper ARIMA implementation
            p = parameters.get("p", 1)  # AR term
            d = parameters.get("d", 0)  # Differencing
            q = parameters.get("q", 0)  # MA term
            forecast = self._forecast_arima(historical_values, forecast_periods, p, d, q)
        elif method == "ai":
            # This would use the AI engine for custom forecasting
            if self.ai_engine:
                forecast = self._forecast_with_ai(historical_data, forecast_type, forecast_units, forecast_periods, parameters)
            else:
                # Fallback to linear regression if AI not available
                forecast = self._forecast_linear_regression(historical_values, forecast_periods)
        else:
            # Default to simple trend extrapolation
            forecast = self._forecast_linear_regression(historical_values, forecast_periods)
        
        # Generate forecast periods
        forecast_data = []
        current_date = start_date
        
        for i in range(forecast_periods):
            if forecast_units == "day":
                period_end = current_date
                next_date = current_date + timedelta(days=1)
            elif forecast_units == "week":
                period_end = current_date + timedelta(days=6)
                next_date = current_date + timedelta(weeks=1)
            elif forecast_units == "month":
                # Last day of month
                if current_date.month == 12:
                    period_end = date(current_date.year, 12, 31)
                    next_date = date(current_date.year + 1, 1, 1)
                else:
                    next_month = current_date.month + 1
                    next_date = date(current_date.year, next_month, 1)
                    period_end = next_date - timedelta(days=1)
            elif forecast_units == "quarter":
                quarter = (current_date.month - 1) // 3 + 1
                if quarter == 4:
                    period_end = date(current_date.year, 12, 31)
                    next_date = date(current_date.year + 1, 1, 1)
                else:
                    next_quarter_month = quarter * 3 + 1
                    next_date = date(current_date.year, next_quarter_month, 1)
                    period_end = next_date - timedelta(days=1)
            elif forecast_units == "year":
                period_end = date(current_date.year, 12, 31)
                next_date = date(current_date.year + 1, 1, 1)
            
            # Ensure period end is not beyond the overall end date
            if period_end > end_date:
                period_end = end_date
            
            # Format period label
            label = self._format_period_label(current_date, period_end, forecast_units)
            
            forecast_data.append({
                "period": i,
                "label": label,
                "start_date": current_date.isoformat(),
                "end_date": period_end.isoformat(),
                "value": forecast[i],
                "is_forecast": True
            })
            
            current_date = next_date
            if current_date > end_date:
                break
        
        return forecast_data
    
    def _forecast_moving_average(self, historical_values: List[float], periods: int, window: int) -> List[float]:
        """Forecast using moving average method."""
        if len(historical_values) < window:
            window = len(historical_values)
            
        forecast = []
        for i in range(periods):
            if i < len(historical_values):
                # For overlap periods, use actual values
                forecast.append(historical_values[i])
            else:
                # Get last 'window' values
                last_values = []
                for j in range(window):
                    idx = i - j - 1
                    if idx >= 0:
                        if idx < len(historical_values):
                            last_values.append(historical_values[idx])
                        else:
                            last_values.append(forecast[idx])
                
                # Calculate average
                if last_values:
                    avg = sum(last_values) / len(last_values)
                    forecast.append(avg)
                else:
                    # Fallback
                    forecast.append(historical_values[-1] if historical_values else 0)
        
        return forecast
    
    def _forecast_exponential_smoothing(self, historical_values: List[float], periods: int, alpha: float) -> List[float]:
        """Forecast using exponential smoothing method."""
        if not historical_values:
            return [0] * periods
            
        forecast = []
        for i in range(periods):
            if i < len(historical_values):
                # For overlap periods, use actual values
                forecast.append(historical_values[i])
            else:
                # Initialize with last known value
                if i == 0:
                    last_value = historical_values[-1]
                else:
                    last_value = forecast[i-1]
                
                # Simple exponential smoothing formula
                if i - 1 < len(historical_values):
                    prev_actual = historical_values[i-1]
                else:
                    prev_actual = forecast[i-1]
                
                smoothed = alpha * prev_actual + (1 - alpha) * last_value
                forecast.append(smoothed)
        
        return forecast
    
    def _forecast_linear_regression(self, historical_values: List[float], periods: int) -> List[float]:
        """Forecast using linear regression method."""
        if not historical_values:
            return [0] * periods
            
        # Create x values (time periods)
        x = list(range(len(historical_values)))
        y = historical_values
        
        # Calculate slope and intercept
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, y))
        sum_xx = sum(x_i * x_i for x_i in x)
        
        if n * sum_xx - sum_x * sum_x == 0:
            # Avoid division by zero
            slope = 0
            intercept = sum_y / n if n > 0 else 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
        
        # Generate forecast
        forecast = []
        for i in range(periods):
            if i < len(historical_values):
                # For overlap periods, use actual values
                forecast.append(historical_values[i])
            else:
                # Calculate forecast using linear model
                period = len(historical_values) + (i - len(historical_values))
                value = intercept + slope * period
                forecast.append(value)
        
        return forecast
    
    def _forecast_seasonal(self, historical_values: List[float], periods: int, season_length: int) -> List[float]:
        """Forecast using seasonal method with multiplicative decomposition."""
        if len(historical_values) < season_length:
            # Not enough data for seasonal forecasting
            return self._forecast_linear_regression(historical_values, periods)
        
        # Calculate seasonal indices
        seasonal_indices = [0] * season_length
        season_counts = [0] * season_length
        
        # Calculate average for each season position
        for i, value in enumerate(historical_values):
            season_pos = i % season_length
            seasonal_indices[season_pos] += value
            season_counts[season_pos] += 1
        
        # Calculate average for each season position
        for i in range(season_length):
            if season_counts[i] > 0:
                seasonal_indices[i] /= season_counts[i]
            else:
                seasonal_indices[i] = 1.0  # Default if no data
        
        # Calculate overall average
        overall_avg = sum(historical_values) / len(historical_values) if historical_values else 0
        
        # Normalize seasonal indices
        if overall_avg != 0:
            seasonal_indices = [idx / overall_avg for idx in seasonal_indices]
        else:
            seasonal_indices = [1.0] * season_length
        
        # Calculate trend using linear regression
        trend_forecast = self._forecast_linear_regression(historical_values, periods)
        
        # Apply seasonal adjustment
        forecast = []
        for i in range(periods):
            if i < len(historical_values):
                # For overlap periods, use actual values
                forecast.append(historical_values[i])
            else:
                # Get trend value and apply seasonal index
                trend = trend_forecast[i]
                season_pos = i % season_length
                seasonal_value = trend * seasonal_indices[season_pos]
                forecast.append(seasonal_value)
        
        return forecast
    
    def _forecast_arima(self, historical_values: List[float], periods: int, p: int, d: int, q: int) -> List[float]:
        """Forecast using ARIMA method (simplified implementation)."""
        # This is a simplified version of ARIMA
        # In a real implementation, this would use a proper statistical package
        
        # Implement differencing if needed
        values = historical_values.copy()
        original_values = historical_values.copy()
        
        for _ in range(d):
            values = [values[i+1] - values[i] for i in range(len(values)-1)]
            if not values:
                values = [0]
        
        # For simplicity, just use autoregressive (AR) component
        forecast = []
        for i in range(periods):
            if i < len(historical_values):
                # For overlap periods, use actual values
                forecast.append(historical_values[i])
            else:
                # Use AR model for prediction
                prediction = 0
                for j in range(1, p + 1):
                    if i - j >= 0:
                        if i - j < len(values):
                            prediction += values[i - j]  # Use original values if available
                        else:
                            diff_prediction = forecast[i - j]  # Use previous predictions
                            for _ in range(d):
                                # "Integrate" the differenced values back
                                if i - j - 1 >= 0:
                                    diff_prediction = diff_prediction + forecast[i - j - 1]
                            prediction += diff_prediction
                
                if p > 0:
                    prediction /= p  # Average of the last p values
                
                # Apply differencing in reverse to get the actual forecast
                if d > 0 and i > 0:
                    prev_value = forecast[i - 1]
                    forecast.append(prev_value + prediction)
                else:
                    forecast.append(prediction)
        
        return forecast
