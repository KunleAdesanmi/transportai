import boto3
import csv
from datetime import datetime, timedelta

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('ResponseAbleExpenses')

def generate_weekly_report():
    # 1. Define the timeframe (Last 7 days)
    last_friday = (datetime.utcnow() - timedelta(days=7)).isoformat()
    
    # 2. Pull data from AWS
    # Note: For small tables, scan is fine. For huge fleets, we'd use Query.
    response = table.scan()
    items = response.get('Items', [])
    
    # 3. Filter and Format
    report_file = f"ResponseAble_Report_{datetime.now().strftime('%Y-%m-%d')}.csv"
    headers = ['Timestamp', 'Driver', 'Origin', 'Destination', 'Price (£)']
    
    with open(report_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        total_saved_admin_time = 0
        for item in items:
            # Only include recent items
            if item['timestamp'] > last_friday:
                writer.writerow([
                    item['timestamp'][:10], # Date only
                    item['driver_id'],
                    item['origin'],
                    item['destination'],
                    item['price']
                ])
                total_saved_admin_time += 20 # Estimate 20 mins saved per job
                
    print(f"✅ Report generated: {report_file}")
    print(f"📈 Total Driver Admin Time Saved this week: {total_saved_admin_time // 60} hours.")

if __name__ == "__main__":
    generate_weekly_report()