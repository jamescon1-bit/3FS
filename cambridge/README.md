# Cambridge NY Commercial AI Modules

AI-powered business automation tools for commercial landscaping and property management operations in Cambridge, NY and the greater NYC area.

## Module Overview

The Cambridge commercial AI system consists of four specialized modules designed to streamline business operations:

### 1. **Photo Organizer** (`photo_organizer.py`)
Advanced photo and media management system for project documentation and client communication.

**Key Features:**
- Intelligent photo categorization and tagging
- Project-based photo organization 
- Client gallery management
- Before/after photo comparisons
- Automatic metadata extraction and indexing
- Bulk photo processing and optimization
- Integration with project timelines

**Use Cases:**
- Document landscaping project progress
- Create client presentations and portfolios
- Organize seasonal maintenance records
- Build marketing materials from project photos

---

### 2. **Design Library** (`design_library.py`)
Comprehensive design asset management and project visualization system.

**Key Features:**
- Design template and asset library management
- Plant and material specification database
- 3D visualization and planning tools
- Seasonal design variations
- Client design approval workflows
- Cost estimation integration
- Vendor catalog management

**Use Cases:**
- Create professional landscape designs
- Manage plant and material libraries
- Generate client proposals with visualizations
- Track design trends and preferences

---

### 3. **Contract Vault** (`contract_vault.py`) 🔐
Secure contract and document storage system for commercial landscaping operations.

**Key Features:**
- **Document Storage & Retrieval**: Client contracts, insurance certificates (COIs), vendor agreements, permits
- **Metadata Tracking**: Document type, client, upload date, expiration date, status
- **Expiration Monitoring**: Flag documents expiring within 30/60/90 days
- **Renewal Reminders**: Automated alerts with urgency levels (Critical/High/Medium/Low)
- **Document Categories**: Contract, Insurance, Permit, Proposal, Invoice, Vendor Agreement, COI
- **Advanced Search**: Filter by client, type, date range, status, tags
- **Security Features**: File hashing, secure storage, audit trails

**Use Cases:**
- Manage commercial landscaping contracts
- Track insurance certificate renewals
- Monitor permit expiration dates
- Organize vendor agreements and documentation
- Generate compliance reports

**API Examples:**
```python
# Initialize vault
vault = ContractVault("client_documents")

# Store a contract
contract_id = vault.store_document(
    source_path="/path/to/contract.pdf",
    document_type=DocumentType.CONTRACT,
    client_name="Manhattan Office Complex",
    expiration_date=datetime(2025, 12, 31)
)

# Check expiring documents
expiring = vault.get_expiring_documents(days_ahead=30)
for doc, urgency in expiring:
    print(f"{doc.client_name}: {doc.filename} expires {doc.expiration_date} ({urgency.value})")

# Generate expiration report
report = vault.generate_expiration_report()
```

---

### 4. **Holiday Decor Planner** (`holiday_decor_planner.py`) 🎄
Complete holiday decoration project management system for commercial NYC installations.

**Key Features:**

**Project Lifecycle Management:**
- Requirements intake → Design selection → Material sourcing → Scheduling → Installation → Maintenance → Takedown
- Phase tracking with automated workflow progression

**Design Themes:**
- Classic Christmas, Winter Wonderland, Modern Minimalist
- Festive Corporate, Luxury Gold, Natural/Rustic, LED Modern

**Material Management:**
- Track lights, ornaments, garlands, wreaths, trees (real/artificial), ribbon, specialty items
- Inventory management with supplier integration
- Cost tracking and budget monitoring

**Installation Scheduling:**
- 2-4 person crew assignments
- 4-8 hour installation windows
- Multi-project coordination (20-50 concurrent projects Nov-Jan)
- Automatic takedown scheduling (Jan 2-15)

**Budget Tracking:**
- $5K-$100K+ project ranges for commercial installations
- Real-time cost monitoring and budget alerts
- Labor cost calculations with crew assignments

**Multi-Project Dashboard:**
- Handle 20-50 concurrent installations during peak season
- Crew utilization tracking
- Installation schedule optimization
- Revenue and profitability analysis

**Use Cases:**
- Manage holiday decorations for Manhattan office buildings
- Coordinate multiple commercial property installations
- Track seasonal workforce and equipment needs
- Generate client proposals and project timelines

