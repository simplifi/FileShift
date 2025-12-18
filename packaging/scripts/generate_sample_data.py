#!/usr/bin/env python3
"""
Sample Data Generator for JSON to CSV Converter
Creates various test datasets for development and testing
"""

import json
import random
import os
from datetime import datetime, timedelta
from pathlib import Path

# Sample data templates
COMPANIES = [
    "Tech Solutions Inc", "Green Energy Co", "Creative Design Studio", "Global Logistics LLC",
    "Health & Wellness Center", "Innovative Software Labs", "Artisan Coffee Roasters",
    "Educational Publishing House", "Sustainable Fashion Brand", "Advanced Manufacturing Corp",
    "Digital Marketing Agency", "Cloud Services Provider", "Biotech Research Lab", 
    "Urban Planning Consultants", "Renewable Resources Corp", "Mobile App Development",
    "Data Analytics Firm", "Cybersecurity Solutions", "E-commerce Platform", "AI Research Institute"
]

DOMAINS = [
    "techsolutions.example", "greenenergy.example", "creativedesign.example", "globallogistics.example",
    "healthwellness.example", "innovativesoftware.example", "artisancoffee.example", "edupublishing.example",
    "sustainablefashion.example", "advancedmfg.example", "digitalmarketing.example", "cloudservices.example",
    "biotechresearch.example", "urbanplanning.example", "renewableresources.example", "mobileapp.example",
    "dataanalytics.example", "cybersecurity.example", "ecommerce.example", "airesearch.example"
]

INDUSTRIES = [
    "technology", "renewable_energy", "design", "logistics", "healthcare", "software",
    "food_beverage", "education", "fashion", "manufacturing", "marketing", "cloud_computing",
    "biotechnology", "consulting", "energy", "mobile", "analytics", "security", "retail", "research"
]

TIERS = ["starter", "professional", "enterprise"]
SUPPORT_LEVELS = ["basic", "standard", "premium"]
ACCOUNT_MANAGERS = [
    "Sarah Johnson", "Michael Chen", "Emily Rodriguez", "David Kim", "Lisa Wang",
    "Alex Thompson", "Morgan Davis", "Jordan Lee", "Casey Miller", "Taylor Brown"
]

def generate_record(record_id):
    """Generate a single JSON record"""
    company_idx = record_id % len(COMPANIES)
    base_date = datetime(2023, 1, 1)
    created_date = base_date + timedelta(days=random.randint(0, 500))
    updated_date = created_date + timedelta(days=random.randint(1, 200))
    
    record = {
        "id": 1000 + record_id,
        "name": f"{COMPANIES[company_idx]} #{record_id}",
        "email": f"contact{record_id}@{DOMAINS[company_idx]}",
        "created_at": created_date.isoformat() + "Z",
        "updated_at": updated_date.isoformat() + "Z",
        "domain": DOMAINS[company_idx],
        "industry": INDUSTRIES[company_idx],
        "employee_count": random.randint(1, 1000),
        "annual_revenue": random.randint(100000, 200000000),
        "metadata": {
            "tier": random.choice(TIERS),
            "support_level": random.choice(SUPPORT_LEVELS),
            "account_manager": random.choice(ACCOUNT_MANAGERS),
            "region": random.choice(["north", "south", "east", "west", "central"]),
            "priority": random.randint(1, 5)
        }
    }
    
    # Add some optional nested fields randomly
    if random.random() > 0.7:
        record["billing"] = {
            "plan": random.choice(["monthly", "annual"]),
            "amount": random.randint(100, 10000),
            "currency": "USD"
        }
    
    if random.random() > 0.8:
        record["integrations"] = {
            "salesforce": random.choice([True, False]),
            "hubspot": random.choice([True, False]),
            "slack": random.choice([True, False])
        }
    
    return record

