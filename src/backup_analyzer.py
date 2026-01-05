"""
UniFi Backup Analyzer - processes backup data and generates documentation
"""
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

from .config import Config
from .ai_integration import AIManager
from .utils import log_execution_time

logger = logging.getLogger('unifi_documenter')

class UniFiBackupAnalyzer:
    """Analyzes UniFi backup data and generates documentation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.ai_manager = AIManager(config)
        
    @log_execution_time
    def analyze_backup_data(self, backup_result: Dict) -> Optional[Dict]:
        """Analyze processed backup data and generate documentation"""
        if not self.ai_manager.is_available():
            logger.error("AI manager not available for analysis")
            return None
        
        try:
            output_folder = backup_result['output_folder']
            document_files = backup_result['document_files']
            timestamp = backup_result['timestamp']
            
            # Create analysis output directory
            analysis_dir = os.path.join(output_folder, 'analysis')
            os.makedirs(analysis_dir, exist_ok=True)
            
            # Group documents by type for intelligent batch processing
            analyzed_documents = []
            
            logger.info(f"Starting analysis of {len(document_files)} documents using batch processing")
            grouped_documents = self._group_documents_by_type(document_files)
            
            logger.info(f"Grouped documents into {len(grouped_documents)} categories: {', '.join(grouped_documents.keys())}")
            
            # Process each group in batches
            for doc_type, files in grouped_documents.items():
                logger.info(f"Processing {len(files)} {doc_type} documents in batches of {self.config.BATCH_SIZE}")
                
                # Process in batches
                for i in range(0, len(files), self.config.BATCH_SIZE):
                    batch_files = files[i:i+self.config.BATCH_SIZE]
                    batch_num = (i // self.config.BATCH_SIZE) + 1
                    total_batches = (len(files) + self.config.BATCH_SIZE - 1) // self.config.BATCH_SIZE
                    
                    logger.info(f"Processing {doc_type} batch {batch_num}/{total_batches} ({len(batch_files)} documents)")
                    
                    batch_results = self._process_batch(doc_type, batch_files, analysis_dir)
                    analyzed_documents.extend(batch_results)
            
            # Generate summary analysis
            summary = self._generate_summary_analysis(analyzed_documents, analysis_dir)
            
            # Create master index
            index = self._create_documentation_index(analyzed_documents, summary, analysis_dir)
            
            result = {
                'analysis_dir': analysis_dir,
                'analyzed_documents': analyzed_documents,
                'summary': summary,
                'index_file': index,
                'timestamp': timestamp,
                'total_documents': len(analyzed_documents)
            }
            
            logger.info(f"Analysis completed successfully. Generated documentation for {len(analyzed_documents)} documents")
            return result
            
        except Exception as e:
            logger.error(f"Backup analysis failed: {str(e)}")
            return None
    
    def _analyze_single_document(self, doc_file: str, output_dir: str) -> Optional[Dict]:
        """Analyze a single JSON document"""
        try:
            with open(doc_file, 'r') as f:
                data = json.load(f)
            
            # Skip empty or invalid documents
            if not data or not isinstance(data, dict):
                logger.warning(f"Skipping invalid document: {doc_file}")
                return None
            
            # Create a hash for the document to identify it
            doc_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:8]
            doc_name = f"doc_{doc_hash}"
            
            # Analyze configuration type
            config_type = self.ai_manager.analyze_configuration_type(data)
            
            # Generate documentation
            context = f"UniFi {config_type} Configuration"
            documentation = self.ai_manager.generate_documentation(data, context)
            
            if not documentation:
                logger.warning(f"Failed to generate documentation for {doc_file}")
                return None
            
            # Save documentation
            doc_filename = f"{doc_name}.md"
            doc_path = os.path.join(output_dir, doc_filename)
            
            # Create enhanced markdown with metadata
            enhanced_doc = self._create_enhanced_markdown(
                documentation, data, config_type, doc_hash, doc_file
            )
            
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_doc)
            
            # Save raw JSON if configured
            if self.config.INCLUDE_RAW_DATA:
                json_filename = f"{doc_name}.json"
                json_path = os.path.join(output_dir, json_filename)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            
            return {
                'document_id': doc_hash,
                'original_file': doc_file,
                'markdown_file': doc_path,
                'json_file': json_path if self.config.INCLUDE_RAW_DATA else None,
                'config_type': config_type,
                'data_keys': list(data.keys()) if isinstance(data, dict) else [],
                'file_size': os.path.getsize(doc_path),
                'character_count': len(enhanced_doc)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze document {doc_file}: {str(e)}")
            return None
    
    def _group_documents_by_type(self, files: List[str]) -> Dict[str, List[str]]:
        """Group documents by type for better context and batch processing."""
        groups = {
            'devices': [],
            'networks': [],
            'settings': [],
            'users': [],
            'firewall': [],
            'wireless': [],
            'ports': [],
            'other': []
        }
        
        for file in files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                
                if not isinstance(data, dict):
                    groups['other'].append(file)
                    continue
                
                # Determine type from content structure
                filename = os.path.basename(file).lower()
                keys = set(data.keys())
                
                # Device identification
                if 'mac' in keys and ('ip' in keys or 'model' in keys or 'type' in keys):
                    groups['devices'].append(file)
                # Network/VLAN identification
                elif any(k in keys for k in ['vlan', 'network_group', 'subnet', 'dhcp', 'gateway']):
                    groups['networks'].append(file)
                # Firewall rules
                elif any(k in keys for k in ['rule_index', 'src_address', 'dst_address', 'action']):
                    groups['firewall'].append(file)
                # Wireless/SSID
                elif any(k in keys for k in ['ssid', 'wpa', 'security', 'wlan']):
                    groups['wireless'].append(file)
                # Port configuration
                elif any(k in keys for k in ['port_idx', 'port_conf_id', 'portconf']):
                    groups['ports'].append(file)
                # User/client data
                elif any(k in keys for k in ['username', 'user_id', 'hostname', 'noted']):
                    groups['users'].append(file)
                # Settings
                elif 'setting' in filename or any(k in keys for k in ['key', 'site_id', 'enabled']):
                    groups['settings'].append(file)
                else:
                    groups['other'].append(file)
                    
            except Exception as e:
                logger.warning(f"Failed to classify document {file}: {str(e)}")
                groups['other'].append(file)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}
    
    def _process_batch(self, doc_type: str, files: List[str], output_dir: str) -> List[Dict]:
        """Process a batch of related documents together for better context."""
        try:
            # Load all files in batch
            documents = []
            file_metadata = []
            
            for file in files:
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                    documents.append(data)
                    file_metadata.append({
                        'file': file,
                        'data': data
                    })
                except Exception as e:
                    logger.warning(f"Failed to load {file}: {str(e)}")
            
            if not documents:
                return []
            
            # Create combined prompt for batch
            batch_data = {
                'type': doc_type,
                'count': len(documents),
                'documents': documents
            }
            
            context = f"UniFi {doc_type.title()} Configuration Batch ({len(documents)} items)"
            batch_documentation = self.ai_manager.generate_documentation(batch_data, context)
            
            if not batch_documentation:
                logger.warning(f"Failed to generate batch documentation for {doc_type}")
                return []
            
            # Save batch documentation
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            batch_filename = f"batch_{doc_type}_{timestamp}.md"
            batch_path = os.path.join(output_dir, batch_filename)
            
            # Create enhanced markdown
            batch_content = f"""# UniFi {doc_type.title()} Configuration Batch

