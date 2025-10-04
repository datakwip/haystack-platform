# Configuration

## ⚠️ Important: config.json Security

**DO NOT commit production credentials to this repository!**

1. Copy `config.json.example` to `config.json`
2. Update `config.json` with your local or production credentials
3. `config.json` is already in `.gitignore` and will not be committed

For local Docker development, the default `config.json` uses:
- Environment: `local`
- Database: TimescaleDB container (`timescaledb:5432`)
- Schema: `public`

# Installation
To install this tool as a package into Python virtual environment:

1. Install virtualenv with pip:
`pip3 install virtualenv`

2. Create new virtual env with python3:
`virtualenv ezm -p python3`

3. Activate virtual env:
Linux: `source ezm/bin/activate`
Windows: `.\ezm\Scripts\activate.bat` in cmd or `.\ezm\Scripts\activate.ps1` in PowerShell

4. Install dependencies:
`pip3 install -r requirements.txt`

5. Run timescaledb locally:
`docker run -d --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=password timescale/timescaledb:latest-pg14`
6. Create Timescaledb database:
`CREATE DATABASE master`
`CREATE EXTENSION IF NOT EXISTS timescaledb;`
7. Build docker
`docker build -t db-service-layer .`
`docker run -d -p 8085:80 --name db-service-layer db-service-layer:latest`
8. autopep
`autopep8 --in-place --recursive ./src`
9 Install antrl
OS X
$ cd /usr/local/lib
$ sudo curl -O https://www.antlr.org/download/antlr-4.10.1-complete.jar
$ export CLASSPATH=".:/usr/local/lib/antlr-4.10.1-complete.jar:$CLASSPATH"
$ alias antlr4='java -jar /usr/local/lib/antlr-4.10.1-complete.jar'
$ alias grun='java org.antlr.v4.gui.TestRig'
$ antlr4 -Dlanguage=Python3 MyGrammer.g4 -visitor -o dist
10. User autopep8
autopep8 --in-place --aggressive <filename>
11. Create hypertable

CREATE OR REPLACE FUNCTION core_dev.create_hypertable(tablename character varying)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
	BEGIN
		PERFORM create_hypertable(tableName, 'ts', chunk_time_interval => INTERVAL '1 month');
		EXECUTE 'ALTER TABLE ' || tableName || ' SET (timescaledb.compress, timescaledb.compress_segmentby = "entity_id");';
		PERFORM add_compression_policy(tableName, INTERVAL '14 days');
	END;
$function$
;


restore core_sanbox from core


insert into core_sandbox.org
 select * from core.org;

insert into core_sandbox."user"
 select * from core."user";

insert into core_sandbox.user_app
 select * from core.user_app;

  insert into core_sandbox.org_user
 select * from core.org_user

  insert into core_sandbox.tag_def
 select * from core.tag_def

  insert into core_sandbox.tag_def_h
 select * from core.tag_def_h

  insert into core_sandbox.tag_def_enum
 select * from core.tag_def_enum

  insert into core_sandbox.tag_def_enum_h
 select * from core.tag_def_enum_h

 insert into core_sandbox.tag_hierarchy
 select * from core.tag_hierarchy

  insert into core_sandbox.tag_hierarchy_h
 select * from core.tag_hierarchy_h

  insert into core_sandbox.tag_meta
 select * from core.tag_meta

  insert into core_sandbox.tag_meta_h
 select * from core.tag_meta_h

  insert into core_sandbox.entity
 select * from core.entity

  insert into core_sandbox.entity_tag
 select * from core.entity_tag

  insert into core_sandbox.entity_tag_h
 select * from core.entity_tag_h

  insert into core_sandbox.org_admin
 select * from core.org_admin

  insert into core_sandbox.org_entity_permission
 select * from core.org_entity_permission

  insert into core_sandbox.org_tag_permission
 select * from core.org_tag_permission

  insert into core_sandbox.user_entity_add_permission
 select * from core.user_entity_add_permission

  insert into core_sandbox.user_entity_rev_permission
 select * from core.user_entity_rev_permission

  insert into core_sandbox.user_tag_add_permission
 select * from core.user_tag_add_permission

  insert into core_sandbox.user_tag_rev_permission
 select * from core.user_tag_rev_permission


grant select, insert,update,delete on all tables in schema core_sandbox to  "vpryimak"