**API Examples:**
```python
# Initialize planner
planner = HolidayDecorPlanner("holiday_projects.db")

# Create new project
project_id = planner.create_project(
    client_name="Manhattan Office Building LLC",
    client_contact="John Smith (555-0123)",
    site_address="123 Madison Ave, New York, NY 10016",
    project_name="Corporate Holiday Display 2024",
    design_theme=DesignTheme.FESTIVE_CORPORATE,
    budget_min=Decimal('15000.00'),
    budget_max=Decimal('25000.00')
)

# Add materials
lights = Material(
    id="MAT_001", 
    name="LED Commercial String Lights",
    material_type=MaterialType.LIGHTS,
    quantity=50, 
    unit_cost=Decimal('45.00')
)
planner.add_material_to_project(project_id, lights)

# Assign crew
crew = CrewAssignment(
    crew_id="CREW_A",
    crew_leader="Mike Johnson", 
    crew_members=["Tom Wilson", "Sarah Davis", "Chris Brown"],
    size=CrewSize.LARGE,
    hourly_rate=Decimal('35.00')
)
planner.assign_crew(project_id, crew)

# Schedule installation
planner.schedule_installation(
    project_id, 
    install_date=date(2024, 11, 25),
    duration=InstallDuration.LONG
)

# Get dashboard overview
dashboard = planner.get_dashboard_summary()
print(f"Active Projects: {dashboard['total_active_projects']}")
print(f"This Week Installations: {dashboard['installations_this_week']}")
print(f"Total Revenue: ${dashboard['total_revenue']}")
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- SQLite3
- Required packages: `sqlite3`, `pathlib`, `dataclasses`, `enum`, `logging`, `decimal`

### Quick Start
```bash
# Navigate to module directory
cd /path/to/cambridge/

# Test individual modules
python3 photo_organizer.py
python3 design_library.py
python3 contract_vault.py
python3 holiday_decor_planner.py
```

### Database Initialization
Each module automatically creates its required database tables on first run:
- `photo_organizer.py` → `photos.db`
- `design_library.py` → `designs.db`
- `contract_vault.py` → `vault.db`
- `holiday_decor_planner.py` → `holiday_decor.db`

## Integration Points

**Cross-Module Workflows:**
- **Project Photos**: Photo Organizer integrates with Holiday Decor project IDs
- **Design Assets**: Design Library provides templates for Holiday Decor themes
- **Contract Management**: Contract Vault stores agreements for all client projects
- **Documentation**: All modules support project-based documentation and reporting

**External Integrations:**
- **Accounting Software**: Export project costs and invoicing data
- **CRM Systems**: Client contact and project history integration
- **Calendar Systems**: Installation scheduling and crew management
- **File Storage**: Secure document storage with backup capabilities

## Business Benefits

### Operational Efficiency
- **Automated Workflows**: Reduce manual data entry and task management
- **Centralized Documentation**: All project materials in one accessible system
- **Compliance Management**: Automated expiration tracking and renewal alerts
- **Resource Optimization**: Crew scheduling and material inventory management

### Client Experience
- **Professional Proposals**: Integrated design, timeline, and cost presentation
- **Progress Transparency**: Photo documentation and project phase tracking
- **Timely Communication**: Automated updates and milestone notifications
- **Quality Assurance**: Documented processes and completion verification

### Revenue Growth
- **Project Scalability**: Manage 20-50+ concurrent holiday installations
- **Cost Control**: Real-time budget tracking and profitability analysis
- **Upselling Opportunities**: Integrated design and service recommendations
- **Client Retention**: Professional service delivery and documentation

## Support & Development

### Module Architecture
Each module follows a consistent design pattern:
- **Data Models**: Dataclasses for type-safe data structures
- **Database Layer**: SQLite with proper indexing and relationships  
- **Business Logic**: Core functionality with error handling
- **API Interface**: Clean programmatic access to all features

### Extensibility
- **Plugin Architecture**: Easy addition of new features and integrations
- **Configuration Management**: Customizable settings per deployment
- **Reporting Framework**: Extensible report generation and export
- **API Access**: RESTful endpoints for external system integration

### Maintenance
- **Automated Backups**: Database and file storage backup procedures
- **Health Monitoring**: System status and performance tracking
- **Update Management**: Version control and deployment procedures
- **Documentation**: Comprehensive API docs and user guides

---

**Cambridge NY Commercial AI Modules** - Empowering commercial landscaping operations with intelligent automation and professional project management.