def create_sample_file(filename, num_records, description=""):
    """Create a sample NDJSON file with specified number of records"""
    print(f"Generating {filename} with {num_records:,} records... {description}")
    
    with open(filename, 'w', encoding='utf-8') as f:
        for i in range(num_records):
            record = generate_record(i)
            f.write(json.dumps(record) + '\n')
            
            # Progress indicator for large files
            if num_records > 1000 and (i + 1) % 10000 == 0:
                print(f"  Progress: {i + 1:,}/{num_records:,} records")
    
    # Show file size
    size = os.path.getsize(filename)
    if size > 1024 * 1024:
        size_str = f"{size / (1024*1024):.1f} MB"
    elif size > 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size} bytes"
    
    print(f"  Created: {filename} ({size_str})")

def generate_ecommerce_record(record_id):
    """Generate e-commerce/order data"""
    products = ["Laptop", "Phone", "Tablet", "Headphones", "Camera", "Watch", "Speakers"]
    statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    
    return {
        "order_id": f"ORD-{10000 + record_id}",
        "customer_id": random.randint(1000, 9999),
        "customer": {
            "name": f"Customer {record_id}",
            "email": f"customer{record_id}@shop.example",
            "address": {
                "street": f"{random.randint(1, 999)} Main St",
                "city": random.choice(["Seattle", "Portland", "San Francisco", "Denver"]),
                "state": random.choice(["WA", "OR", "CA", "CO"]),
                "zip": f"{random.randint(10000, 99999)}"
            }
        },
        "items": [
            {
                "product": random.choice(products),
                "quantity": random.randint(1, 5),
                "price": round(random.uniform(10.99, 999.99), 2),
                "sku": f"SKU-{random.randint(100, 999)}"
            } for _ in range(random.randint(1, 4))
        ],
        "total": round(random.uniform(25.00, 2500.00), 2),
        "status": random.choice(statuses),
        "payment": {
            "method": random.choice(["credit_card", "paypal", "apple_pay"]),
            "last_four": f"{random.randint(1000, 9999)}"
        },
        "created_at": (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 200))).isoformat(),
        "shipping": {
            "carrier": random.choice(["UPS", "FedEx", "USPS"]),
            "tracking": f"TR{random.randint(100000000, 999999999)}",
            "cost": round(random.uniform(5.99, 25.99), 2)
        }
    }

def generate_social_media_record(record_id):
    """Generate social media post data"""
    platforms = ["twitter", "facebook", "instagram", "linkedin"]
    post_types = ["text", "image", "video", "link"]
    
    return {
        "post_id": f"POST-{record_id}",
        "user_id": random.randint(10000, 99999),
        "username": f"user{record_id}",
        "platform": random.choice(platforms),
        "content": {
            "type": random.choice(post_types),
            "text": f"This is sample post content #{record_id}",
            "hashtags": [f"#tag{i}" for i in range(random.randint(0, 5))],
            "mentions": [f"@user{random.randint(1, 100)}" for _ in range(random.randint(0, 3))]
        },
        "engagement": {
            "likes": random.randint(0, 10000),
            "shares": random.randint(0, 1000),
            "comments": random.randint(0, 500),
            "impressions": random.randint(100, 50000)
        },
        "metadata": {
            "device": random.choice(["iPhone", "Android", "Web", "iPad"]),
            "location": random.choice(["New York", "London", "Tokyo", "Sydney"]),
            "language": random.choice(["en", "es", "fr", "de", "ja"])
        },
        "timestamp": (datetime(2024, 1, 1) + timedelta(hours=random.randint(0, 8760))).isoformat()
    }

