"""Main script to orchestrate Haystack building data generation."""

import logging
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

# Add src to path
sys.path.append(str(Path(__file__).parent))

from database.connection import DatabaseConnection
from database.schema_setup import SchemaSetup
from database.data_loader import DataLoader
from generators.entities import EntityGenerator
from generators.time_series import TimeSeriesGenerator
from generators.weather import WeatherSimulator
from generators.schedules import ScheduleGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_generation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
console = Console()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        raise


def setup_database(db_config: Dict[str, Any]) -> tuple[DatabaseConnection, SchemaSetup, DataLoader]:
    """Set up database connections and schema.
    
    Args:
        db_config: Database configuration
        
    Returns:
        Tuple of (DatabaseConnection, SchemaSetup, DataLoader)
    """
    console.print("[bold blue]Setting up database connection...[/bold blue]")
    
    # Initialize database connection
    db = DatabaseConnection(db_config['database'])
    
    # Test connection
    try:
        db.execute_query("SELECT 1")
        console.print("[green]✓[/green] Database connection successful")
    except Exception as e:
        console.print(f"[red]✗[/red] Database connection failed: {e}")
        raise
        
    # Setup schema
    schema = SchemaSetup(db)
    org_id = schema.initialize_organization(
        db_config['organization']['name'],
        db_config['organization']['key']
    )
    console.print(f"[green]✓[/green] Organization setup complete (ID: {org_id})")
    
    # Setup hypertables
    console.print("[yellow]Setting up TimescaleDB hypertables...[/yellow]")
    try:
        db.setup_hypertables()
        console.print("[green]✓[/green] Hypertables configured")
    except Exception as e:
        console.print(f"[yellow]![/yellow] Hypertable setup warning: {e}")
        
    # Create value tables
    schema.create_value_tables(db_config['organization']['key'])
    
    # Initialize data loader
    data_loader = DataLoader(db, db_config['tables']['value_table'])
    
    return db, schema, data_loader