**Generated:** {datetime.now().isoformat()}  
**Document Count:** {len(documents)}  
**Configuration Type:** {doc_type.title()}  

---

{batch_documentation}

---

## Batch Metadata

- **Processed Files**: {len(files)}
- **Document Type**: {doc_type}
- **Batch Generated**: {datetime.now().isoformat()}

### Files in This Batch

"""
            for i, file in enumerate(files, 1):
                batch_content += f"{i}. `{os.path.basename(file)}`\n"
            
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            # Return analysis results for each document
            results = []
            for metadata in file_metadata:
                doc_hash = hashlib.md5(json.dumps(metadata['data'], sort_keys=True).encode()).hexdigest()[:8]
                results.append({
                    'document_id': doc_hash,
                    'original_file': metadata['file'],
                    'markdown_file': batch_path,  # All documents share the batch file
                    'json_file': None,
                    'config_type': doc_type,
                    'data_keys': list(metadata['data'].keys()) if isinstance(metadata['data'], dict) else [],
                    'file_size': os.path.getsize(batch_path) // len(files),  # Approximate per-doc size
                    'character_count': len(batch_content) // len(files),
                    'processed_as_batch': True
                })
            
            logger.info(f"Successfully processed batch of {len(results)} {doc_type} documents")
            return results
            
        except Exception as e:
            logger.error(f"Failed to process batch for {doc_type}: {str(e)}")
            return []
    
    def _create_enhanced_markdown(self, documentation: str, data: Dict, 
                                 config_type: str, doc_hash: str, original_file: str) -> str:
        """Create enhanced markdown with metadata and structure"""
        timestamp = datetime.now().isoformat()
        
        metadata = f"""---
document_id: {doc_hash}
config_type: {config_type}
generated_at: {timestamp}
original_file: {os.path.basename(original_file)}
data_keys: {', '.join(data.keys()) if isinstance(data, dict) else 'N/A'}
---

"""
        
        # Add document header
        header = f"""# UniFi {config_type} Configuration

**Document ID:** `{doc_hash}`  
**Generated:** {timestamp}  
**Configuration Type:** {config_type}  

---

"""
        
        # Clean up and structure the documentation
        cleaned_doc = documentation.strip()
        
        # Add footer with metadata
        footer = f"""

---

## Document Metadata

- **Document ID**: `{doc_hash}`
- **Configuration Type**: {config_type}
- **Original File**: `{os.path.basename(original_file)}`
- **Data Keys**: {', '.join(data.keys()) if isinstance(data, dict) else 'N/A'}
- **Generated**: {timestamp}
- **Source**: UniFi Backup Analysis System

