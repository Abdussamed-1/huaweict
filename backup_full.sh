#!/bin/bash
# Full Backup Script - Milvus + RDS
# Usage: ./backup_full.sh

set -e

BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "🔄 Starting full backup..."
echo "Backup directory: $BACKUP_DIR"

# 1. Export Milvus
echo ""
echo "📦 Step 1: Exporting Milvus..."
python export_from_milvus.py \
  --format json \
  --output $BACKUP_DIR/milvus_backup.json \
  --batch-size 1000

# 2. Backup RDS (if configured)
if [ ! -z "$RDS_HOST" ]; then
    echo ""
    echo "📦 Step 2: Backing up RDS..."
    
    if [ "$RDS_ENGINE" == "postgresql" ]; then
        PGPASSWORD=$RDS_PASSWORD pg_dump \
          -h $RDS_HOST \
          -p $RDS_PORT \
          -U $RDS_USER \
          -d $RDS_DB \
          -F c \
          -f $BACKUP_DIR/rds_backup.dump
    elif [ "$RDS_ENGINE" == "mysql" ]; then
        mysqldump \
          -h $RDS_HOST \
          -P $RDS_PORT \
          -u $RDS_USER \
          -p$RDS_PASSWORD \
          $RDS_DB \
          > $BACKUP_DIR/rds_backup.sql
    fi
    
    echo "✅ RDS backup completed"
else
    echo "⚠️  RDS not configured, skipping RDS backup"
fi

# 3. Upload to OBS (if configured)
if [ ! -z "$OBS_BUCKET_NAME" ]; then
    echo ""
    echo "📤 Step 3: Uploading to OBS..."
    
    # Check if obsutil is available
    if command -v obsutil &> /dev/null; then
        obsutil cp $BACKUP_DIR obs://$OBS_BUCKET_NAME/backups/$(date +%Y%m%d)/
        echo "✅ Uploaded to OBS"
    else
        echo "⚠️  obsutil not found, skipping OBS upload"
    fi
else
    echo "⚠️  OBS not configured, skipping OBS upload"
fi

# 4. Create backup manifest
echo ""
echo "📝 Step 4: Creating backup manifest..."
cat > $BACKUP_DIR/manifest.json <<EOF
{
  "backup_date": "$(date -Iseconds)",
  "milvus_backup": "milvus_backup.json",
  "rds_backup": "$([ -z "$RDS_HOST" ] && echo "none" || echo "rds_backup.$([ "$RDS_ENGINE" == "postgresql" ] && echo "dump" || echo "sql")")",
  "backup_size": "$(du -sh $BACKUP_DIR | cut -f1)"
}
EOF

echo ""
echo "✅ Full backup completed!"
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Files:"
ls -lh $BACKUP_DIR