def generate_building_entities(schema: SchemaSetup, building_config: Dict[str, Any]) -> Dict[str, int]:
    """Generate all building entities.
    
    Args:
        schema: SchemaSetup instance
        building_config: Building configuration
        
    Returns:
        Dictionary mapping entity names to IDs
    """
    console.print("[bold blue]Generating building entities...[/bold blue]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Creating entities...", total=None)
        
        entity_gen = EntityGenerator(schema, building_config)
        entity_map = entity_gen.generate_all_entities()
        
        progress.update(task, description=f"Created {len(entity_map)} entities", completed=True)
        
    # Display summary
    equipment_count = sum(1 for key in entity_map.keys() if key.startswith('equip-'))
    point_count = sum(1 for key in entity_map.keys() if key.startswith('point-'))
    
    table = Table(title="Entity Generation Summary")
    table.add_column("Entity Type", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    
    table.add_row("Site", "1")
    table.add_row("Equipment", str(equipment_count))
    table.add_row("Points", str(point_count))
    table.add_row("Total", str(len(entity_map)))
    
    console.print(table)
    
    return entity_map


def generate_historical_data(data_loader: DataLoader, building_config: Dict[str, Any], 
                           entity_map: Dict[str, int], days: int = 30) -> None:
    """Generate historical time-series data.
    
    Args:
        data_loader: DataLoader instance
        building_config: Building configuration
        entity_map: Entity ID mapping
        days: Number of days of data to generate
    """
    console.print(f"[bold blue]Generating {days} days of historical data...[/bold blue]")
    
    # Initialize generators
    ts_gen = TimeSeriesGenerator(building_config, entity_map)
    weather_sim = WeatherSimulator(building_config['weather'])
    schedule_gen = ScheduleGenerator(building_config)
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        # Generate data
        data_task = progress.add_task("Generating time-series data...", total=100)
        
        historical_df = ts_gen.generate_historical_data(days)
        progress.update(data_task, completed=50)
        
        # Insert data in chunks
        chunk_size = 10000
        total_chunks = len(historical_df) // chunk_size + 1
        
        insert_task = progress.add_task("Inserting data into database...", total=total_chunks)
        
        data_loader.insert_dataframe(historical_df, chunk_size)
        progress.update(data_task, completed=100)
        progress.update(insert_task, completed=total_chunks)
        
    console.print(f"[green]✓[/green] Generated {len(historical_df):,} historical data points")


def generate_current_values(data_loader: DataLoader, building_config: Dict[str, Any], 
                          entity_map: Dict[str, int]) -> None:
    """Generate current values for all points.
    
    Args:
        data_loader: DataLoader instance
        building_config: Building configuration
        entity_map: Entity ID mapping
    """
    console.print("[bold blue]Generating current values...[/bold blue]")
    
    ts_gen = TimeSeriesGenerator(building_config, entity_map)
    current_time = datetime.now().replace(second=0, microsecond=0)
    
    # Generate current weather and occupancy
    weather_sim = WeatherSimulator(building_config['weather'])
    schedule_gen = ScheduleGenerator(building_config)
    
    weather = weather_sim.get_current_weather(current_time)
    occupancy = schedule_gen.get_occupancy_ratio(current_time)
    
    # Generate current data points
    current_data = ts_gen._generate_timestamp_data(
        current_time,
        weather['dry_bulb_temp'],
        weather['season'],
        occupancy
    )
    
    # Update current values table
    data_loader.update_current_values(current_data)
    
    console.print(f"[green]✓[/green] Updated {len(current_data)} current values")


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
    
    # Sample data validation
    console.print("\n[bold blue]Sample Data Validation[/bold blue]")
    
    sample_queries = [
        {
            "name": "Average Zone Temperatures",
            "query": """
                SELECT AVG(value_n) as avg_temp 
                FROM core.values_demo v
                JOIN core.entity_tag et ON v.entity_id = et.entity_id
                JOIN core.tag_def td ON et.tag_id = td.id
                WHERE td.name = 'zoneTemp' AND v.ts > NOW() - INTERVAL '1 day'
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
                value = list(result[0].values())[0]
                console.print(f"[green]✓[/green] {sample['name']}: {value}")
            else:
                console.print(f"[yellow]![/yellow] {sample['name']}: No data")
        except Exception as e:
            console.print(f"[red]✗[/red] {sample['name']}: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate Haystack building data')
    parser.add_argument('--db-config', default='config/database_config.yaml',
                       help='Database configuration file')
    parser.add_argument('--building-config', default='config/building_config.yaml',
                       help='Building configuration file')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days of historical data to generate')
    parser.add_argument('--entities-only', action='store_true',
                       help='Only generate entities, skip time-series data')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip validation queries')
    
    args = parser.parse_args()
    
    try:
        # Load configurations
        console.print("[bold green]Haystack Building Data Simulator[/bold green]")
        console.print(f"Loading configuration files...")
        
        db_config = load_config(args.db_config)
        building_config = load_config(args.building_config)
        
        # Setup database
        db, schema, data_loader = setup_database(db_config)
        
        # Generate entities
        entity_map = generate_building_entities(schema, building_config)
        
        if not args.entities_only:
            # Generate historical data
            generate_historical_data(data_loader, building_config, entity_map, args.days)
            
            # Generate current values
            generate_current_values(data_loader, building_config, entity_map)
        
        # Validation
        if not args.skip_validation:
            display_validation_results(db)
        
        console.print("\n[bold green]✓ Data generation completed successfully![/bold green]")
        
        # Connection info
        console.print(f"\n[bold blue]Database Connection:[/bold blue]")
        console.print(f"Host: {db_config['database']['host']}")
        console.print(f"Database: {db_config['database']['database']}")
        console.print(f"Tables: {db_config['tables']['value_table']}, {db_config['tables']['current_table']}")
        
        # Close database connection
        db.close()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logger.exception("Fatal error during data generation")
        sys.exit(1)


if __name__ == '__main__':
    main()