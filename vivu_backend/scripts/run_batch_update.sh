#!/bin/bash
# Script to run batch update for all places
# This will take several hours due to geocoding API rate limits

echo "Starting batch update for all places from row 58..."
echo "This will take several hours. Progress will be logged."
echo ""

python scripts/batch_update_places_optimized.py --start 58 2>&1 | tee batch_update_log.txt

echo ""
echo "Batch update completed. Check batch_update_log.txt for details."