"""
        
        return metadata + header + cleaned_doc + footer
    
    def _generate_summary_analysis(self, analyzed_documents: List[Dict], output_dir: str) -> Optional[str]:
        """Generate a summary analysis of all documents"""
        if not analyzed_documents:
            return None
        
        try:
            # Collect summary information
            config_types = {}
            total_docs = len(analyzed_documents)
            total_size = sum(doc['file_size'] for doc in analyzed_documents)
            
            for doc in analyzed_documents:
                config_type = doc['config_type']
                config_types[config_type] = config_types.get(config_type, 0) + 1
            
            # Create summary data for AI analysis
            summary_data = {
                'total_documents': total_docs,
                'total_size_bytes': total_size,
                'configuration_types': config_types,
                'document_list': [
                    {
                        'id': doc['document_id'],
                        'type': doc['config_type'],
                        'keys': doc['data_keys']
                    }
                    for doc in analyzed_documents
                ]
            }
            
            # Generate AI summary
            context = "UniFi Backup Summary Analysis"
            summary_documentation = self.ai_manager.generate_documentation(summary_data, context)
            
            if summary_documentation:
                # Create enhanced summary
                timestamp = datetime.now().isoformat()
                
                summary_content = f"""# UniFi Backup Analysis Summary

**Generated:** {timestamp}  
**Total Documents:** {total_docs}  
**Total Size:** {total_size:,} bytes  

## Configuration Overview

{summary_documentation}

## Document Statistics

| Configuration Type | Count |
|-------------------|-------|
"""
                
                for config_type, count in sorted(config_types.items()):
                    summary_content += f"| {config_type} | {count} |\n"
                
                summary_content += f"""

## Document Inventory

| Document ID | Configuration Type | Data Keys |
|------------|-------------------|-----------|
"""
                
                for doc in analyzed_documents:
                    keys_str = ', '.join(doc['data_keys'][:5])  # Limit to first 5 keys
                    if len(doc['data_keys']) > 5:
                        keys_str += '...'
                    summary_content += f"| `{doc['document_id']}` | {doc['config_type']} | {keys_str} |\n"
                
                # Save summary
                summary_path = os.path.join(output_dir, 'SUMMARY.md')
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(summary_content)
                
                logger.info(f"Summary analysis saved to {summary_path}")
                return summary_path
            
        except Exception as e:
            logger.error(f"Failed to generate summary analysis: {str(e)}")
        
        return None
    
    def _create_documentation_index(self, analyzed_documents: List[Dict], 
                                  summary_file: Optional[str], output_dir: str) -> str:
        """Create a master index of all documentation"""
        timestamp = datetime.now().isoformat()
        
        index_content = f"""# UniFi Configuration Documentation Index

**Generated:** {timestamp}  
**Total Documents:** {len(analyzed_documents)}  

This index provides access to all analyzed UniFi configuration documentation generated from backup data.

## Quick Navigation

"""
        
        if summary_file:
            index_content += "- [📊 **Summary Analysis**](SUMMARY.md) - Overview of all configurations\n"
        
        # Group by configuration type
        config_groups = {}
        for doc in analyzed_documents:
            config_type = doc['config_type']
            if config_type not in config_groups:
                config_groups[config_type] = []
            config_groups[config_type].append(doc)
        
        # Add navigation by type
        for config_type in sorted(config_groups.keys()):
            index_content += f"- [📋 {config_type}](#{config_type.lower().replace(' ', '-')}-configurations)\n"
        
        index_content += "\n---\n\n"
        
        # Add detailed sections for each configuration type
        for config_type in sorted(config_groups.keys()):
            docs = config_groups[config_type]
            index_content += f"## {config_type} Configurations\n\n"
            
            for doc in docs:
                filename = os.path.basename(doc['markdown_file'])
                doc_id = doc['document_id']
                keys_preview = ', '.join(doc['data_keys'][:3])
                if len(doc['data_keys']) > 3:
                    keys_preview += '...'
                
                index_content += f"- [**{doc_id}**]({filename}) - Keys: `{keys_preview}`\n"
            
            index_content += "\n"
        
        # Add metadata section
        index_content += f"""---

## Documentation Metadata

- **Generated By**: UniFi Backup Analyzer
- **Generation Time**: {timestamp}
- **Total Documents**: {len(analyzed_documents)}
- **Configuration Types**: {len(config_groups)}
- **Output Format**: {self.config.OUTPUT_FORMAT}

## RAG Optimization

This documentation is optimized for Retrieval-Augmented Generation (RAG) systems:

- ✅ Structured markdown format
- ✅ Consistent metadata in frontmatter
- ✅ Searchable content with keywords
- ✅ Clear section headers and navigation
- ✅ Document cross-references
- ✅ Comprehensive summaries

## File Structure

```
analysis/
├── INDEX.md (this file)
├── SUMMARY.md (overall analysis)
"""
        
        for doc in analyzed_documents:
            filename = os.path.basename(doc['markdown_file'])
            index_content += f"├── {filename}\n"
        
        index_content += "```\n"
        
        # Save index
        index_path = os.path.join(output_dir, 'INDEX.md')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        logger.info(f"Documentation index saved to {index_path}")
        return index_path