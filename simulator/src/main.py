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
        console.print("[green]OK[/green] Database connection successful")
    except Exception as e:
        console.print(f"[red]ERROR[/red] Database connection failed: {e}")
        raise
        
    # Setup schema
    schema = SchemaSetup(db)
    org_id, org_key = schema.initialize_organization(
        db_config['organization']['name'],
        db_config['organization']['key']
    )
    console.print(f"[green]OK[/green] Organization setup complete (ID: {org_id}, Key: {org_key})")

    # Create test user ONLY for simulator orgs (safety checked)
    try:
        test_user_id = schema.initialize_test_user(org_id, org_key, "test@datakwip.local")
        console.print(f"[green]OK[/green] Test user created (ID: {test_user_id})")
    except ValueError as e:
        console.print(f"[yellow]SKIP[/yellow] {str(e)}")
    
    # Setup hypertables
    console.print("[yellow]Setting up TimescaleDB hypertables...[/yellow]")
    try:
        db.setup_hypertables(
            value_table=db_config['tables']['value_table'],
            current_table=db_config['tables']['current_table']
        )
        console.print("[green]OK[/green] Hypertables configured")
    except Exception as e:
        console.print(f"[yellow]WARNING[/yellow] Hypertable setup warning: {e}")
        
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
    
    console.print("Creating entities...")
    
    entity_gen = EntityGenerator(schema, building_config)
    entity_map = entity_gen.generate_all_entities()
    
    console.print(f"Created {len(entity_map)} entities")
        
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
    
    # Generate data
    console.print("Generating time-series data...")
    historical_df = ts_gen.generate_historical_data(days)
    
    # Insert data in chunks
    console.print("Inserting data into database...")
    chunk_size = 10000
    data_loader.insert_dataframe(historical_df, chunk_size)
        
    console.print(f"[green]OK[/green] Generated {len(historical_df):,} historical data points")


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
    
    console.print(f"[green]OK[/green] Updated {len(current_data)} current values")