def generate_iot_sensor_record(record_id):
    """Generate IoT sensor data"""
    sensor_types = ["temperature", "humidity", "pressure", "motion", "light"]
    
    return {
        "sensor_id": f"SENSOR-{1000 + record_id}",
        "device": {
            "name": f"Device {record_id}",
            "location": {
                "building": random.choice(["Building A", "Building B", "Building C"]),
                "floor": random.randint(1, 10),
                "room": f"Room {random.randint(100, 999)}"
            },
            "coordinates": {
                "lat": round(random.uniform(37.0, 38.0), 6),
                "lng": round(random.uniform(-122.5, -121.5), 6)
            }
        },
        "readings": {
            "temperature": round(random.uniform(18.0, 30.0), 2),
            "humidity": round(random.uniform(30.0, 80.0), 1),
            "pressure": round(random.uniform(990.0, 1030.0), 1),
            "light_level": random.randint(0, 1000),
            "motion_detected": random.choice([True, False])
        },
        "status": {
            "battery_level": random.randint(10, 100),
            "signal_strength": random.randint(-80, -30),
            "last_maintenance": (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 100))).isoformat(),
            "error_count": random.randint(0, 5)
        },
        "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 1440))).isoformat()
    }

def generate_financial_record(record_id):
    """Generate financial transaction data"""
    transaction_types = ["debit", "credit", "transfer", "fee", "interest"]
    categories = ["groceries", "gas", "restaurants", "shopping", "utilities", "entertainment"]
    
    return {
        "transaction_id": f"TXN-{100000 + record_id}",
        "account": {
            "number": f"****{random.randint(1000, 9999)}",
            "type": random.choice(["checking", "savings", "credit"]),
            "bank": random.choice(["Chase", "Wells Fargo", "Bank of America", "Citi"])
        },
        "amount": round(random.uniform(-2000.00, 5000.00), 2),
        "type": random.choice(transaction_types),
        "category": random.choice(categories),
        "merchant": {
            "name": f"Merchant {record_id}",
            "category": random.choice(categories),
            "location": {
                "city": random.choice(["New York", "Los Angeles", "Chicago"]),
                "state": random.choice(["NY", "CA", "IL"])
            }
        },
        "date": (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
        "balance_after": round(random.uniform(100.00, 25000.00), 2),
        "pending": random.choice([True, False]),
        "tags": [random.choice(["business", "personal", "tax-deductible"]) for _ in range(random.randint(0, 2))]
    }

def generate_healthcare_record(record_id):
    """Generate healthcare/patient data (anonymized)"""
    conditions = ["hypertension", "diabetes", "asthma", "arthritis", "migraine"]
    medications = ["lisinopril", "metformin", "albuterol", "ibuprofen", "acetaminophen"]
    
    return {
        "patient_id": f"PAT-{10000 + record_id}",
        "demographics": {
            "age_group": random.choice(["18-30", "31-45", "46-60", "61-75", "75+"]),
            "gender": random.choice(["M", "F", "Other"]),
            "zip_code": f"{random.randint(10000, 99999)}"
        },
        "visit": {
            "id": f"VISIT-{record_id}",
            "date": (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d"),
            "type": random.choice(["routine", "urgent", "followup", "emergency"]),
            "department": random.choice(["cardiology", "internal_medicine", "orthopedics", "neurology"])
        },
        "vitals": {
            "blood_pressure": {
                "systolic": random.randint(90, 180),
                "diastolic": random.randint(60, 120)
            },
            "heart_rate": random.randint(60, 100),
            "temperature": round(random.uniform(96.0, 102.0), 1),
            "weight": random.randint(100, 300),
            "height": random.randint(60, 80)
        },
        "conditions": random.sample(conditions, random.randint(0, 3)),
        "medications": random.sample(medications, random.randint(0, 4)),
        "insurance": {
            "provider": random.choice(["Aetna", "BlueCross", "Cigna", "UnitedHealth"]),
            "plan_type": random.choice(["HMO", "PPO", "EPO"])
        }
    }

def generate_log_record(record_id):
    """Generate application log data"""
    levels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
    services = ["auth-service", "user-service", "payment-service", "notification-service"]
    
    return {
        "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 1440))).isoformat(),
        "level": random.choice(levels),
        "service": random.choice(services),
        "host": f"server-{random.randint(1, 10)}.example.com",
        "request_id": f"req-{record_id}-{random.randint(1000, 9999)}",
        "user_id": random.randint(10000, 99999) if random.random() > 0.3 else None,
        "message": f"Sample log message {record_id}",
        "context": {
            "endpoint": random.choice(["/api/users", "/api/orders", "/api/payments", "/api/health"]),
            "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "status_code": random.choice([200, 201, 400, 401, 404, 500]),
            "response_time": random.randint(10, 2000),
            "ip_address": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        },
        "metadata": {
            "version": "1.0.0",
            "environment": random.choice(["production", "staging", "development"]),
            "region": random.choice(["us-east-1", "us-west-2", "eu-west-1"])
        }
    }

def create_specialized_file(filename, generator_func, num_records, description):
    """Create a specialized sample file using a specific generator function"""
    print(f"Generating {filename} with {num_records:,} records... {description}")
    
    with open(filename, 'w', encoding='utf-8') as f:
        for i in range(num_records):
            record = generator_func(i)
            f.write(json.dumps(record) + '\n')
            
            if num_records > 1000 and (i + 1) % 10000 == 0:
                print(f"  Progress: {i + 1:,}/{num_records:,} records")
    
    size = os.path.getsize(filename)
    if size > 1024 * 1024:
        size_str = f"{size / (1024*1024):.1f} MB"
    elif size > 1024:
        size_str = f"{size / 1024:.1f} KB"
    else:
        size_str = f"{size} bytes"
    
    print(f"  Created: {filename} ({size_str})")

def main():
    """Generate various sample data files"""
    print("🔧 JSON to CSV Converter - Sample Data Generator")
    print("=" * 50)
    
    # Create samples directory
    samples_dir = Path("samples")
    samples_dir.mkdir(exist_ok=True)
    
    print("\n📋 Creating basic company data samples...")
    # Small samples for quick testing
    create_sample_file("samples/companies_small.json", 10, "(Quick test)")
    create_sample_file("samples/companies_medium.json", 100, "(Feature testing)")
    create_sample_file("samples/companies_large.json", 1000, "(Performance testing)")
    
    print("\n🛒 Creating e-commerce data samples...")
    create_specialized_file("samples/ecommerce_orders.json", generate_ecommerce_record, 250, "(Order data)")
    
    print("\n📱 Creating social media data samples...")
    create_specialized_file("samples/social_posts.json", generate_social_media_record, 500, "(Social media posts)")
    
    print("\n🌡️ Creating IoT sensor data samples...")
    create_specialized_file("samples/iot_sensors.json", generate_iot_sensor_record, 1000, "(Sensor readings)")
    
    print("\n💰 Creating financial data samples...")
    create_specialized_file("samples/financial_transactions.json", generate_financial_record, 750, "(Bank transactions)")
    
    print("\n🏥 Creating healthcare data samples...")
    create_specialized_file("samples/healthcare_visits.json", generate_healthcare_record, 300, "(Patient visits)")
    
    print("\n📝 Creating application log samples...")
    create_specialized_file("samples/application_logs.json", generate_log_record, 2000, "(Application logs)")
    
    print("\n🔍 Creating specialized structure samples...")
    
    # Flat structure (no nested objects)
    with open("samples/flat_users.json", 'w') as f:
        for i in range(100):
            record = {
                "id": i + 1,
                "first_name": f"User{i + 1}",
                "last_name": f"Lastname{i + 1}",
                "email": f"user{i + 1}@example.com",
                "age": random.randint(18, 65),
                "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                "salary": random.randint(30000, 150000),
                "active": random.choice([True, False]),
                "join_date": (datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1400))).strftime("%Y-%m-%d")
            }
            f.write(json.dumps(record) + '\n')
    
    # Deeply nested structure
    with open("samples/deeply_nested.json", 'w') as f:
        for i in range(50):
            record = {
                "id": i + 1,
                "user": {
                    "profile": {
                        "personal": {
                            "name": f"User {i + 1}",
                            "email": f"user{i + 1}@example.com",
                            "demographics": {
                                "age": random.randint(18, 65),
                                "location": {
                                    "country": "USA",
                                    "coordinates": {
                                        "lat": round(random.uniform(25.0, 49.0), 6),
                                        "lng": round(random.uniform(-125.0, -66.0), 6)
                                    }
                                }
                            }
                        },
                        "preferences": {
                            "theme": random.choice(["dark", "light"]),
                            "notifications": {
                                "email": random.choice([True, False]),
                                "sms": random.choice([True, False]),
                                "push": {
                                    "enabled": random.choice([True, False]),
                                    "frequency": random.choice(["immediate", "hourly", "daily"])
                                }
                            }
                        }
                    },
                    "settings": {
                        "privacy": {
                            "public_profile": random.choice([True, False]),
                            "data_sharing": random.choice([True, False]),
                            "analytics": {
                                "tracking": random.choice([True, False]),
                                "cookies": {
                                    "essential": True,
                                    "analytics": random.choice([True, False]),
                                    "marketing": random.choice([True, False])
                                }
                            }
                        }
                    }
                }
            }
            f.write(json.dumps(record) + '\n')
    
    # Mixed data types sample
    with open("samples/mixed_types.json", 'w') as f:
        for i in range(75):
            record = {
                "id": i + 1,
                "string_field": f"String value {i}",
                "integer_field": random.randint(1, 1000),
                "float_field": round(random.uniform(0.0, 100.0), 3),
                "boolean_field": random.choice([True, False]),
                "null_field": None if random.random() > 0.7 else f"Not null {i}",
                "array_simple": [random.randint(1, 10) for _ in range(random.randint(1, 5))],
                "array_objects": [
                    {"name": f"Item {j}", "value": random.randint(1, 100)}
                    for j in range(random.randint(1, 3))
                ],
                "timestamp": datetime.now().isoformat(),
                "date_only": datetime.now().strftime("%Y-%m-%d"),
                "large_number": random.randint(1000000000, 9999999999),
                "scientific_notation": random.uniform(1e-6, 1e6)
            }
            f.write(json.dumps(record) + '\n')
    
    # Ask before creating very large files
    create_huge = input("\n❓ Create huge sample files (50k+ records)? This may take several minutes [y/N]: ")
    if create_huge.lower().startswith('y'):
        print("\n🚀 Creating large-scale samples (this may take a while)...")
        create_specialized_file("samples/ecommerce_huge.json", generate_ecommerce_record, 50000, "(Large e-commerce dataset)")
        create_specialized_file("samples/logs_huge.json", generate_log_record, 100000, "(Large log dataset)")
        create_specialized_file("samples/iot_huge.json", generate_iot_sensor_record, 75000, "(Large IoT dataset)")
        create_sample_file("samples/companies_huge.json", 250000, "(Massive company dataset)")
    
    print(f"\n✅ Sample data generation complete!")
    print(f"📁 Files created in 'samples/' directory")
    print(f"💡 Use these files to test the JSON to CSV converter")
    
    # Create a README for the samples
    with open("samples/README.md", 'w') as f:
        f.write("""# Sample Data Files

This directory contains various sample JSON files for testing the converter:

## Quick Testing
- `small_10.json` - 10 records for basic functionality testing
- `medium_100.json` - 100 records for feature testing
- `flat_structure.json` - 50 records with no nested objects
- `nested_structure.json` - 20 records with deeply nested data

## Performance Testing
- `medium_1k.json` - 1,000 records
- `large_10k.json` - 10,000 records
- `large_50k.json` - 50,000 records

## Stress Testing (if generated)
- `huge_100k.json` - 100,000 records (~25-50 MB)
- `huge_250k.json` - 250,000 records (~60-120 MB)
- `huge_500k.json` - 500,000 records (~120-250 MB)

## Usage
```bash
# Test with small file
python json_to_csv_converter.py samples/small_10.json

# Test CLI with specific fields
python json_to_csv_cli.py samples/medium_100.json output.csv id,name,email,industry

# Stress test with large file
python json_to_csv_converter.py samples/large_50k.json
```

## Regenerating Data
Run `python generate_sample_data.py` to recreate these files.
""")

if __name__ == "__main__":
    main()