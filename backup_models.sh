#!/bin/bash
#
# Backup and restore ML models and learning data
# This script helps you safely backup your trained models before updates
#

set -e

MODELS_DIR="models"
BACKUP_DIR="models_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

backup() {
    echo -e "${GREEN}Creating backup of ML models...${NC}"
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Check if models directory exists and has files
    if [ ! -d "$MODELS_DIR" ]; then
        echo -e "${RED}Error: models/ directory does not exist${NC}"
        exit 1
    fi
    
    # Check if there are any model files to backup (excluding README and .gitkeep)
    MODEL_FILES=$(find "$MODELS_DIR" -maxdepth 1 -type f \( -name "*.pkl" -o -name "*.keras" -o -name "*.h5" -o -name "*.pt" -o -name "*.npy" -o -name "*.joblib" \) 2>/dev/null | wc -l)
    
    if [ "$MODEL_FILES" -eq 0 ]; then
        echo -e "${YELLOW}Warning: No model files found to backup${NC}"
        echo "This is normal if the bot hasn't been run yet."
        exit 0
    fi
    
    # Create timestamped backup
    BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
    mkdir -p "$BACKUP_PATH"
    
    # Copy all model files
    find "$MODELS_DIR" -maxdepth 1 -type f \( -name "*.pkl" -o -name "*.keras" -o -name "*.h5" -o -name "*.pt" -o -name "*.npy" -o -name "*.joblib" \) -exec cp -v {} "$BACKUP_PATH/" \;
    
    # Calculate backup size
    BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
    
    echo -e "${GREEN}✓ Backup created successfully!${NC}"
    echo "Location: $BACKUP_PATH"
    echo "Size: $BACKUP_SIZE"
    echo ""
    echo "Your models are safe and can be restored at any time."
}

restore() {
    echo -e "${GREEN}Restoring ML models from backup...${NC}"
    
    # Check if backup directory exists
    if [ ! -d "$BACKUP_DIR" ]; then
        echo -e "${RED}Error: No backups found${NC}"
        exit 1
    fi
    
    # List available backups
    echo "Available backups:"
    ls -1 "$BACKUP_DIR" | nl
    echo ""
    
    # If a specific backup is provided, use it
    if [ -n "$1" ]; then
        BACKUP_NAME="$1"
        RESTORE_PATH="$BACKUP_DIR/$BACKUP_NAME"
    else
        # Get the latest backup
        BACKUP_NAME=$(ls -1t "$BACKUP_DIR" | head -1)
        RESTORE_PATH="$BACKUP_DIR/$BACKUP_NAME"
        echo -e "${YELLOW}No backup specified, using latest: $BACKUP_NAME${NC}"
    fi
    
    # Check if backup exists
    if [ ! -d "$RESTORE_PATH" ]; then
        echo -e "${RED}Error: Backup not found: $RESTORE_PATH${NC}"
        exit 1
    fi
    
    # Create models directory if it doesn't exist
    mkdir -p "$MODELS_DIR"
    
    # Confirm restore
    echo -e "${YELLOW}WARNING: This will overwrite current models${NC}"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled"
        exit 0
    fi
    
    # Copy backup files to models directory
    cp -v "$RESTORE_PATH"/* "$MODELS_DIR/" 2>/dev/null || true
    
    echo -e "${GREEN}✓ Models restored successfully!${NC}"
    echo "Restored from: $RESTORE_PATH"
}

list_backups() {
    echo -e "${GREEN}Available backups:${NC}"
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
        echo "No backups found"
        exit 0
    fi
    
    echo ""
    for backup in "$BACKUP_DIR"/*; do
        if [ -d "$backup" ]; then
            backup_name=$(basename "$backup")
            backup_size=$(du -sh "$backup" | cut -f1)
            file_count=$(find "$backup" -type f | wc -l)
            echo "  $backup_name"
            echo "    Size: $backup_size"
            echo "    Files: $file_count"
            echo ""
        fi
    done
}

cleanup() {
    echo -e "${GREEN}Cleaning up old backups...${NC}"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        echo "No backups to clean up"
        exit 0
    fi
    
    # Keep only the last 5 backups
    BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" | wc -l)
    
    if [ "$BACKUP_COUNT" -gt 5 ]; then
        echo "Found $BACKUP_COUNT backups, keeping 5 most recent..."
        ls -1t "$BACKUP_DIR" | tail -n +6 | while read old_backup; do
            rm -rf "$BACKUP_DIR/$old_backup"
            echo "Removed: $old_backup"
        done
        echo -e "${GREEN}✓ Cleanup complete${NC}"
    else
        echo "Only $BACKUP_COUNT backups found, no cleanup needed"
    fi
}

show_help() {
    cat << EOF
RAD Trading Bot - Model Backup Utility

Usage: $0 [command] [options]

Commands:
    backup              Create a new backup of all ML models
    restore [name]      Restore models from backup (latest if name not specified)
    list                List all available backups
    cleanup             Remove old backups (keep only 5 most recent)
    help                Show this help message

Examples:
    $0 backup                          # Create new backup
    $0 restore                         # Restore from latest backup
    $0 restore backup_20250101_120000  # Restore specific backup
    $0 list                            # List all backups
    $0 cleanup                         # Clean up old backups

Notes:
    - Backups are stored in: $BACKUP_DIR/
    - Model files are protected by .gitignore
    - Your learning data is never lost during git pull
    - Backups are for extra safety and disaster recovery

EOF
}

# Main script logic
case "${1:-help}" in
    backup)
        backup
        ;;
    restore)
        restore "$2"
        ;;
    list)
        list_backups
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
