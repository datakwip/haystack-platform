"""Standalone validation script to check database contents without modifying data."""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'src'))

import yaml
from database.connection import DatabaseConnection
from rich.console import Console
from rich.table import Table

console = Console()

def display_validation_results(db: DatabaseConnection) -> None:
    """Display validation queries and results.
    
    Args:
        db: DatabaseConnection instance
    """
    console.print("\n[bold blue]Validation Results[/bold blue]")
    
    # Get row counts
    queries = {
        "Entities": "SELECT COUNT(*) as count FROM core.entity",
        "Entity Tags": "SELECT COUNT(*) as count FROM core.entity_tag", 
        "Time-series Records": "SELECT COUNT(*) as count FROM core.values_demo",
        "Current Values": "SELECT COUNT(*) as count FROM core.values_demo_current"
    }
    
    table = Table(title="Database Summary")
    table.add_column("Table", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    
    for name, query in queries.items():
        try:
            result = db.execute_query(query)
            count = result[0]['count'] if result else 0
            table.add_row(name, f"{count:,}")
        except Exception as e:
            table.add_row(name, f"Error: {e}")
            
    console.print(table)
    
    # Time range analysis
    console.print("\n[bold blue]Time Range Analysis[/bold blue]")
    
    time_queries = [
        {
            "name": "Historical Data Range",
            "query": """
                SELECT 
                    MIN(ts) as earliest,
                    MAX(ts) as latest,
                    COUNT(*) as total_records
                FROM core.values_demo
            """
        },
        {
            "name": "Current Values Latest",
            "query": """
                SELECT 
                    MIN(ts) as earliest,
                    MAX(ts) as latest,
                    COUNT(*) as total_records
                FROM core.values_demo_current
            """
        }
    ]
    
    for query_info in time_queries:
        try:
            result = db.execute_query(query_info['query'])
            if result:
                data = result[0]
                console.print(f"[cyan]{query_info['name']}:[/cyan]")
                console.print(f"  Earliest: {data['earliest']}")
                console.print(f"  Latest: {data['latest']}")
                console.print(f"  Records: {data['total_records']:,}")
            else:
                console.print(f"[yellow]WARNING[/yellow] {query_info['name']}: No data")
        except Exception as e:
            console.print(f"[red]ERROR[/red] {query_info['name']}: {e}")
    
    # Check what tags actually exist
    console.print("\n[bold blue]Available Tags Analysis[/bold blue]")
    
    tag_queries = [
        {
            "name": "Temperature-related Tags",
            "query": """
                SELECT DISTINCT td.name, COUNT(*) as usage_count
                FROM core.tag_def td
                JOIN core.entity_tag et ON td.id = et.tag_id
                WHERE td.name ILIKE '%temp%'
                GROUP BY td.name
                ORDER BY usage_count DESC
            """
        },
        {
            "name": "All Point Tags (Top 10)",
            "query": """
                SELECT DISTINCT td.name, COUNT(*) as usage_count
                FROM core.tag_def td
                JOIN core.entity_tag et ON td.id = et.tag_id
                JOIN core.entity_tag et2 ON et.entity_id = et2.entity_id
                JOIN core.tag_def td2 ON et2.tag_id = td2.id
                WHERE td2.name = 'point'
                GROUP BY td.name
                ORDER BY usage_count DESC
                LIMIT 10
            """
        }
    ]
    
    for query_info in tag_queries:
        try:
            result = db.execute_query(query_info['query'])
            if result:
                console.print(f"[cyan]{query_info['name']}:[/cyan]")
                for row in result:
                    console.print(f"  {row['name']}: {row['usage_count']} entities")
            else:
                console.print(f"[yellow]WARNING[/yellow] {query_info['name']}: No data")
        except Exception as e:
            console.print(f"[red]ERROR[/red] {query_info['name']}: {e}")

    # Sample data validation with better time ranges
    console.print("\n[bold blue]Sample Data Validation[/bold blue]")
    
    sample_queries = [
        {
            "name": "Average Zone Temperatures (All Data)",
            "query": """
                SELECT AVG(v.value_n) as avg_temp, COUNT(*) as sample_count
                FROM core.values_demo v
                JOIN core.entity_tag et ON v.entity_id = et.entity_id
                JOIN core.tag_def td ON et.tag_id = td.id
                WHERE td.name = 'temp'
            """
        },
        {
            "name": "Zone Temperature Range",
            "query": """
                SELECT 
                    MIN(v.value_n) as min_temp,
                    MAX(v.value_n) as max_temp,
                    AVG(v.value_n) as avg_temp
                FROM core.values_demo v
                JOIN core.entity_tag et ON v.entity_id = et.entity_id
                JOIN core.tag_def td ON et.tag_id = td.id
                WHERE td.name = 'temp'
            """
        },
        {
            "name": "Latest Chiller Status",
            "query": """
                SELECT COUNT(*) as running_chillers
                FROM core.values_demo_current v
                JOIN core.entity_tag et ON v.entity_id = et.entity_id  
                JOIN core.tag_def td ON et.tag_id = td.id
                WHERE td.name = 'status' AND v.value_b = true
                AND et.entity_id IN (
                    SELECT DISTINCT et2.entity_id 
                    FROM core.entity_tag et2
                    JOIN core.tag_def td2 ON et2.tag_id = td2.id
                    WHERE td2.name = 'chiller'
                )
            """
        }
    ]
    
    for sample in sample_queries:
        try:
            result = db.execute_query(sample['query'])
            if result:
                data = result[0]
                if sample['name'] == "Average Zone Temperatures (All Data)":
                    console.print(f"[green]OK[/green] {sample['name']}: {data['avg_temp']:.1f}°F ({data['sample_count']:,} readings)")
                elif sample['name'] == "Zone Temperature Range":
                    console.print(f"[green]OK[/green] {sample['name']}: {data['min_temp']:.1f}°F - {data['max_temp']:.1f}°F (avg: {data['avg_temp']:.1f}°F)")
                else:
                    # Handle other queries with single values
                    value = list(data.values())[0]
                    console.print(f"[green]OK[/green] {sample['name']}: {value}")
            else:
                console.print(f"[yellow]WARNING[/yellow] {sample['name']}: No data")
        except Exception as e:
            console.print(f"[red]ERROR[/red] {sample['name']}: {e}")

def main():
    """Main validation function."""
    console.print("[bold green]Database Validation (Read-Only)[/bold green]")
    
    # Load database config
    try:
        with open('config/database_config.yaml', 'r') as f:
            db_config = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Failed to load database config: {e}[/red]")
        return
    
    # Connect and validate
    try:
        db = DatabaseConnection(db_config['database'])
        display_validation_results(db)
        console.print("\n[bold green]Validation completed successfully![/bold green]")
    except Exception as e:
        console.print(f"\n[red]Validation failed: {e}[/red]")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    main()