def display_validation_results(db: DatabaseConnection, db_config: Dict[str, Any]) -> None:
    """Display validation queries and results.

    Args:
        db: DatabaseConnection instance
        db_config: Database configuration dictionary
    """
    console.print("\n[bold blue]Validation Results[/bold blue]")

    value_table = db_config['tables']['value_table']
    current_table = db_config['tables']['current_table']

    # Get row counts
    queries = {
        "Entities": "SELECT COUNT(*) as count FROM core.entity",
        "Entity Tags": "SELECT COUNT(*) as count FROM core.entity_tag",
        "Time-series Records": f"SELECT COUNT(*) as count FROM core.{value_table}",
        "Current Values": f"SELECT COUNT(*) as count FROM core.{current_table}"
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
            "query": f"""
                SELECT AVG(v.value_n) as avg_temp
                FROM core.{value_table} v
                JOIN core.entity_tag et ON v.entity_id = et.entity_id
                JOIN core.tag_def td ON et.tag_id = td.id
                WHERE td.name = 'temp' AND v.ts > NOW() - INTERVAL '1 day'
            """
        },
        {
            "name": "Latest Chiller Status",
            "query": f"""
                SELECT COUNT(*) as running_chillers
                FROM core.{current_table} v
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
                console.print(f"[green]OK[/green] {sample['name']}: {value}")
            else:
                console.print(f"[yellow]WARNING[/yellow] {sample['name']}: No data")
        except Exception as e:
            console.print(f"[red]ERROR[/red] {sample['name']}: {e}")


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
    parser.add_argument('--reset', action='store_true',
                       help='Reset all data before generating (ensures coherent dataset)')
    parser.add_argument('--service', action='store_true',
                       help='Run in continuous service mode (generates data every 15 minutes)')
    parser.add_argument('--catchup', action='store_true',
                       help='Fill data gaps from last timestamp to present, then exit')
    parser.add_argument('--check-state', action='store_true',
                       help='Show current service state and exit')

    args = parser.parse_args()

    # Handle service mode
    if args.service:
        console.print("[bold blue]Starting Continuous Service Mode[/bold blue]")
        console.print("For production deployment, use: python src/service_main.py")
        console.print("Press Ctrl+C to stop\n")

        from service.continuous_generator import ContinuousDataService
        from service.scheduler import DataGenerationScheduler
        from service.health_server import HealthCheckServer
        import time

        try:
            db_config = load_config(args.db_config)
            building_config = load_config(args.building_config)

            # Initialize service
            service = ContinuousDataService(
                db_config,
                building_config,
                db_config['tables']['value_table']
            )

            # Startup
            if not service.startup():
                console.print("[red]Service startup failed[/red]")
                sys.exit(1)

            # Start health server
            health_port = 8080
            health_server = HealthCheckServer(port=health_port, health_callback=service.health_check)
            health_server.start()
            console.print(f"[green]Health check available at http://localhost:{health_port}/health[/green]")

            # Start scheduler
            interval_minutes = building_config['generation']['data_interval_minutes']
            scheduler = DataGenerationScheduler(interval_minutes=interval_minutes)
            scheduler.start(service.generate_current_interval)

            console.print("[bold green]Service running![/bold green]")

            # Keep running
            while not service.shutdown_requested:
                time.sleep(1)

            # Cleanup
            scheduler.stop()
            health_server.stop()
            service.shutdown()

        except KeyboardInterrupt:
            console.print("\n[yellow]Service stopped by user[/yellow]")
            sys.exit(0)

        return

    # Handle check-state mode
    if args.check_state:
        db_config = load_config(args.db_config)
        db = DatabaseConnection(db_config['database'])

        from service.state_manager import StateManager
        state_mgr = StateManager(db)

        console.print("\n[bold blue]Current Service State[/bold blue]")
        state = state_mgr.get_service_state()

        if state:
            console.print(f"Status: {state.get('status')}")
            console.print(f"Last Run: {state.get('last_run_timestamp')}")
            console.print(f"Updated: {state.get('updated_at')}")
            if state.get('error_message'):
                console.print(f"[red]Error: {state['error_message']}[/red]")

            totalizers = state.get('totalizers', {})
            if totalizers:
                console.print("\nTotalizer States:")
                console.print(f"  Electric Energy: {totalizers.get('electric_energy', 0):.1f} kWh")
                console.print(f"  Gas Volume: {totalizers.get('gas_volume', 0):.0f} ft³")
                console.print(f"  Water Volume: {totalizers.get('water_volume', 0):.0f} gal")
        else:
            console.print("[yellow]No service state found[/yellow]")

        db.close()
        return

    # Handle catchup mode
    if args.catchup:
        console.print("[bold blue]Gap Fill Mode[/bold blue]")
        db_config = load_config(args.db_config)
        building_config = load_config(args.building_config)

        db = DatabaseConnection(db_config['database'])

        from service.state_manager import StateManager
        from service.gap_filler import GapFiller
        from generators.entities import EntityGenerator

        state_mgr = StateManager(db)

        # Load or create entities
        data_loader = DataLoader(db, db_config['tables']['value_table'])
        entities_exist = data_loader.detect_entities_exist()

        if not entities_exist:
            console.print("[red]No entities found. Run with --entities-only first[/red]")
            sys.exit(1)

        # Load entity map
        query = """
            SELECT e.id, et_id.value_s as entity_name
            FROM core.entity e
            JOIN core.entity_tag et_id ON e.id = et_id.entity_id
            JOIN core.tag_def td_id ON et_id.tag_id = td_id.id
            WHERE td_id.name = 'id'
        """
        result = db.execute_query(query)
        entity_map = {row['entity_name']: row['id'] for row in result if row['entity_name']}

        # Calculate gap
        gap_start, gap_end, num_intervals = state_mgr.calculate_gap(db_config['tables']['value_table'])

        if num_intervals == 0:
            console.print("[green]No gaps detected - data is current[/green]")
            db.close()
            return

        console.print(f"Gap detected: {num_intervals} intervals from {gap_start} to {gap_end}")

        # Get totalizers
        totalizers = state_mgr.get_totalizer_states(db_config['tables']['value_table'])
        console.print(f"Resuming from totalizers: {totalizers}")

        # Fill gap
        gap_filler = GapFiller(db, building_config, entity_map, db_config['tables']['value_table'])
        success = gap_filler.fill_gap_incremental(gap_start, gap_end, totalizers)

        if success:
            console.print("[green]Gap filled successfully[/green]")
        else:
            console.print("[red]Gap fill failed[/red]")
            sys.exit(1)

        db.close()
        return

    # Continue with batch mode (original behavior)
    try:
        # Load configurations
        console.print("[bold green]Haystack Building Data Simulator[/bold green]")
        console.print(f"Loading configuration files...")
        
        db_config = load_config(args.db_config)
        building_config = load_config(args.building_config)
        
        # Setup database
        db, schema, data_loader = setup_database(db_config)
        
        # Reset data if requested
        if args.reset:
            console.print("[bold yellow]RESETTING ALL DATA[/bold yellow]")
            console.print("[yellow]This will delete all entities and time-series data![/yellow]")
            db.reset_all_data(
                value_table=db_config['tables']['value_table'],
                current_table=db_config['tables']['current_table']
            )
            console.print("[green]OK[/green] Data reset complete")
        
        # Generate entities
        entity_map = generate_building_entities(schema, building_config)
        
        if not args.entities_only:
            # Generate historical data
            generate_historical_data(data_loader, building_config, entity_map, args.days)
            
            # Generate current values
            generate_current_values(data_loader, building_config, entity_map)
        
        # Validation
        if not args.skip_validation:
            display_validation_results(db, db_config)
        
        console.print("\n[bold green]SUCCESS: Data generation completed successfully![/bold green]")
        
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