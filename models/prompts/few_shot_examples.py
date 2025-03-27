"""
Few-shot examples for AI-native ERP system prompts.

This module contains structured examples that can be used to train or prompt
various AI components within the ERP system. These examples demonstrate how to
format inputs and expected outputs for different ERP modules and functions.
"""

class FewShotExamples:
    """Collection of few-shot examples for different ERP modules and functions."""
    
    @staticmethod
    def finance_examples():
        """Examples for finance-related AI tasks."""
        return [
            # Invoice processing example
            {
                "input": "Process this invoice: Invoice #1234 from Acme Corp dated March 15, 2025 for $5,420.80 for IT services.",
                "output": {
                    "invoice_number": "1234",
                    "vendor": "Acme Corp",
                    "date": "2025-03-15",
                    "amount": 5420.80,
                    "currency": "USD",
                    "category": "IT Services",
                    "payment_status": "pending",
                    "suggested_gl_account": "IT-EXPENSES-5000"
                }
            },
            # Financial analysis example
            {
                "input": "Analyze our Q1 expenses and highlight unusual patterns.",
                "output": {
                    "analysis": "Q1 expenses are 12% higher than previous quarter. Three unusual transactions detected: (1) $45,000 payment to DataServ on Jan 15 classified as 'misc', (2) Travel expenses increased 35% despite no change in headcount, (3) Double payment to vendor CloudTech (#INV-3456 and #INV-3457).",
                    "recommendations": ["Reclassify DataServ payment as 'Cloud Infrastructure'", "Audit travel expense approvals", "Request refund for duplicate payment to CloudTech"],
                    "risk_level": "medium",
                    "estimated_financial_impact": "$62,450"
                }
            },
            # Budget forecasting example
            {
                "input": "Create Q2 budget forecast based on current trends and seasonality.",
                "output": {
                    "forecast": {
                        "q2_revenue": 3245000,
                        "q2_expenses": 2145000,
                        "q2_profit_margin": 33.9,
                        "confidence_score": 0.87
                    },
                    "assumptions": [
                        "5% MoM growth in SaaS revenue",
                        "Seasonal 15% increase in marketing spend",
                        "New office lease starting in May"
                    ],
                    "scenarios": {
                        "conservative": {"q2_revenue": 3050000, "q2_expenses": 2200000},
                        "aggressive": {"q2_revenue": 3500000, "q2_expenses": 2100000}
                    }
                }
            }
        ]
    
    @staticmethod
    def hr_examples():
        """Examples for HR-related AI tasks."""
        return [
            # Candidate evaluation example
            {
                "input": "Evaluate this candidate for Senior Developer role: 5 years Python, 3 years React, BS Computer Science, led team of 4 at previous company.",
                "output": {
                    "match_score": 82,
                    "strengths": ["Technical skills match requirements", "Leadership experience"],
                    "gaps": ["No cloud infrastructure experience mentioned", "Limited experience with microservices"],
                    "recommended_interview_focus": ["System design experience", "Team management approach"],
                    "salary_range_fit": "Within established range",
                    "growth_potential": "High - could grow into architecture role"
                }
            },
            # Performance review analysis
            {
                "input": "Summarize key themes from Sarah's annual performance reviews over the last 3 years.",
                "output": {
                    "strengths_consistent": ["Project delivery", "Client communication", "Problem-solving"],
                    "areas_of_improvement": ["Documentation", "Knowledge sharing"],
                    "progress_areas": ["Technical leadership improved significantly in year 2-3"],
                    "risk_factors": ["Workload consistently flagged as too high"],
                    "promotion_readiness": "Ready for senior position based on consistent performance",
                    "retention_recommendations": ["Discuss career path options", "Consider for team lead role"]
                }
            },
            # Team composition analysis
            {
                "input": "Analyze current engineering team composition and identify skill gaps.",
                "output": {
                    "current_composition": {
                        "frontend": 4,
                        "backend": 6,
                        "devops": 1,
                        "qa": 2
                    },
                    "skill_coverage": {
                        "high": ["JavaScript", "Python", "SQL"],
                        "medium": ["AWS", "React", "Node.js"],
                        "low": ["Kubernetes", "Security testing", "Performance optimization"]
                    },
                    "critical_gaps": ["DevOps/SRE experience", "Security engineering"],
                    "hiring_recommendations": [
                        {"role": "DevOps Engineer", "priority": "High"},
                        {"role": "Security Engineer", "priority": "Medium"}
                    ],
                    "training_recommendations": [
                        {"topic": "Kubernetes for developers", "target_audience": "Backend team"},
                        {"topic": "Security best practices", "target_audience": "All engineers"}
                    ]
                }
            }
        ]
    
    @staticmethod
    def supply_chain_examples():
        """Examples for supply chain-related AI tasks."""
        return [
            # Inventory optimization example
            {
                "input": "Optimize inventory levels for product SKU-12345 based on seasonal demand.",
                "output": {
                    "current_inventory": 1250,
                    "recommended_inventory": 950,
                    "reduction_opportunity": 300,
                    "carrying_cost_savings": "$4,500/month",
                    "stockout_risk": "Low (2.3%)",
                    "demand_forecast": {
                        "next_30_days": 420,
                        "next_60_days": 850,
                        "next_90_days": 1200
                    },
                    "reorder_recommendation": {
                        "trigger_point": 500,
                        "order_quantity": 800,
                        "lead_time_buffer": "15 days"
                    }
                }
            },
            # Supplier performance analysis
            {
                "input": "Analyze performance of supplier Acme Electronics over past 12 months.",
                "output": {
                    "on_time_delivery": "86% (industry avg: 92%)",
                    "quality_issues": "3.2% defect rate (industry avg: 1.8%)",
                    "price_competitiveness": "5% below market average",
                    "responsiveness": "Average response time: 2.3 days (industry avg: 1.5 days)",
                    "risk_factors": ["Single source for critical component XYZ-789", "Financial stability concerns based on recent news"],
                    "recommendations": [
                        "Initiate supplier improvement program focusing on quality",
                        "Identify backup suppliers for component XYZ-789",
                        "Renegotiate contract terms to include stricter quality requirements"
                    ]
                }
            },
            # Logistics optimization
            {
                "input": "Find most cost-effective shipping method for 500 units from Chicago to Dallas, needed by March 30.",
                "output": {
                    "options": [
                        {
                            "method": "LTL Freight",
                            "carrier": "XYZ Logistics",
                            "cost": 1250.00,
                            "transit_time": "3-5 days",
                            "carbon_footprint": "Medium",
                            "reliability_score": 92
                        },
                        {
                            "method": "Expedited Ground",
                            "carrier": "FastShip",
                            "cost": 1875.00,
                            "transit_time": "2 days",
                            "carbon_footprint": "High",
                            "reliability_score": 96
                        },
                        {
                            "method": "Standard Ground",
                            "carrier": "EcoShip",
                            "cost": 950.00,
                            "transit_time": "5-7 days",
                            "carbon_footprint": "Low",
                            "reliability_score": 88
                        }
                    ],
                    "recommendation": "LTL Freight with XYZ Logistics",
                    "reasoning": "Balanced option with sufficient delivery time buffer, moderate cost, and good reliability rating",
                    "contingency": "Book by March 22 to ensure on-time arrival, consider expedited option if delayed"
                }
            }
        ]
    
    @staticmethod
    def customer_service_examples():
        """Examples for customer service-related AI tasks."""
        return [
            # Customer inquiry classification
            {
                "input": "I ordered your premium plan last week but was charged for the basic plan. My order number is #45678.",
                "output": {
                    "issue_type": "Billing discrepancy",
                    "priority": "High",
                    "sentiment": "Dissatisfied",
                    "required_actions": ["Verify order details", "Check billing records", "Process refund/adjustment"],
                    "suggested_response": "I understand you were charged incorrectly for your recent order #45678. I'll look into this billing discrepancy right away and ensure you're charged the correct amount for the premium plan you ordered.",
                    "relevant_department": "Billing support",
                    "estimated_resolution_time": "1-2 business days"
                }
            },
            # Customer churn prediction
            {
                "input": "Analyze account activity for customer Acme Corp (customer_id: 12345) and assess churn risk.",
                "output": {
                    "churn_risk": "High (78%)",
                    "warning_signals": [
                        "50% decrease in platform usage over past 2 months",
                        "Support tickets increased from 1 to 5 per month",
                        "Renewal date approaching in 45 days",
                        "Key stakeholder changed (previous champion left company)"
                    ],
                    "account_health": {
                        "current_score": 35,
                        "previous_score": 72,
                        "trend": "Declining rapidly"
                    },
                    "recommended_interventions": [
                        {"action": "Executive customer success meeting", "priority": "Urgent"},
                        {"action": "Targeted training session for new stakeholders", "priority": "High"},
                        {"action": "Discount offer on renewal", "priority": "Medium"}
                    ],
                    "potential_annual_revenue_at_risk": "$75,000"
                }
            },
            # Customer feedback analysis
            {
                "input": "Analyze customer feedback from satisfaction survey for Q1 2025.",
                "output": {
                    "overall_satisfaction": 7.8,
                    "nps_score": 32,
                    "response_rate": "24% (1240 responses)",
                    "key_themes": {
                        "positive": ["Ease of use", "Customer support responsiveness", "Product reliability"],
                        "negative": ["Mobile app performance", "Integration complexity", "Documentation quality"]
                    },
                    "sentiment_breakdown": {
                        "positive": "62%",
                        "neutral": "21%",
                        "negative": "17%"
                    },
                    "critical_issues": ["Mobile app crashes reported by 8% of respondents", "Integration issues cited as blocker by 5% of enterprise customers"],
                    "improvement_recommendations": [
                        {"area": "Mobile app stability", "impact": "High", "affected_segment": "All users"},
                        {"area": "Integration documentation", "impact": "Medium", "affected_segment": "Enterprise customers"},
                        {"area": "Video tutorials", "impact": "Medium", "affected_segment": "New users"}
                    ],
                    "trend_vs_previous_quarter": "+0.5 points in overall satisfaction, -2 points in NPS"
                }
            }
        ]
    
    @staticmethod
    def ai_workflow_examples():
        """Examples for AI workflow and automation tasks."""
        return [
            # Process automation example
            {
                "input": "Automate the monthly financial reporting process.",
                "output": {
                    "process_analysis": {
                        "current_steps": 12,
                        "automatable_steps": 9,
                        "required_human_review": 3,
                        "current_time_required": "3 business days",
                        "estimated_automated_time": "4 hours"
                    },
                    "workflow_design": [
                        {"step": "Data collection", "agent": "DataFetchAgent", "source_systems": ["ERP", "CRM", "Banking API"]},
                        {"step": "Data validation", "agent": "DataQualityAgent", "rules": ["Completeness check", "Anomaly detection"]},
                        {"step": "Financial calculations", "agent": "FinanceAnalyticsAgent", "calculations": ["Revenue recognition", "Expense categorization"]},
                        {"step": "Report generation", "agent": "ReportGenerationAgent", "formats": ["PDF", "Excel", "Interactive dashboard"]},
                        {"step": "Human review", "assignee_role": "Finance Manager", "focus_areas": ["Unusual variances", "Commentary", "Final approval"]},
                        {"step": "Distribution", "agent": "CommunicationAgent", "channels": ["Email", "Intranet", "Secure portal"]}
                    ],
                    "required_integrations": ["QuickBooks API", "Salesforce API", "Banking APIs", "Excel", "Power BI"],
                    "estimated_roi": {
                        "time_savings": "32 hours per month",
                        "error_reduction": "Estimated 95% reduction in data entry errors",
                        "cost_savings": "$3,800 per month"
                    },
                    "implementation_timeline": "3-4 weeks"
                }
            },
            # Decision automation
            {
                "input": "Create an automated credit approval workflow for new customers.",
                "output": {
                    "decision_framework": {
                        "input_data_points": ["Credit score", "Payment history", "Order size", "Company age", "Industry"],
                        "decision_logic": [
                            {"rule": "Credit score > 700 AND company age > 2 years", "outcome": "Automatic approval", "credit_limit": "Up to $50,000"},
                            {"rule": "Credit score 600-700 OR company age < 2 years", "outcome": "Manual review", "assigned_to": "Credit team"},
                            {"rule": "Credit score < 600", "outcome": "Prepayment required", "deposit_percentage": "50%"}
                        ],
                        "confidence_threshold": 0.85
                    },
                    "workflow_steps": [
                        {"step": "Data collection", "source": ["Customer application", "Credit bureau API", "Internal history"]},
                        {"step": "Risk scoring", "agent": "CreditRiskAgent", "model": "GradientBoosting"},
                        {"step": "Decision application", "agent": "DecisionAgent"},
                        {"step": "Notification", "agent": "CommunicationAgent", "targets": ["Customer", "Sales rep", "Finance team"]},
                        {"step": "Documentation", "agent": "ComplianceAgent", "artifacts": ["Decision record", "Audit trail"]}
                    ],
                    "performance_monitoring": {
                        "metrics": ["Decision accuracy", "Processing time", "Bad debt ratio"],
                        "review_frequency": "Weekly",
                        "learning_feedback": "Continuous model updating based on payment performance"
                    },
                    "human_oversight": {
                        "review_triggers": ["Any credit line > $25,000", "Model confidence < 85%", "New industry segment"],
                        "escalation_path": "Credit Manager"
                    }
                }
            },
            # Anomaly detection
            {
                "input": "Create an anomaly detection system for monitoring procurement transactions.",
                "output": {
                    "detection_framework": {
                        "data_sources": ["Purchase orders", "Vendor master", "Invoice system", "Payment history"],
                        "anomaly_types": [
                            {"type": "Price variance", "threshold": "> 20% from historical average"},
                            {"type": "Unusual vendor", "criteria": "New vendor + Large transaction + Rush order"},
                            {"type": "Order splitting", "pattern": "Multiple orders below approval threshold from same vendor within 48 hours"},
                            {"type": "Invoice anomalies", "signals": ["Duplicate invoices", "Rounded amounts", "Missing documentation"]}
                        ]
                    },
                    "workflow_integration": {
                        "monitoring": {"frequency": "Real-time", "batch_jobs": "Daily reconciliation"},
                        "alerting": {
                            "priority_levels": ["Low", "Medium", "High", "Critical"],
                            "notification_channels": ["Dashboard", "Email", "SMS for critical"],
                            "assignment_logic": "Rules-based routing to appropriate reviewer"
                        },
                        "investigation_support": {
                            "context_gathering": "Automatic collection of related transactions and documentation",
                            "visualization": "Network graph of related vendors, employees, and transactions",
                            "risk_scoring": "Composite score based on multiple anomaly factors"
                        }
                    },
                    "continuous_improvement": {
                        "feedback_loop": "Investigation outcomes feed back to model",
                        "learning_approach": "Supervised learning with human-validated outcomes",
                        "performance_metrics": ["Precision", "Recall", "False positive rate", "Time to detection"]
                    },
                    "estimated_benefits": {
                        "fraud_prevention": "$120,000 - $180,000 annually",
                        "process_efficiency": "85% reduction in manual review time",
                        "compliance": "Improved audit readiness and documentation"
                    }
                }
            }
        ]
    
    @staticmethod
    def multi_agent_coordination_examples():
        """Examples for multi-agent coordination in complex processes."""
        return [
            # Order-to-cash process example
            {
                "input": "Execute order-to-cash process for new order #12345 from customer Acme Corp.",
                "output": {
                    "process_status": "Initiated",
                    "order_details": {
                        "order_id": "12345",
                        "customer": "Acme Corp",
                        "value": "$27,500",
                        "priority": "Standard"
                    },
                    "agent_assignments": [
                        {
                            "agent": "OrderValidationAgent",
                            "task": "Validate order details and customer credit status",
                            "status": "In progress",
                            "estimated_completion": "5 minutes"
                        },
                        {
                            "agent": "InventoryAgent",
                            "task": "Check inventory availability and allocate stock",
                            "status": "Scheduled",
                            "dependencies": ["OrderValidationAgent completion"]
                        },
                        {
                            "agent": "LogisticsAgent",
                            "task": "Determine optimal fulfillment and shipping method",
                            "status": "Scheduled",
                            "dependencies": ["InventoryAgent completion"]
                        },
                        {
                            "agent": "BillingAgent",
                            "task": "Create and send invoice",
                            "status": "Scheduled",
                            "dependencies": ["LogisticsAgent confirmation"]
                        },
                        {
                            "agent": "CustomerCommunicationAgent",
                            "task": "Send order confirmation and delivery updates",
                            "status": "Partially completed",
                            "notes": "Initial confirmation sent, tracking updates pending"
                        }
                    ],
                    "process_monitoring": {
                        "current_stage": "Order validation",
                        "next_milestone": "Inventory allocation",
                        "overall_progress": "15%",
                        "estimated_completion": "March 29, 2025",
                        "exceptions": "None"
                    },
                    "handoffs": [
                        {
                            "from": "OrderValidationAgent",
                            "to": "InventoryAgent",
                            "data_transferred": ["Validated line items", "Shipping priority", "Customer location"],
                            "status": "Pending"
                        }
                    ]
                }
            },
            # Strategic planning example
            {
                "input": "Develop Q2 marketing plan based on Q1 performance and market intelligence.",
                "output": {
                    "process_status": "Completed",
                    "coordination_details": {
                        "agent_collaboration": [
                            {
                                "agent": "DataAnalysisAgent",
                                "contribution": "Analyzed Q1 campaign performance data",
                                "key_findings": ["Email campaigns outperformed social media by 35%", "Product X conversion rate declined 12%", "Customer acquisition cost increased 8%"]
                            },
                            {
                                "agent": "MarketIntelligenceAgent",
                                "contribution": "Gathered competitive and industry insights",
                                "key_findings": ["Competitor launched similar product at 15% lower price point", "Industry keyword costs increased 22%", "New channel opportunity identified: podcast advertising"]
                            },
                            {
                                "agent": "BudgetAgent",
                                "contribution": "Optimized budget allocation based on ROAS",
                                "key_findings": ["Reallocated 30% of social budget to email marketing", "Increased content marketing by 15%", "Created contingency fund for emerging channels"]
                            },
                            {
                                "agent": "CreativeAgent",
                                "contribution": "Generated campaign concepts and messaging",
                                "key_findings": ["Developed 3 creative directions with 5 message variations each", "A/B testing plan for headline optimization", "Updated style guide for Q2 campaigns"]
                            },
                            {
                                "agent": "PlanningAgent",
                                "contribution": "Synthesized inputs into cohesive plan",
                                "key_findings": ["12-week campaign calendar", "Channel integration strategy", "Success metrics and monitoring framework"]
                            }
                        ],
                        "conflict_resolution": [
                            {
                                "conflict": "Budget allocation disagreement between channels",
                                "resolution_approach": "Scenario modeling with sensitivity analysis",
                                "outcome": "Hybrid approach with performance-based adjustments"
                            }
                        ],
                        "consensus_decisions": [
                            "Increase email frequency from biweekly to weekly",
                            "Launch retargeting campaign for abandoned carts",
                            "Pause Product X promotion pending pricing review"
                        ]
                    },
                    "final_plan": {
                        "url": "marketing-plans/q2-2025-final.pdf",
                        "version": "1.2",
                        "approval_status": "Pending executive review"
                    }
                }
            },
            # Cross-functional process example
            {
                "input": "Coordinate new product launch process for Product XYZ-100.",
                "output": {
                    "process_status": "In progress",
                    "product_details": {
                        "name": "XYZ-100",
                        "category": "Enterprise Software",
                        "launch_date": "May 15, 2025",
                        "readiness": "75%"
                    },
                    "department_coordination": [
                        {
                            "department": "Product Development",
                            "agent": "ProductDevelopmentAgent",
                            "status": "On track",
                            "deliverables": [
                                {"item": "Final QA testing", "status": "In progress", "due": "April 10"},
                                {"item": "Documentation", "status": "Completed", "completion_date": "March 15"}
                            ],
                            "blockers": "None"
                        },
                        {
                            "department": "Marketing",
                            "agent": "MarketingAgent",
                            "status": "At risk",
                            "deliverables": [
                                {"item": "Campaign materials", "status": "Delayed", "due": "April 1", "revised_due": "April 10"},
                                {"item": "Website updates", "status": "In progress", "due": "April 15"}
                            ],
                            "blockers": "Awaiting final product screenshots"
                        },
                        {
                            "department": "Sales",
                            "agent": "SalesEnablementAgent",
                            "status": "On track",
                            "deliverables": [
                                {"item": "Training materials", "status": "In progress", "due": "April 20"},
                                {"item": "Pricing strategy", "status": "Completed", "completion_date": "March 10"}
                            ],
                            "blockers": "None"
                        },
                        {
                            "department": "Customer Support",
                            "agent": "SupportAgent",
                            "status": "On track",
                            "deliverables": [
                                {"item": "Knowledge base articles", "status": "In progress", "due": "April 25"},
                                {"item": "Support team training", "status": "Scheduled", "due": "May 1"}
                            ],
                            "blockers": "None"
                        }
                    ],
                    "cross_functional_coordination": {
                        "weekly_sync_meetings": "Every Tuesday at 10am",
                        "shared_workspace": "product-launch/xyz-100",
                        "critical_path_items": [
                            "Final QA signoff",
                            "Marketing materials completion",
                            "Sales training completion"
                        ],
                        "risk_mitigation": [
                            {"risk": "Marketing materials delay", "mitigation": "Assigned additional designer, prioritized critical assets"},
                            {"risk": "Last-minute feature changes", "mitigation": "Feature freeze implemented March 20, exception process defined"}
                        ]
                    },
                    "next_actions": [
                        {"action": "Follow up on marketing materials progress", "owner": "ProjectCoordinationAgent", "due": "March 29"},
                        {"action": "Schedule final go/no-go decision meeting", "owner": "ProjectCoordinationAgent", "due": "April 25"}
                    ]
                }
            }
        ]
    
    @staticmethod
    def dashboard_and_visualization_examples():
        """Examples for dashboard and data visualization AI tasks."""
        return [
            # Executive dashboard example
            {
                "input": "Create an executive dashboard showing key business metrics for Q1 2025.",
                "output": {
                    "dashboard_configuration": {
                        "title": "Executive Performance Dashboard - Q1 2025",
                        "refresh_rate": "Daily at 6:00 AM",
                        "access_control": "Executive team and department heads",
                        "layout": "Responsive grid with 6 primary tiles and drill-down capability"
                    },
                    "data_sources": [
                        {"source": "Financial system", "metrics": ["Revenue", "Expenses", "Profit", "Cash flow"]},
                        {"source": "CRM", "metrics": ["Sales pipeline", "Conversion rates", "Customer acquisition cost"]},
                        {"source": "HR system", "metrics": ["Headcount", "Turnover", "Productivity"]},
                        {"source": "Operations", "metrics": ["Production output", "Quality metrics", "On-time delivery"]},
                        {"source": "Customer support", "metrics": ["Ticket volume", "Resolution time", "CSAT"]}
                    ],
                    "visualization_components": [
                        {
                            "title": "Financial Summary",
                            "type": "Scorecard with trend indicators",
                            "metrics": ["Revenue: $12.5M (+8% YoY)", "Gross margin: 62% (+2pts)", "EBITDA: $3.2M (+5%)"],
                            "visualization": "Key numbers with directional arrows and sparklines"
                        },
                        {
                            "title": "Sales Performance",
                            "type": "Multi-series chart",
                            "metrics": ["Monthly sales by product line", "Pipeline coverage ratio", "Win rate"],
                            "visualization": "Stacked bar chart with trend line overlay"
                        },
                        {
                            "title": "Operational Efficiency",
                            "type": "Gauge charts and KPIs",
                            "metrics": ["Production capacity utilization", "Order fulfillment time", "Quality index"],
                            "visualization": "Radial gauges with thresholds and comparison to targets"
                        },
                        {
                            "title": "Customer Metrics",
                            "type": "Combined chart",
                            "metrics": ["NPS trend", "Customer acquisition", "Churn rate"],
                            "visualization": "Line chart with annotations for key events and initiatives"
                        },
                        {
                            "title": "Market Performance",
                            "type": "Geospatial visualization",
                            "metrics": ["Regional sales performance", "Market penetration", "Growth opportunities"],
                            "visualization": "Interactive map with color-coded regions and drill-down"
                        },
                        {
                            "title": "Risk Indicators",
                            "type": "Heat map",
                            "metrics": ["Supply chain disruptions", "Competitive threats", "Regulatory compliance"],
                            "visualization": "Color-coded matrix showing risk severity and probability"
                        }
                    ],
                    "interactivity": {
                        "filters": ["Time period", "Product line", "Region", "Customer segment"],
                        "drill_down": "Ability to explore underlying data behind each visualization",
                        "alerts": "Configurable thresholds for key metrics with email/mobile notifications"
                    },
                    "insights_layer": {
                        "automated_analysis": "AI-generated insights highlighting key changes, anomalies, and opportunities",
                        "predictive_elements": "Forecast indicators for next-quarter performance",
                        "recommended_actions": "Suggested focus areas based on current performance"
                    }
                }
            },
            # Operational dashboard example
            {
                "input": "Create a supply chain operations dashboard for the manufacturing team.",
                "output": {
                    "dashboard_configuration": {
                        "title": "Manufacturing Operations Command Center",
                        "refresh_rate": "Real-time with 5-minute data updates",
                        "access_control": "Operations team, shift supervisors, plant managers",
                        "layout": "Modular grid with status indicators and detailed views"
                    },
                    "data_sources": [
                        {"source": "ERP system", "metrics": ["Production orders", "Material availability", "Work in progress"]},
                        {"source": "MES", "metrics": ["Machine status", "Production rates", "Quality test results"]},
                        {"source": "IIoT sensors", "metrics": ["Equipment performance", "Energy consumption", "Environmental conditions"]},
                        {"source": "Warehouse management", "metrics": ["Inventory levels", "Space utilization", "Picking performance"]},
                        {"source": "Transportation management", "metrics": ["Inbound shipments", "Outbound deliveries", "Carrier performance"]}
                    ],
                    "visualization_components": [
                        {
                            "title": "Production Status",
                            "type": "Real-time monitoring board",
                            "metrics": ["OEE by production line", "Current production rate vs. target", "Downtime incidents"],
                            "visualization": "Production line diagram with status indicators and performance metrics"
                        },
                        {
                            "title": "Material Flow",
                            "type": "Sankey diagram",
                            "metrics": ["Material movement through production stages", "Bottlenecks", "WIP levels"],
                            "visualization": "Flow diagram with color-coded volume indicators and bottleneck highlights"
                        },
                        {
                            "title": "Quality Control",
                            "type": "Statistical process control charts",
                            "metrics": ["Defect rates by product type", "Process capability indices", "Quality alerts"],
                            "visualization": "Control charts with upper/lower control limits and trend lines"
                        },
                        {
                            "title": "Inventory Management",
                            "type": "Heat map and bar charts",
                            "metrics": ["Inventory turnover by SKU", "Stockout risks", "Slow-moving items"],
                            "visualization": "Heat map of inventory levels, bar charts for turnover rates"
                        },
                        {
                            "title": "Logistics Performance",
                            "type": "KPI summary",
                            "metrics": ["On-time delivery rate", "Freight cost per unit", "Carrier performance scores"],
                            "visualization": "Tabular summary with color-coded status indicators"
                        },
                        {
                            "title": "Energy Consumption",
                            "type": "Trend charts",
                            "metrics": ["Electricity usage by department", "Energy cost trends", "Sustainability metrics"],
                            "visualization": "Line charts showing historical usage and cost trends"
                        }
                    ],
                    "interactivity": {
                        "filters": ["Production line", "Product type", "Shift", "Date range"],
                        "drill_down": "Detailed views for each production line and equipment",
                        "alerts": "Automated alerts for critical issues and performance deviations"
                    },
                    "insights_layer": {
                        "root_cause_analysis": "Identify key factors contributing to production delays or quality issues",
                        "predictive_maintenance": "Forecast equipment maintenance needs based on usage patterns",
                        "continuous_improvement": "Recommendations for process optimization and efficiency gains"
                    }
                }
            },
            # Sales performance dashboard
            {
                "input": "Develop a sales performance dashboard for the sales team.",
                "output": {
                    "dashboard_configuration": {
                        "title": "Sales Performance Analytics",
                        "refresh_rate": "Hourly with real-time data feeds",
                        "access_control": "Sales team, managers, executive leadership",
                        "layout": "Customizable widgets with drag-and-drop interface"
                    },
                    "data_sources": [
                        {"source": "CRM system", "metrics": ["Leads generated", "Opportunities", "Won deals"]},
                        {"source": "Marketing automation", "metrics": ["Campaign effectiveness", "Lead scoring", "ROI"]},
                        {"source": "Financial system", "metrics": ["Revenue by product", "Sales pipeline value", "Commission payouts"]},
                        {"source": "Customer support", "metrics": ["Customer satisfaction scores", "Renewal rates", "Churn analysis"]},
                        {"source": "Competitive intelligence", "metrics": ["Win/loss analysis", "Market share trends", "Pricing comparison"]}
                    ],
                    "visualization_components": [
                        {
                            "title": "Pipeline Overview",
                            "type": "Funnel chart",
                            "metrics": ["Leads by stage", "Conversion rates", "Deal values"],
                            "visualization": "Interactive funnel with stage breakdown and conversion metrics"
                        },
                        {
                            "title": "Deal Performance",
                            "type": "Bubble chart",
                            "metrics": ["Deal size vs. win rate", "Sales cycle duration", "Deal profitability"],
                            "visualization": "Bubble chart with size representing deal value and color for win rate"
                        },
                        {
                            "title": "Revenue Analysis",
                            "type": "Stacked area chart",
                            "metrics": ["Monthly revenue trends", "Product mix contribution", "Regional performance"],
                            "visualization": "Area chart showing revenue composition over time"
                        },
                        {
                            "title": "Customer Insights",
                            "type": "Heat map and scatter plot",
                            "metrics": ["Customer lifetime value", "Churn risk", "Cross-sell opportunities"],
                            "visualization": "Heat map of customer segments and scatter plot for CLV vs. churn risk"
                        },
                        {
                            "title": "Competitive Benchmarking",
                            "type": "Bar chart and radar plot",
                            "metrics": ["Win rates vs. competitors", "Pricing comparison
                            "visualization": "Bar chart for win rates and radar plot for feature comparison"
                        },
                        {
                            "title": "Performance Summary",
                            "type": "KPI dashboard",
                            "metrics": ["Sales targets vs. actuals", "Team performance", "Deal close ratios"],
                            "visualization": "Tabular summary with color-coded indicators and trend arrows"
                        }
                    ],
                    "interactivity": {
                        "filters": ["Time period", "Sales region", "Product category", "Sales rep"],
                        "drill_down": "Detailed views for individual deals and customer profiles",
                        "alerts": "Automated alerts for deal milestones and performance thresholds"
                    },
                    "insights_layer": {
                        "predictive_forecasts": "AI-generated sales forecasts and lead conversion predictions",
                        "opportunity_identification": "Recommendations for upsell, cross-sell, and deal acceleration",
                        "performance_benchmarks": "Comparison to industry benchmarks and internal goals"
                    }
                }
            }
        ]