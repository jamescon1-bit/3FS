"""
Cambridge NY Contract Vault System
Secure contract and document storage system for commercial landscaping operations.

Features:
- Store/retrieve contracts, insurance certs, vendor agreements, permits
- Track expiration dates with renewal reminders
- Document metadata and version tracking
- Search and reporting capabilities
- Automated expiration alerts (30/60/90 day windows)
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
import json
import hashlib
import os
from pathlib import Path


class DocumentType(Enum):
    CONTRACT = "contract"
    INSURANCE_CERTIFICATE = "insurance_certificate"
    VENDOR_AGREEMENT = "vendor_agreement"
    PERMIT = "permit"
    LICENSE = "license"
    BOND = "bond"
    LEASE = "lease"
    SERVICE_AGREEMENT = "service_agreement"
    MAINTENANCE_CONTRACT = "maintenance_contract"
    SAFETY_CERTIFICATION = "safety_certification"


class DocumentStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"
    PENDING_RENEWAL = "pending_renewal"
    ARCHIVED = "archived"
    DRAFT = "draft"


class AlertType(Enum):
    EXPIRATION_90_DAY = "expiration_90_day"
    EXPIRATION_60_DAY = "expiration_60_day"
    EXPIRATION_30_DAY = "expiration_30_day"
    EXPIRATION_7_DAY = "expiration_7_day"
    EXPIRED = "expired"


@dataclass
class ExpirationAlert:
    """Alert for upcoming document expirations"""
    document_id: str
    alert_type: AlertType
    alert_date: date
    document_name: str
    client_name: str
    expiration_date: date
    days_until_expiration: int
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_date: Optional[datetime] = None


@dataclass
class DocumentVersion:
    """Version tracking for document amendments"""
    version_number: int
    created_date: datetime
    created_by: str
    file_path: str
    file_hash: str
    change_notes: Optional[str] = None
    file_size: int = 0


@dataclass
class Document:
    """Core document storage and metadata"""
    document_id: str
    name: str
    document_type: DocumentType
    client_name: str
    effective_date: date
    expiration_date: Optional[date]
    value: Optional[float]  # Contract value, bond amount, etc.
    status: DocumentStatus
    created_date: datetime
    created_by: str
    versions: List[DocumentVersion] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    renewal_contact: Optional[str] = None
    renewal_phone: Optional[str] = None
    renewal_email: Optional[str] = None
    auto_renew: bool = False
    
    def get_current_version(self) -> Optional[DocumentVersion]:
        """Get the latest version of the document"""
        return max(self.versions, key=lambda v: v.version_number) if self.versions else None
    
    def days_until_expiration(self) -> Optional[int]:
        """Calculate days until expiration"""
        if not self.expiration_date:
            return None
        delta = self.expiration_date - date.today()
        return delta.days
    
    def update_status(self):
        """Update document status based on expiration date"""
        if not self.expiration_date:
            return
        
        days_left = self.days_until_expiration()
        if days_left is None:
            return
        
        if days_left < 0:
            self.status = DocumentStatus.EXPIRED
        elif days_left <= 30:
            self.status = DocumentStatus.EXPIRING_SOON
        else:
            self.status = DocumentStatus.ACTIVE


class ContractVault:
    """Secure document storage and management system"""
    
    def __init__(self, vault_directory: str = "./contract_vault"):
        self.vault_directory = Path(vault_directory)
        self.vault_directory.mkdir(exist_ok=True, parents=True)
        
        # Storage paths
        self.documents_db = self.vault_directory / "documents.json"
        self.alerts_db = self.vault_directory / "alerts.json"
        self.files_directory = self.vault_directory / "files"
        self.files_directory.mkdir(exist_ok=True)
        
        # Load existing data
        self.documents: Dict[str, Document] = self._load_documents()
        self.alerts: List[ExpirationAlert] = self._load_alerts()
        
        # Update all document statuses on startup
        self._update_all_statuses()
    
    def _generate_document_id(self, name: str, client_name: str) -> str:
        """Generate unique document ID"""
        timestamp = datetime.now().isoformat()
        source = f"{name}_{client_name}_{timestamp}"
        return hashlib.md5(source.encode()).hexdigest()[:12].upper()
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for version tracking"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _load_documents(self) -> Dict[str, Document]:
        """Load documents from JSON storage"""
        if not self.documents_db.exists():
            return {}
        
        try:
            with open(self.documents_db, 'r') as f:
                data = json.load(f)
                documents = {}
                for doc_id, doc_data in data.items():
                    # Convert dates and enums
                    doc_data['effective_date'] = date.fromisoformat(doc_data['effective_date'])
                    if doc_data.get('expiration_date'):
                        doc_data['expiration_date'] = date.fromisoformat(doc_data['expiration_date'])
                    doc_data['created_date'] = datetime.fromisoformat(doc_data['created_date'])
                    doc_data['document_type'] = DocumentType(doc_data['document_type'])
                    doc_data['status'] = DocumentStatus(doc_data['status'])
                    
                    # Convert versions
                    versions = []
                    for version_data in doc_data.get('versions', []):
                        version_data['created_date'] = datetime.fromisoformat(version_data['created_date'])
                        versions.append(DocumentVersion(**version_data))
                    doc_data['versions'] = versions
                    
                    documents[doc_id] = Document(**doc_data)
                return documents
        except Exception as e:
            print(f"Error loading documents: {e}")
            return {}
    
    def _save_documents(self):
        """Save documents to JSON storage"""
        try:
            data = {}
            for doc_id, document in self.documents.items():
                doc_dict = {
                    'document_id': document.document_id,
                    'name': document.name,
                    'document_type': document.document_type.value,
                    'client_name': document.client_name,
                    'effective_date': document.effective_date.isoformat(),
                    'expiration_date': document.expiration_date.isoformat() if document.expiration_date else None,
                    'value': document.value,
                    'status': document.status.value,
                    'created_date': document.created_date.isoformat(),
                    'created_by': document.created_by,
                    'tags': document.tags,
                    'notes': document.notes,
                    'renewal_contact': document.renewal_contact,
                    'renewal_phone': document.renewal_phone,
                    'renewal_email': document.renewal_email,
                    'auto_renew': document.auto_renew,
                    'versions': []
                }
                
                for version in document.versions:
                    doc_dict['versions'].append({
                        'version_number': version.version_number,
                        'created_date': version.created_date.isoformat(),
                        'created_by': version.created_by,
                        'file_path': version.file_path,
                        'file_hash': version.file_hash,
                        'change_notes': version.change_notes,
                        'file_size': version.file_size
                    })
                
                data[doc_id] = doc_dict
            
            with open(self.documents_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving documents: {e}")
    
    def _load_alerts(self) -> List[ExpirationAlert]:
        """Load alerts from JSON storage"""
        if not self.alerts_db.exists():
            return []
        
        try:
            with open(self.alerts_db, 'r') as f:
                data = json.load(f)
                alerts = []
                for alert_data in data:
                    alert_data['alert_type'] = AlertType(alert_data['alert_type'])
                    alert_data['alert_date'] = date.fromisoformat(alert_data['alert_date'])
                    alert_data['expiration_date'] = date.fromisoformat(alert_data['expiration_date'])
                    if alert_data.get('acknowledged_date'):
                        alert_data['acknowledged_date'] = datetime.fromisoformat(alert_data['acknowledged_date'])
                    alerts.append(ExpirationAlert(**alert_data))
                return alerts
        except Exception as e:
            print(f"Error loading alerts: {e}")
            return []
    
    def _save_alerts(self):
        """Save alerts to JSON storage"""
        try:
            data = []
            for alert in self.alerts:
                alert_dict = {
                    'document_id': alert.document_id,
                    'alert_type': alert.alert_type.value,
                    'alert_date': alert.alert_date.isoformat(),
                    'document_name': alert.document_name,
                    'client_name': alert.client_name,
                    'expiration_date': alert.expiration_date.isoformat(),
                    'days_until_expiration': alert.days_until_expiration,
                    'is_acknowledged': alert.is_acknowledged,
                    'acknowledged_by': alert.acknowledged_by,
                    'acknowledged_date': alert.acknowledged_date.isoformat() if alert.acknowledged_date else None
                }
                data.append(alert_dict)
            
            with open(self.alerts_db, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving alerts: {e}")
    
    def _update_all_statuses(self):
        """Update status for all documents"""
        for document in self.documents.values():
            document.update_status()
        self._save_documents()
    
    def store_document(self,
                      name: str,
                      document_type: DocumentType,
                      client_name: str,
                      effective_date: date,
                      file_path: Optional[str] = None,
                      expiration_date: Optional[date] = None,
                      value: Optional[float] = None,
                      created_by: str = "system",
                      tags: List[str] = None,
                      notes: str = None,
                      renewal_contact: str = None,
                      renewal_phone: str = None,
                      renewal_email: str = None,
                      auto_renew: bool = False) -> str:
        """Store a new document in the vault"""
        
        document_id = self._generate_document_id(name, client_name)
        
        # Determine status
        status = DocumentStatus.ACTIVE
        if expiration_date:
            days_left = (expiration_date - date.today()).days
            if days_left < 0:
                status = DocumentStatus.EXPIRED
            elif days_left <= 30:
                status = DocumentStatus.EXPIRING_SOON
        
        document = Document(
            document_id=document_id,
            name=name,
            document_type=document_type,
            client_name=client_name,
            effective_date=effective_date,
            expiration_date=expiration_date,
            value=value,
            status=status,
            created_date=datetime.now(),
            created_by=created_by,
            tags=tags or [],
            notes=notes,
            renewal_contact=renewal_contact,
            renewal_phone=renewal_phone,
            renewal_email=renewal_email,
            auto_renew=auto_renew
        )
        
        # Handle file storage if provided
        if file_path and os.path.exists(file_path):
            stored_file_path = self._store_file(file_path, document_id, 1)
            file_hash = self._calculate_file_hash(file_path)
            file_size = os.path.getsize(file_path)
            
            version = DocumentVersion(
                version_number=1,
                created_date=datetime.now(),
                created_by=created_by,
                file_path=stored_file_path,
                file_hash=file_hash,
                file_size=file_size,
                change_notes="Initial version"
            )
            document.versions.append(version)
        
        self.documents[document_id] = document
        self._save_documents()
        
        # Generate expiration alerts if applicable
        if expiration_date:
            self._generate_expiration_alerts(document)
        
        return document_id
    
    def _store_file(self, source_path: str, document_id: str, version: int) -> str:
        """Store physical file in vault directory"""
        file_extension = Path(source_path).suffix
        stored_filename = f"{document_id}_v{version}{file_extension}"
        stored_path = self.files_directory / stored_filename
        
        # Copy file to vault
        import shutil
        shutil.copy2(source_path, stored_path)
        
        return str(stored_path)
    
    def add_document_version(self,
                           document_id: str,
                           file_path: str,
                           created_by: str,
                           change_notes: str = None) -> bool:
        """Add a new version to an existing document"""
        if document_id not in self.documents:
            return False
        
        document = self.documents[document_id]
        current_version = document.get_current_version()
        new_version_number = (current_version.version_number + 1) if current_version else 1
        
        # Store the new file
        stored_file_path = self._store_file(file_path, document_id, new_version_number)
        file_hash = self._calculate_file_hash(file_path)
        file_size = os.path.getsize(file_path)
        
        version = DocumentVersion(
            version_number=new_version_number,
            created_date=datetime.now(),
            created_by=created_by,
            file_path=stored_file_path,
            file_hash=file_hash,
            file_size=file_size,
            change_notes=change_notes
        )
        
        document.versions.append(version)
        self._save_documents()
        return True
    
    def search_documents(self,
                        client_name: str = None,
                        document_type: DocumentType = None,
                        status: DocumentStatus = None,
                        expiring_within_days: int = None,
                        tags: List[str] = None) -> List[Document]:
        """Search documents by various criteria"""
        results = []
        
        for document in self.documents.values():
            # Apply filters
            if client_name and client_name.lower() not in document.client_name.lower():
                continue
            
            if document_type and document.document_type != document_type:
                continue
            
            if status and document.status != status:
                continue
            
            if expiring_within_days is not None and document.expiration_date:
                days_left = document.days_until_expiration()
                if days_left is None or days_left > expiring_within_days:
                    continue
            
            if tags:
                if not any(tag in document.tags for tag in tags):
                    continue
            
            results.append(document)
        
        return results
    
    def _generate_expiration_alerts(self, document: Document):
        """Generate expiration alerts for a document"""
        if not document.expiration_date:
            return
        
        today = date.today()
        alert_dates = [
            (document.expiration_date - timedelta(days=90), AlertType.EXPIRATION_90_DAY),
            (document.expiration_date - timedelta(days=60), AlertType.EXPIRATION_60_DAY),
            (document.expiration_date - timedelta(days=30), AlertType.EXPIRATION_30_DAY),
            (document.expiration_date - timedelta(days=7), AlertType.EXPIRATION_7_DAY),
        ]
        
        for alert_date, alert_type in alert_dates:
            if alert_date >= today:  # Only future alerts
                days_until = (document.expiration_date - alert_date).days
                
                alert = ExpirationAlert(
                    document_id=document.document_id,
                    alert_type=alert_type,
                    alert_date=alert_date,
                    document_name=document.name,
                    client_name=document.client_name,
                    expiration_date=document.expiration_date,
                    days_until_expiration=days_until
                )
                self.alerts.append(alert)
        
        self._save_alerts()
    
    def get_pending_alerts(self, days_ahead: int = 7) -> List[ExpirationAlert]:
        """Get alerts that are due within the specified number of days"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        pending = [
            alert for alert in self.alerts
            if not alert.is_acknowledged and alert.alert_date <= cutoff_date
        ]
        
        return sorted(pending, key=lambda a: a.alert_date)
    
    def acknowledge_alert(self, alert: ExpirationAlert, acknowledged_by: str):
        """Mark an alert as acknowledged"""
        alert.is_acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_date = datetime.now()
        self._save_alerts()
    
    def generate_expiring_report(self, days_ahead: int = 90) -> str:
        """Generate a report of expiring documents"""
        expiring_docs = self.search_documents(expiring_within_days=days_ahead)
        expiring_docs.sort(key=lambda d: d.expiration_date or date.max)
        
        output = []
        output.append("CAMBRIDGE NY CONTRACT VAULT - EXPIRING DOCUMENTS REPORT")
        output.append("=" * 60)
        output.append(f"Documents expiring within {days_ahead} days")
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        output.append("")
        
        if not expiring_docs:
            output.append("No documents expiring within the specified timeframe.")
            return "\n".join(output)
        
        # Group by urgency
        urgent = [d for d in expiring_docs if d.days_until_expiration() and d.days_until_expiration() <= 30]
        soon = [d for d in expiring_docs if d.days_until_expiration() and 30 < d.days_until_expiration() <= 60]
        later = [d for d in expiring_docs if d.days_until_expiration() and d.days_until_expiration() > 60]
        
        if urgent:
            output.append("🚨 URGENT (30 days or less):")
            for doc in urgent:
                days = doc.days_until_expiration()
                output.append(f"  • {doc.name} ({doc.client_name})")
                output.append(f"    Expires: {doc.expiration_date} ({days} days)")
                output.append(f"    Type: {doc.document_type.value.replace('_', ' ').title()}")
                if doc.renewal_email:
                    output.append(f"    Contact: {doc.renewal_email}")
                output.append("")
        
        if soon:
            output.append("⚠️ SOON (31-60 days):")
            for doc in soon:
                days = doc.days_until_expiration()
                output.append(f"  • {doc.name} ({doc.client_name}) - {days} days")
                output.append(f"    Type: {doc.document_type.value.replace('_', ' ').title()}")
                output.append("")
        
        if later:
            output.append("📅 UPCOMING (61+ days):")
            for doc in later:
                days = doc.days_until_expiration()
                output.append(f"  • {doc.name} ({doc.client_name}) - {days} days")
                output.append("")
        
        return "\n".join(output)


