-- Tags: no-parallel

SET allow_experimental_database_replicated=1;

DROP DATABASE IF EXISTS replicated_database_params;

CREATE DATABASE replicated_database_params ENGINE = Replicated('some/path/' || currentDatabase() || '/replicated_database_params');
SHOW CREATE DATABASE replicated_database_params;
DROP DATABASE replicated_database_params;

CREATE DATABASE replicated_database_params ENGINE = Replicated('some/path/' || currentDatabase() || '/replicated_database_params', 'shard_1');
SHOW CREATE DATABASE replicated_database_params;
DROP DATABASE replicated_database_params;
