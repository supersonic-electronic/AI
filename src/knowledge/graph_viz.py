"""
Graph visualization utilities for the knowledge graph.

This module provides basic visualization capabilities for the knowledge graph,
including network plots and concept relationship diagrams.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.colors import to_rgba
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

from .graph_db import GraphDatabase
from .ontology import ConceptType, RelationshipType
from src.settings import Settings


class GraphVisualizer:
    """
    Visualize knowledge graph data using matplotlib and networkx.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the graph visualizer."""
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        if not HAS_MATPLOTLIB:
            self.logger.warning("matplotlib not available, visualization disabled")
        if not HAS_NETWORKX:
            self.logger.warning("networkx not available, graph analysis disabled")
        
        # Color scheme for different concept types
        self.concept_colors = {
            ConceptType.EQUATION: '#FF6B6B',      # Red
            ConceptType.FORMULA: '#4ECDC4',       # Teal
            ConceptType.VARIABLE: '#45B7D1',      # Blue
            ConceptType.CONSTANT: '#96CEB4',      # Green
            ConceptType.FUNCTION: '#FFEAA7',      # Yellow
            ConceptType.MATRIX: '#DDA0DD',        # Plum
            ConceptType.PORTFOLIO: '#FFB74D',     # Orange
            ConceptType.RISK: '#F06292',          # Pink
            ConceptType.RETURN: '#81C784',        # Light Green
            ConceptType.OPTIMIZATION: '#BA68C8',  # Purple
            ConceptType.METRIC: '#64B5F6',        # Light Blue
            ConceptType.METHODOLOGY: '#A1887F',   # Brown
        }
        
        # Default color for unknown types
        self.default_color = '#9E9E9E'  # Grey
        
        # Initialize graph database
        self.graph_db = GraphDatabase(settings)
    
    def visualize_concept_network(self, concept_id: str, 
                                depth: int = 2, 
                                output_path: Optional[Path] = None,
                                layout: str = 'spring',
                                figsize: Tuple[int, int] = (12, 8)) -> bool:
        """
        Visualize the network around a specific concept.
        
        Args:
            concept_id: ID of the central concept
            depth: Maximum depth to explore
            output_path: Path to save the visualization
            layout: Layout algorithm ('spring', 'circular', 'random')
            figsize: Figure size (width, height)
            
        Returns:
            True if successful, False otherwise
        """
        if not HAS_MATPLOTLIB or not HAS_NETWORKX:
            self.logger.error("Visualization requires matplotlib and networkx")
            return False
        
        try:
            # Get concept network
            network_data = self.graph_db.get_concept_neighbors(concept_id, depth)
            
            if not network_data:
                self.logger.warning(f"No network data found for concept {concept_id}")
                return False
            
            # Create NetworkX graph
            G = nx.Graph()
            
            # Add central concept
            center_concept = network_data.get('center', {})
            G.add_node(concept_id, **center_concept)
            
            # Add neighbor concepts
            for neighbor in network_data.get('neighbors', []):
                neighbor_id = neighbor.get('id', '')
                if neighbor_id:
                    G.add_node(neighbor_id, **neighbor)
            
            # Add relationships
            for relationship in network_data.get('relationships', []):
                # Extract source and target from relationship
                # Note: This might need adjustment based on actual relationship structure
                source = relationship.get('source_concept_id', '')
                target = relationship.get('target_concept_id', '')
                
                if source and target and source in G and target in G:
                    G.add_edge(source, target, **relationship)
            
            # Create visualization
            plt.figure(figsize=figsize)
            
            # Choose layout
            if layout == 'spring':
                pos = nx.spring_layout(G, k=1, iterations=50)
            elif layout == 'circular':
                pos = nx.circular_layout(G)
            elif layout == 'random':
                pos = nx.random_layout(G)
            else:
                pos = nx.spring_layout(G)
            
            # Draw nodes with colors based on concept type
            node_colors = []
            node_sizes = []
            
            for node in G.nodes():
                node_data = G.nodes[node]
                concept_type = node_data.get('type', '')
                
                # Get color for concept type
                try:
                    concept_enum = ConceptType(concept_type)
                    color = self.concept_colors.get(concept_enum, self.default_color)
                except ValueError:
                    color = self.default_color
                
                node_colors.append(color)
                
                # Size based on confidence or centrality
                confidence = node_data.get('confidence', 0.5)
                size = 300 + (confidence * 700)  # Size between 300 and 1000
                node_sizes.append(size)
            
            # Draw the graph
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                                 node_size=node_sizes, alpha=0.8)
            
            nx.draw_networkx_edges(G, pos, alpha=0.5, width=1)
            
            # Add labels
            labels = {}
            for node in G.nodes():
                node_data = G.nodes[node]
                name = node_data.get('name', node)
                # Truncate long names
                if len(name) > 15:
                    name = name[:12] + '...'
                labels[node] = name
            
            nx.draw_networkx_labels(G, pos, labels, font_size=8)
            
            # Add title
            central_name = center_concept.get('name', concept_id)
            plt.title(f"Concept Network: {central_name}", fontsize=16, fontweight='bold')
            
            # Create legend
            legend_elements = []
            for concept_type, color in self.concept_colors.items():
                legend_elements.append(patches.Patch(color=color, label=concept_type.value))
            
            plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.2, 1))
            
            plt.axis('off')
            plt.tight_layout()
            
            # Save or show
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Visualization saved to {output_path}")
            else:
                plt.show()
            
            plt.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating visualization: {e}")
            return False
    
    def visualize_document_concepts(self, document_name: str,
                                  output_path: Optional[Path] = None,
                                  figsize: Tuple[int, int] = (14, 10)) -> bool:
        """
        Visualize concepts from a specific document.
        
        Args:
            document_name: Name of the document
            output_path: Path to save the visualization
            figsize: Figure size (width, height)
            
        Returns:
            True if successful, False otherwise
        """
        if not HAS_MATPLOTLIB or not HAS_NETWORKX:
            self.logger.error("Visualization requires matplotlib and networkx")
            return False
        
        try:
            # Get document concepts
            concepts = self.graph_db.get_document_concepts(document_name)
            
            if not concepts:
                self.logger.warning(f"No concepts found for document {document_name}")
                return False
            
            # Create graph
            G = nx.Graph()
            
            # Add concepts as nodes
            for concept in concepts:
                concept_id = concept.get('id', '')
                if concept_id:
                    G.add_node(concept_id, **concept)
            
            # Add relationships between concepts in this document
            for concept in concepts:
                concept_id = concept.get('id', '')
                if concept_id:
                    related = self.graph_db.get_related_concepts(concept_id)
                    for rel in related:
                        related_concept = rel.get('concept', {})
                        related_id = related_concept.get('id', '')
                        
                        # Only add if both concepts are from the same document
                        if (related_id and related_id in G and 
                            related_concept.get('source_document') == document_name):
                            G.add_edge(concept_id, related_id, **rel.get('relationship', {}))
            
            # Create visualization
            plt.figure(figsize=figsize)
            
            # Use spring layout for better visualization
            pos = nx.spring_layout(G, k=2, iterations=50)
            
            # Group concepts by type for better visualization
            concept_groups = {}
            for node in G.nodes():
                node_data = G.nodes[node]
                concept_type = node_data.get('type', 'unknown')
                
                if concept_type not in concept_groups:
                    concept_groups[concept_type] = []
                concept_groups[concept_type].append(node)
            
            # Draw nodes by group
            for concept_type, nodes in concept_groups.items():
                try:
                    concept_enum = ConceptType(concept_type)
                    color = self.concept_colors.get(concept_enum, self.default_color)
                except ValueError:
                    color = self.default_color
                
                # Calculate node sizes based on confidence
                node_sizes = []
                for node in nodes:
                    node_data = G.nodes[node]
                    confidence = node_data.get('confidence', 0.5)
                    size = 200 + (confidence * 500)
                    node_sizes.append(size)
                
                nx.draw_networkx_nodes(G, pos, nodelist=nodes, 
                                     node_color=color, node_size=node_sizes, 
                                     alpha=0.8, label=concept_type)
            
            # Draw edges
            nx.draw_networkx_edges(G, pos, alpha=0.3, width=1.5)
            
            # Add labels
            labels = {}
            for node in G.nodes():
                node_data = G.nodes[node]
                name = node_data.get('name', node)
                if len(name) > 12:
                    name = name[:9] + '...'
                labels[node] = name
            
            nx.draw_networkx_labels(G, pos, labels, font_size=9)
            
            # Add title
            plt.title(f"Document Concepts: {document_name}", fontsize=16, fontweight='bold')
            
            # Add legend
            plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1))
            
            # Add statistics
            stats_text = f"Concepts: {len(concepts)}\nConnections: {len(G.edges())}"
            plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            plt.axis('off')
            plt.tight_layout()
            
            # Save or show
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Document visualization saved to {output_path}")
            else:
                plt.show()
            
            plt.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating document visualization: {e}")
            return False
    
    def create_concept_hierarchy_diagram(self, concept_types: List[str],
                                       output_path: Optional[Path] = None,
                                       figsize: Tuple[int, int] = (12, 8)) -> bool:
        """
        Create a hierarchical diagram of concept types.
        
        Args:
            concept_types: List of concept types to include
            output_path: Path to save the diagram
            figsize: Figure size (width, height)
            
        Returns:
            True if successful, False otherwise
        """
        if not HAS_MATPLOTLIB:
            self.logger.error("Visualization requires matplotlib")
            return False
        
        try:
            # Create figure
            fig, ax = plt.subplots(figsize=figsize)
            
            # Define hierarchy levels
            hierarchy = {
                'Mathematical': [ConceptType.EQUATION, ConceptType.FORMULA, ConceptType.VARIABLE, 
                               ConceptType.CONSTANT, ConceptType.FUNCTION, ConceptType.MATRIX],
                'Financial': [ConceptType.PORTFOLIO, ConceptType.RISK, ConceptType.RETURN, 
                            ConceptType.OPTIMIZATION, ConceptType.METRIC],
                'Semantic': [ConceptType.METHODOLOGY, ConceptType.ALGORITHM, ConceptType.DEFINITION]
            }
            
            y_pos = 0.8
            x_positions = [0.2, 0.5, 0.8]
            
            # Draw hierarchy
            for i, (category, types) in enumerate(hierarchy.items()):
                # Draw category header
                ax.text(x_positions[i], y_pos, category, fontsize=14, fontweight='bold',
                       ha='center', transform=ax.transAxes)
                
                # Draw concept types
                for j, concept_type in enumerate(types):
                    if concept_type.value in concept_types:
                        y = y_pos - 0.1 * (j + 1)
                        color = self.concept_colors.get(concept_type, self.default_color)
                        
                        # Draw colored box
                        rect = patches.Rectangle((x_positions[i] - 0.1, y - 0.02), 0.2, 0.04,
                                               facecolor=color, alpha=0.7, transform=ax.transAxes)
                        ax.add_patch(rect)
                        
                        # Add text
                        ax.text(x_positions[i], y, concept_type.value, fontsize=10,
                               ha='center', va='center', transform=ax.transAxes)
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            plt.title('Concept Type Hierarchy', fontsize=16, fontweight='bold')
            plt.tight_layout()
            
            # Save or show
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Hierarchy diagram saved to {output_path}")
            else:
                plt.show()
            
            plt.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating hierarchy diagram: {e}")
            return False
    
    def export_graph_for_external_viz(self, output_path: Path, 
                                    format: str = 'gexf') -> bool:
        """
        Export graph data for external visualization tools.
        
        Args:
            output_path: Path to save the export
            format: Export format ('gexf', 'graphml', 'json')
            
        Returns:
            True if successful, False otherwise
        """
        if not HAS_NETWORKX:
            self.logger.error("Export requires networkx")
            return False
        
        try:
            # Get all concepts and relationships
            concepts = self.graph_db.query_graph("MATCH (c:Concept) RETURN c")
            relationships = self.graph_db.query_graph("MATCH ()-[r:RELATED_TO]->() RETURN r")
            
            # Create NetworkX graph
            G = nx.Graph()
            
            # Add concepts as nodes
            for concept in concepts:
                concept_data = concept.get('c', {})
                concept_id = concept_data.get('id', '')
                if concept_id:
                    G.add_node(concept_id, **concept_data)
            
            # Add relationships as edges
            for relationship in relationships:
                rel_data = relationship.get('r', {})
                source = rel_data.get('source_concept_id', '')
                target = rel_data.get('target_concept_id', '')
                
                if source and target and source in G and target in G:
                    G.add_edge(source, target, **rel_data)
            
            # Export in requested format
            if format == 'gexf':
                nx.write_gexf(G, output_path)
            elif format == 'graphml':
                nx.write_graphml(G, output_path)
            elif format == 'json':
                # Custom JSON export
                export_data = {
                    'nodes': [{'id': node, **data} for node, data in G.nodes(data=True)],
                    'edges': [{'source': source, 'target': target, **data} 
                             for source, target, data in G.edges(data=True)]
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return False
            
            self.logger.info(f"Graph exported to {output_path} in {format} format")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting graph: {e}")
            return False
    
    def close(self):
        """Close the graph database connection."""
        if self.graph_db:
            self.graph_db.close()


def get_graph_visualizer(settings: Settings) -> GraphVisualizer:
    """
    Factory function to create a graph visualizer.
    
    Args:
        settings: Application settings
        
    Returns:
        GraphVisualizer instance
    """
    return GraphVisualizer(settings)