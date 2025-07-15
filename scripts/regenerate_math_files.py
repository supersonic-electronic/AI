#!/usr/bin/env python3
"""
Regenerate math files using the improved mathematical content detector.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.settings import Settings
from src.ingestion.improved_math_detector import ImprovedMathDetector


def regenerate_math_files():
    """Regenerate math files using improved detector."""
    
    # Load settings
    settings = Settings.from_env_and_yaml("config-improved-math.yaml")
    
    # Create improved detector
    detector = ImprovedMathDetector(settings)
    
    # Find existing math files
    math_dir = Path("data/math")
    backup_dir = Path("data/math_backup")
    
    if not backup_dir.exists():
        print("Error: No backup directory found. Please run the ingestion first.")
        return
    
    print("Regenerating math files with improved detection...")
    print("=" * 60)
    
    # Process each backup math file
    for backup_file in backup_dir.glob("*.math"):
        print(f"Processing: {backup_file.name}")
        
        # Load original math file
        with open(backup_file, 'r', encoding='utf-8') as f:
            original_entries = json.load(f)
        
        # Reprocess each entry with improved detector
        new_entries = []
        original_count = 0
        improved_count = 0
        
        for entry in original_entries:
            original_count += 1
            
            # Get the raw text
            raw_text = entry["block"]["raw_text"]
            
            # Test with improved detector
            is_math, confidence, breakdown = detector.detect_mathematical_content(raw_text)
            
            if is_math:
                # Update the entry with new confidence
                entry["block"]["confidence"] = confidence
                
                # Add detection breakdown for analysis
                entry["block"]["detection_breakdown"] = breakdown
                
                new_entries.append(entry)
                improved_count += 1
        
        # Save new math file
        output_file = math_dir / backup_file.name
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(new_entries, f, indent=2, ensure_ascii=False)
        
        print(f"  Original entries: {original_count}")
        print(f"  Improved entries: {improved_count}")
        print(f"  Reduction: {original_count - improved_count} ({(original_count - improved_count) / original_count * 100:.1f}%)")
        print()
    
    print("Regeneration complete!")
    
    # Show summary statistics
    print("\nSummary:")
    print("-" * 40)
    
    total_original = 0
    total_improved = 0
    
    for backup_file in backup_dir.glob("*.math"):
        with open(backup_file, 'r', encoding='utf-8') as f:
            original_count = len(json.load(f))
        
        math_file = math_dir / backup_file.name
        with open(math_file, 'r', encoding='utf-8') as f:
            improved_count = len(json.load(f))
        
        total_original += original_count
        total_improved += improved_count
    
    print(f"Total original detections: {total_original}")
    print(f"Total improved detections: {total_improved}")
    print(f"Total false positives removed: {total_original - total_improved}")
    print(f"False positive reduction: {(total_original - total_improved) / total_original * 100:.1f}%")


if __name__ == "__main__":
    regenerate_math_files()