# Example Usage
if __name__ == "__main__":
    # Initialize the contract vault
    vault = ContractVault("./cambridge_contracts")
    
    print("=== Cambridge NY Contract Vault Examples ===\n")
    
    # Example 1: Store insurance certificate
    print("1. STORING INSURANCE CERTIFICATE")
    print("-" * 40)
    
    insurance_id = vault.store_document(
        name="General Liability Insurance",
        document_type=DocumentType.INSURANCE_CERTIFICATE,
        client_name="Cambridge Landscaping Inc",
        effective_date=date(2024, 1, 1),
        expiration_date=date(2024, 12, 31),
        value=2000000.0,  # $2M coverage
        created_by="admin",
        tags=["liability", "commercial", "required"],
        notes="Required for all commercial contracts in NYC",
        renewal_contact="State Farm Agent",
        renewal_email="agent@statefarm.com",
        auto_renew=True
    )
    
    print(f"Stored insurance certificate with ID: {insurance_id}")
    
    # Example 2: Store vendor agreement
    print("\n2. STORING VENDOR AGREEMENT")
    print("-" * 40)
    
    vendor_id = vault.store_document(
        name="Plant Supplier Agreement - NYC Wholesale",
        document_type=DocumentType.VENDOR_AGREEMENT,
        client_name="NYC Botanical Supplies",
        effective_date=date(2024, 3, 1),
        expiration_date=date(2025, 2, 28),
        value=150000.0,  # Annual volume commitment
        created_by="procurement",
        tags=["vendor", "plants", "wholesale", "nyc"],
        notes="Exclusive supplier for commercial plant installations",
        renewal_contact="John Smith",
        renewal_phone="212-555-0123",
        renewal_email="j.smith@nycbotanical.com"
    )
    
    print(f"Stored vendor agreement with ID: {vendor_id}")
    
    # Example 3: Store permit
    print("\n3. STORING CITY PERMIT")
    print("-" * 40)
    
    permit_id = vault.store_document(
        name="NYC Tree Work Permit - Zone 3",
        document_type=DocumentType.PERMIT,
        client_name="NYC Parks Department",
        effective_date=date(2024, 6, 1),
        expiration_date=date(2024, 11, 30),
        created_by="permits_team",
        tags=["permit", "nyc", "trees", "seasonal"],
        notes="Required for tree maintenance in Central Park area",
        renewal_contact="NYC Parks Permits Office",
        renewal_phone="311"
    )
    
    print(f"Stored permit with ID: {permit_id}")
    
    # Example 4: Search expiring documents
    print("\n4. SEARCHING EXPIRING DOCUMENTS")
    print("-" * 40)
    
    expiring_docs = vault.search_documents(expiring_within_days=365)
    print(f"Found {len(expiring_docs)} documents expiring within 365 days:")
    
    for doc in expiring_docs:
        days_left = doc.days_until_expiration()
        print(f"  • {doc.name} ({doc.client_name}) - {days_left} days left")
    
    # Example 5: Generate expiring report
    print("\n5. EXPIRING DOCUMENTS REPORT")
    print("-" * 40)
    
    report = vault.generate_expiring_report(days_ahead=300)
    print(report)
    
    # Example 6: Check pending alerts
    print("\n6. PENDING EXPIRATION ALERTS")
    print("-" * 40)
    
    alerts = vault.get_pending_alerts(days_ahead=180)
    print(f"Found {len(alerts)} pending alerts:")
    
    for alert in alerts:
        print(f"  • {alert.alert_type.value.replace('_', ' ').title()}")
        print(f"    Document: {alert.document_name} ({alert.client_name})")
        print(f"    Alert Date: {alert.alert_date}")
        print(f"    Days Until Expiration: {alert.days_until_expiration}")
        print("")