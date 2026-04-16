#!/bin/bash
set -e

DB_HOST="${MOODLE_DATABASE_HOST:-db}"
DB_USER="${MOODLE_DATABASE_USER:-moodle}"
DB_PASS="${MOODLE_DATABASE_PASSWORD:-moodlesecret}"
DB_NAME="${MOODLE_DATABASE_NAME:-moodle}"

echo "Waiting for MySQL at $DB_HOST:3306..."
until nc -z "$DB_HOST" 3306; do
  echo "MySQL is unavailable - sleeping"
  sleep 2
done
echo "MySQL is up!"

# Generate config.php if not present
if [ ! -f /var/www/html/config.php ]; then
  echo "Generating config.php..."
  cat > /var/www/html/config.php <<EOF
<?php
unset(\$CFG);
global \$CFG;
\$CFG = new stdClass();
\$CFG->dbtype    = 'mysqli';
\$CFG->dblibrary = 'native';
\$CFG->dbhost    = '$DB_HOST';
\$CFG->dbname    = '$DB_NAME';
\$CFG->dbuser    = '$DB_USER';
\$CFG->dbpass    = '$DB_PASS';
\$CFG->prefix    = 'mdl_';
\$CFG->dboptions = ['dbpersist' => false, 'dbport' => 3306, 'dbsocket' => ''];
\$CFG->wwwroot   = 'http://localhost:62080';
\$CFG->dataroot  = '/var/www/moodledata';
\$CFG->admin     = 'admin';
\$CFG->directorypermissions = 02777;
require_once(__DIR__ . '/lib/setup.php');
EOF
  chown www-data:www-data /var/www/html/config.php
fi

exec "$@"
