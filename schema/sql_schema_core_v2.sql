-- core.entity definition

-- Drop table

-- DROP TABLE core.entity;

CREATE TABLE core.entity (
	id serial4 NOT NULL,
	value_table_id varchar NULL,
	disabled_ts timestamp NULL,
	CONSTRAINT entity_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_entity_id ON core.entity USING btree (id);


-- core.entity_enum definition

-- Drop table

-- DROP TABLE core.entity_enum;

CREATE TABLE core.entity_enum (
	id serial4 NOT NULL,
	enum_id int4 NULL,
	value varchar NULL,
	"label" varchar NULL,
	disabled_ts timestamp NULL,
	CONSTRAINT entity_enum_enum_id_value_key UNIQUE (enum_id, value),
	CONSTRAINT entity_enum_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_entity_enum_id ON core.entity_enum USING btree (id);


-- core.entity_enum_def definition

-- Drop table

-- DROP TABLE core.entity_enum_def;

CREATE TABLE core.entity_enum_def (
	id serial4 NOT NULL,
	"name" varchar NULL,
	CONSTRAINT entity_enum_def_name_key UNIQUE (name),
	CONSTRAINT entity_enum_def_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_entity_enum_def_id ON core.entity_enum_def USING btree (id);


-- core.entity_enum_h definition

-- Drop table

-- DROP TABLE core.entity_enum_h;

CREATE TABLE core.entity_enum_h (
	id int4 NOT NULL,
	enum_id int4 NULL,
	value varchar NULL,
	"label" varchar NULL,
	user_id int4 NOT NULL,
	modified timestamp NOT NULL,
	CONSTRAINT entity_enum_h_enum_id_value_modified_key UNIQUE (enum_id, value, modified),
	CONSTRAINT entity_enum_h_pkey PRIMARY KEY (id, modified)
);
CREATE INDEX ix_core_entity_enum_h_id ON core.entity_enum_h USING btree (id);
CREATE INDEX ix_core_entity_enum_h_user_id ON core.entity_enum_h USING btree (user_id);


-- core.entity_tag definition

-- Drop table

-- DROP TABLE core.entity_tag;

CREATE TABLE core.entity_tag (
	id serial4 NOT NULL,
	entity_id int4 NULL,
	tag_id int4 NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_list _varchar NULL,
	value_dict jsonb NULL,
	value_ref int4 NULL,
	value_enum int4 NULL,
	disabled_ts timestamp NULL,
	CONSTRAINT entity_tag_entity_id_tag_id_disabled_ts_key UNIQUE (entity_id, tag_id, disabled_ts),
	CONSTRAINT entity_tag_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_entity_tag_entity_id ON core.entity_tag USING btree (entity_id);
CREATE INDEX ix_core_entity_tag_id ON core.entity_tag USING btree (id);
CREATE INDEX ix_core_entity_tag_tag_id ON core.entity_tag USING btree (tag_id);


-- core.entity_tag_delete definition

-- Drop table

-- DROP TABLE core.entity_tag_delete;

CREATE TABLE core.entity_tag_delete (
	id int4 NULL,
	entity_id int4 NULL,
	tag_id int4 NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_list _varchar NULL,
	value_dict jsonb NULL,
	value_ref int4 NULL,
	value_enum int4 NULL,
	disabled_ts timestamp NULL
);


-- core.entity_tag_delete_20250421 definition

-- Drop table

-- DROP TABLE core.entity_tag_delete_20250421;

CREATE TABLE core.entity_tag_delete_20250421 (
	id int4 NULL,
	entity_id int4 NULL,
	tag_id int4 NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_list _varchar NULL,
	value_dict jsonb NULL,
	value_ref int4 NULL,
	value_enum int4 NULL,
	disabled_ts timestamp NULL
);


-- core.entity_tag_h definition

-- Drop table

-- DROP TABLE core.entity_tag_h;

CREATE TABLE core.entity_tag_h (
	id int4 NOT NULL,
	entity_id int4 NULL,
	tag_id int4 NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_list _varchar NULL,
	value_dict jsonb NULL,
	value_ref int4 NULL,
	value_enum int4 NULL,
	user_id int4 NOT NULL,
	modified timestamp NOT NULL,
	CONSTRAINT entity_tag_h_entity_id_tag_id_modified_key UNIQUE (entity_id, tag_id, modified),
	CONSTRAINT entity_tag_h_pkey PRIMARY KEY (id, modified)
);
CREATE INDEX ix_core_entity_tag_h_id ON core.entity_tag_h USING btree (id);
CREATE INDEX ix_core_entity_tag_h_user_id ON core.entity_tag_h USING btree (user_id);


-- core.entity_test definition

-- Drop table

-- DROP TABLE core.entity_test;

CREATE TABLE core.entity_test (
	id serial4 NOT NULL,
	value_table_id varchar NULL,
	disabled_ts timestamp NULL,
	CONSTRAINT entity_test__pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_entity_test__id ON core.entity_test USING btree (id);


-- core.org definition

-- Drop table

-- DROP TABLE core.org;

CREATE TABLE core.org (
	id serial4 NOT NULL,
	"name" varchar NULL,
	"key" varchar NULL,
	value_table varchar NOT NULL,
	disabled_ts timestamp NULL,
	schema_name varchar NOT NULL,
	CONSTRAINT org_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_org_id ON core.org USING btree (id);
CREATE UNIQUE INDEX ix_core_org_name ON core.org USING btree (name);


-- core.org_admin definition

-- Drop table

-- DROP TABLE core.org_admin;

CREATE TABLE core.org_admin (
	id serial4 NOT NULL,
	org_id int4 NOT NULL,
	user_id int4 NOT NULL,
	CONSTRAINT org_admin_org_id_user_id_key UNIQUE (org_id, user_id),
	CONSTRAINT org_admin_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_org_admin_id ON core.org_admin USING btree (id);
CREATE INDEX ix_core_org_admin_org_id ON core.org_admin USING btree (org_id);
CREATE INDEX ix_core_org_admin_user_id ON core.org_admin USING btree (user_id);


-- core.org_entity_permission definition

-- Drop table

-- DROP TABLE core.org_entity_permission;

CREATE TABLE core.org_entity_permission (
	id serial4 NOT NULL,
	org_id int4 NOT NULL,
	entity_id int4 NOT NULL,
	CONSTRAINT org_entity_permission_org_id_entity_id_key UNIQUE (org_id, entity_id),
	CONSTRAINT org_entity_permission_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_org_entity_permission_entity_id ON core.org_entity_permission USING btree (entity_id);
CREATE INDEX ix_core_org_entity_permission_id ON core.org_entity_permission USING btree (id);
CREATE INDEX ix_core_org_entity_permission_org_id ON core.org_entity_permission USING btree (org_id);


-- core.org_tag_permission definition

-- Drop table

-- DROP TABLE core.org_tag_permission;

CREATE TABLE core.org_tag_permission (
	id serial4 NOT NULL,
	org_id int4 NOT NULL,
	tag_id int4 NOT NULL,
	CONSTRAINT org_tag_permission_org_id_tag_id_key UNIQUE (org_id, tag_id),
	CONSTRAINT org_tag_permission_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_org_tag_permission_id ON core.org_tag_permission USING btree (id);
CREATE INDEX ix_core_org_tag_permission_org_id ON core.org_tag_permission USING btree (org_id);
CREATE INDEX ix_core_org_tag_permission_tag_id ON core.org_tag_permission USING btree (tag_id);


-- core.org_user definition

-- Drop table

-- DROP TABLE core.org_user;

CREATE TABLE core.org_user (
	id serial4 NOT NULL,
	user_id int4 NOT NULL,
	org_id int4 NOT NULL,
	CONSTRAINT org_user_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_org_user_id ON core.org_user USING btree (id);
CREATE INDEX ix_core_org_user_org_id ON core.org_user USING btree (org_id);
CREATE INDEX ix_core_org_user_user_id ON core.org_user USING btree (user_id);


-- core.poller_config definition

-- Drop table

-- DROP TABLE core.poller_config;

CREATE TABLE core.poller_config (
	id serial4 NOT NULL,
	org_id int4 NOT NULL,
	poller_type varchar(255) NOT NULL,
	poller_id serial4 NOT NULL,
	poller_name varchar(255) NOT NULL,
	config text NOT NULL,
	created_at timestamp DEFAULT now() NULL,
	status varchar NOT NULL,
	CONSTRAINT poller_config_pkey PRIMARY KEY (id),
	CONSTRAINT poller_config_poller_id_key UNIQUE (poller_id)
);
CREATE INDEX ix_core_poller_config_poller_id ON core.poller_config USING btree (poller_id);


-- core.tag_def definition

-- Drop table

-- DROP TABLE core.tag_def;

CREATE TABLE core.tag_def (
	id serial4 NOT NULL,
	"name" varchar NOT NULL,
	url varchar NULL,
	doc varchar NULL,
	dis varchar NULL,
	file_ext varchar NULL,
	mime varchar NULL,
	"version" varchar NULL,
	min_val int4 NULL,
	max_val int4 NULL,
	base_uri varchar NULL,
	pref_unit _varchar NULL,
	disabled_ts timestamp NULL,
	CONSTRAINT tag_def_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_tag_def_id ON core.tag_def USING btree (id);
CREATE UNIQUE INDEX ix_core_tag_def_name ON core.tag_def USING btree (name);


-- core.tag_def_enum definition

-- Drop table

-- DROP TABLE core.tag_def_enum;

CREATE TABLE core.tag_def_enum (
	id serial4 NOT NULL,
	tag_id int4 NOT NULL,
	value varchar NOT NULL,
	"label" varchar NOT NULL,
	disabled_ts timestamp NULL,
	CONSTRAINT tag_def_enum_pkey PRIMARY KEY (id),
	CONSTRAINT tag_def_enum_tag_id_value_key UNIQUE (tag_id, value)
);
CREATE INDEX ix_core_tag_def_enum_id ON core.tag_def_enum USING btree (id);
CREATE INDEX ix_core_tag_def_enum_tag_id ON core.tag_def_enum USING btree (tag_id);


-- core.tag_def_enum_h definition

-- Drop table

-- DROP TABLE core.tag_def_enum_h;

CREATE TABLE core.tag_def_enum_h (
	id int4 NOT NULL,
	tag_id int4 NOT NULL,
	value varchar NOT NULL,
	"label" varchar NOT NULL,
	user_id int4 NOT NULL,
	modified timestamp NOT NULL,
	CONSTRAINT tag_def_enum_h_pkey PRIMARY KEY (id, modified),
	CONSTRAINT tag_def_enum_h_tag_id_value_modified_key UNIQUE (tag_id, value, modified)
);
CREATE INDEX ix_core_tag_def_enum_h_id ON core.tag_def_enum_h USING btree (id);
CREATE INDEX ix_core_tag_def_enum_h_tag_id ON core.tag_def_enum_h USING btree (tag_id);
CREATE INDEX ix_core_tag_def_enum_h_user_id ON core.tag_def_enum_h USING btree (user_id);


-- core.tag_def_h definition

-- Drop table

-- DROP TABLE core.tag_def_h;

CREATE TABLE core.tag_def_h (
	id int4 NOT NULL,
	"name" varchar NULL,
	url varchar NULL,
	doc varchar NULL,
	dis varchar NULL,
	file_ext varchar NULL,
	mime varchar NULL,
	"version" varchar NULL,
	min_val int4 NULL,
	max_val int4 NULL,
	base_uri varchar NULL,
	pref_unit _varchar NULL,
	user_id int4 NOT NULL,
	modified timestamp NOT NULL,
	CONSTRAINT tag_def_h_name_modified_key UNIQUE (name, modified),
	CONSTRAINT tag_def_h_pkey PRIMARY KEY (id, modified)
);
CREATE INDEX ix_core_tag_def_h_id ON core.tag_def_h USING btree (id);
CREATE INDEX ix_core_tag_def_h_name ON core.tag_def_h USING btree (name);
CREATE INDEX ix_core_tag_def_h_user_id ON core.tag_def_h USING btree (user_id);


-- core.tag_hierarchy definition

-- Drop table

-- DROP TABLE core.tag_hierarchy;

CREATE TABLE core.tag_hierarchy (
	id serial4 NOT NULL,
	child_id int4 NOT NULL,
	parent_id int4 NOT NULL,
	disabled_ts timestamp NULL,
	CONSTRAINT tag_hierarchy_child_id_parent_id_key UNIQUE (child_id, parent_id),
	CONSTRAINT tag_hierarchy_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_tag_hierarchy_id ON core.tag_hierarchy USING btree (id);


-- core.tag_hierarchy_h definition

-- Drop table

-- DROP TABLE core.tag_hierarchy_h;

CREATE TABLE core.tag_hierarchy_h (
	id int4 NOT NULL,
	child_id int4 NOT NULL,
	parent_id int4 NOT NULL,
	user_id int4 NOT NULL,
	modified timestamp NOT NULL,
	CONSTRAINT tag_hierarchy_h_child_id_parent_id_modified_key UNIQUE (child_id, parent_id, modified),
	CONSTRAINT tag_hierarchy_h_pkey PRIMARY KEY (id, modified)
);
CREATE INDEX ix_core_tag_hierarchy_h_id ON core.tag_hierarchy_h USING btree (id);
CREATE INDEX ix_core_tag_hierarchy_h_user_id ON core.tag_hierarchy_h USING btree (user_id);


-- core.tag_meta definition

-- Drop table

-- DROP TABLE core.tag_meta;

CREATE TABLE core.tag_meta (
	id serial4 NOT NULL,
	tag_id int4 NOT NULL,
	"attribute" int4 NOT NULL,
	value int4 NULL,
	disabled_ts timestamp NULL,
	CONSTRAINT tag_meta_pkey PRIMARY KEY (id),
	CONSTRAINT tag_meta_tag_id_attribute_value_key UNIQUE (tag_id, attribute, value)
);
CREATE INDEX ix_core_tag_meta_id ON core.tag_meta USING btree (id);


-- core.tag_meta_h definition

-- Drop table

-- DROP TABLE core.tag_meta_h;

CREATE TABLE core.tag_meta_h (
	id int4 NOT NULL,
	tag_id int4 NOT NULL,
	"attribute" int4 NOT NULL,
	value int4 NULL,
	user_id int4 NOT NULL,
	modified timestamp NOT NULL,
	CONSTRAINT tag_meta_h_pkey PRIMARY KEY (id, modified),
	CONSTRAINT tag_meta_h_tag_id_attribute_value_modified_key UNIQUE (tag_id, attribute, value, modified)
);
CREATE INDEX ix_core_tag_meta_h_id ON core.tag_meta_h USING btree (id);
CREATE INDEX ix_core_tag_meta_h_user_id ON core.tag_meta_h USING btree (user_id);


-- core.temp1 definition

-- Drop table

-- DROP TABLE core.temp1;

CREATE TABLE core.temp1 (
	entity_id int4 NULL,
	value_s varchar NULL
);


-- core.test_entity definition

-- Drop table

-- DROP TABLE core.test_entity;

CREATE TABLE core.test_entity (
	id serial4 NOT NULL,
	value_table_id varchar NULL,
	disabled_ts timestamp NULL,
	CONSTRAINT test_entity_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_test_entity_id ON core.test_entity USING btree (id);


-- core.test_values definition

-- Drop table

-- DROP TABLE core.test_values;

CREATE TABLE core.test_values (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	value_dict jsonb NULL,
	CONSTRAINT test_values_pkey PRIMARY KEY (entity_id, ts)
);


-- core.test_values_current definition

-- Drop table

-- DROP TABLE core.test_values_current;

CREATE TABLE core.test_values_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT test_values_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_test_values_current_entity_id ON core.test_values_current USING btree (entity_id);


-- core.uploaded_files definition

-- Drop table

-- DROP TABLE core.uploaded_files;

CREATE TABLE core.uploaded_files (
	file_id uuid NOT NULL,
	poller_id int4 NOT NULL,
	raw_file_path text NOT NULL,
	processed_file_path text NULL,
	created_time timestamp NULL,
	processed_time timestamp NULL,
	stored_time timestamp NULL,
	CONSTRAINT uploaded_files_pkey PRIMARY KEY (file_id)
);


-- core."user" definition

-- Drop table

-- DROP TABLE core."user";

CREATE TABLE core."user" (
	id serial4 NOT NULL,
	email varchar NULL,
	disabled_ts timestamp NULL,
	CONSTRAINT user_pkey PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_core_user_email ON core."user" USING btree (email);
CREATE INDEX ix_core_user_id ON core."user" USING btree (id);


-- core.user_app definition

-- Drop table

-- DROP TABLE core.user_app;

CREATE TABLE core.user_app (
	id serial4 NOT NULL,
	user_id int4 NOT NULL,
	CONSTRAINT user_app_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_core_user_app_id ON core.user_app USING btree (id);
CREATE INDEX ix_core_user_app_user_id ON core.user_app USING btree (user_id);


-- core.user_entity_add_permission definition

-- Drop table

-- DROP TABLE core.user_entity_add_permission;

CREATE TABLE core.user_entity_add_permission (
	id serial4 NOT NULL,
	user_id int4 NOT NULL,
	entity_id int4 NOT NULL,
	CONSTRAINT user_entity_add_permission_pkey PRIMARY KEY (id),
	CONSTRAINT user_entity_add_permission_user_id_entity_id_key UNIQUE (user_id, entity_id)
);
CREATE INDEX ix_core_user_entity_add_permission_entity_id ON core.user_entity_add_permission USING btree (entity_id);
CREATE INDEX ix_core_user_entity_add_permission_id ON core.user_entity_add_permission USING btree (id);
CREATE INDEX ix_core_user_entity_add_permission_user_id ON core.user_entity_add_permission USING btree (user_id);


-- core.user_entity_rev_permission definition

-- Drop table

-- DROP TABLE core.user_entity_rev_permission;

CREATE TABLE core.user_entity_rev_permission (
	id serial4 NOT NULL,
	user_id int4 NOT NULL,
	entity_id int4 NOT NULL,
	CONSTRAINT user_entity_rev_permission_pkey PRIMARY KEY (id),
	CONSTRAINT user_entity_rev_permission_user_id_entity_id_key UNIQUE (user_id, entity_id)
);
CREATE INDEX ix_core_user_entity_rev_permission_entity_id ON core.user_entity_rev_permission USING btree (entity_id);
CREATE INDEX ix_core_user_entity_rev_permission_id ON core.user_entity_rev_permission USING btree (id);
CREATE INDEX ix_core_user_entity_rev_permission_user_id ON core.user_entity_rev_permission USING btree (user_id);


-- core.user_tag_add_permission definition

-- Drop table

-- DROP TABLE core.user_tag_add_permission;

CREATE TABLE core.user_tag_add_permission (
	id serial4 NOT NULL,
	user_id int4 NOT NULL,
	tag_id int4 NOT NULL,
	CONSTRAINT user_tag_add_permission_pkey PRIMARY KEY (id),
	CONSTRAINT user_tag_add_permission_user_id_tag_id_key UNIQUE (user_id, tag_id)
);
CREATE INDEX ix_core_user_tag_add_permission_id ON core.user_tag_add_permission USING btree (id);
CREATE INDEX ix_core_user_tag_add_permission_tag_id ON core.user_tag_add_permission USING btree (tag_id);
CREATE INDEX ix_core_user_tag_add_permission_user_id ON core.user_tag_add_permission USING btree (user_id);


-- core.user_tag_rev_permission definition

-- Drop table

-- DROP TABLE core.user_tag_rev_permission;

CREATE TABLE core.user_tag_rev_permission (
	id serial4 NOT NULL,
	user_id int4 NOT NULL,
	tag_id int4 NOT NULL,
	CONSTRAINT user_tag_rev_permission_pkey PRIMARY KEY (id),
	CONSTRAINT user_tag_rev_permission_user_id_tag_id_key UNIQUE (user_id, tag_id)
);
CREATE INDEX ix_core_user_tag_rev_permission_id ON core.user_tag_rev_permission USING btree (id);
CREATE INDEX ix_core_user_tag_rev_permission_tag_id ON core.user_tag_rev_permission USING btree (tag_id);
CREATE INDEX ix_core_user_tag_rev_permission_user_id ON core.user_tag_rev_permission USING btree (user_id);


-- core."values" definition

-- Drop table

-- DROP TABLE core."values";

CREATE TABLE core."values" (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_entity_id ON core."values" USING btree (entity_id);
CREATE INDEX values_ts_idx ON core."values" USING btree (ts DESC);


-- core.values_brandoncon definition

-- Drop table

-- DROP TABLE core.values_brandoncon;

CREATE TABLE core.values_brandoncon (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_brandoncon_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_brandoncon_entity_id ON core.values_brandoncon USING btree (entity_id);
CREATE INDEX values_brandoncon_ts_idx ON core.values_brandoncon USING btree (ts DESC);


-- core.values_brandoncon_current definition

-- Drop table

-- DROP TABLE core.values_brandoncon_current;

CREATE TABLE core.values_brandoncon_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_brandoncon_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_values_brandoncon_current_entity_id ON core.values_brandoncon_current USING btree (entity_id);


-- core.values_brandoncon_virtual_points definition

-- Drop table

-- DROP TABLE core.values_brandoncon_virtual_points;

CREATE TABLE core.values_brandoncon_virtual_points (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_brandoncon_virtual_points_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_brandoncon_virtual_points_entity_id ON core.values_brandoncon_virtual_points USING btree (entity_id);
CREATE INDEX values_brandoncon_virtual_points_ts_idx ON core.values_brandoncon_virtual_points USING btree (ts DESC);


-- core.values_coa definition

-- Drop table

-- DROP TABLE core.values_coa;

CREATE TABLE core.values_coa (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_coa_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_coa_entity_id ON core.values_coa USING btree (entity_id);
CREATE INDEX values_coa_ts_idx ON core.values_coa USING btree (ts DESC);


-- core.values_coa_current definition

-- Drop table

-- DROP TABLE core.values_coa_current;

CREATE TABLE core.values_coa_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_coa_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_values_coa_current_entity_id ON core.values_coa_current USING btree (entity_id);


-- core.values_copy_delete definition

-- Drop table

-- DROP TABLE core.values_copy_delete;

CREATE TABLE core.values_copy_delete (
	entity_id int4 NULL,
	ts timestamp NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL
);


-- core.values_current definition

-- Drop table

-- DROP TABLE core.values_current;

CREATE TABLE core.values_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_values_current_entity_id ON core.values_current USING btree (entity_id);


-- core.values_datakwip definition

-- Drop table

-- DROP TABLE core.values_datakwip;

CREATE TABLE core.values_datakwip (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_datakwip_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_datakwip_entity_id ON core.values_datakwip USING btree (entity_id);
CREATE INDEX values_datakwip_ts_idx ON core.values_datakwip USING btree (ts DESC);


-- core.values_datakwip_current definition

-- Drop table

-- DROP TABLE core.values_datakwip_current;

CREATE TABLE core.values_datakwip_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_datakwip_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_values_datakwip_current_entity_id ON core.values_datakwip_current USING btree (entity_id);


-- core.values_datakwip_virtual_points definition

-- Drop table

-- DROP TABLE core.values_datakwip_virtual_points;

CREATE TABLE core.values_datakwip_virtual_points (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_datakwip_virtual_points_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_datakwip_virtual_points_entity_id ON core.values_datakwip_virtual_points USING btree (entity_id);


-- core.values_fend definition

-- Drop table

-- DROP TABLE core.values_fend;

CREATE TABLE core.values_fend (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_fend_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_fend_entity_id ON core.values_fend USING btree (entity_id);
CREATE INDEX values_fend_ts_idx ON core.values_fend USING btree (ts DESC);


-- core.values_fend_current definition

-- Drop table

-- DROP TABLE core.values_fend_current;

CREATE TABLE core.values_fend_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_fend_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_values_fend_current_entity_id ON core.values_fend_current USING btree (entity_id);


-- core.values_fend_virtual_points definition

-- Drop table

-- DROP TABLE core.values_fend_virtual_points;

CREATE TABLE core.values_fend_virtual_points (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_fend_virtual_points_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_fend_virtual_points_entity_id ON core.values_fend_virtual_points USING btree (entity_id);
CREATE INDEX values_fend_virtual_points_ts_idx ON core.values_fend_virtual_points USING btree (ts DESC);


-- core.values_grady definition

-- Drop table

-- DROP TABLE core.values_grady;

CREATE TABLE core.values_grady (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_grady_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_grady_entity_id ON core.values_grady USING btree (entity_id);
CREATE INDEX values_grady_ts_idx ON core.values_grady USING btree (ts DESC);


-- core.values_grady_current definition

-- Drop table

-- DROP TABLE core.values_grady_current;

CREATE TABLE core.values_grady_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_grady_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_values_grady_current_entity_id ON core.values_grady_current USING btree (entity_id);


-- core.values_grady_virtual_points definition

-- Drop table

-- DROP TABLE core.values_grady_virtual_points;

CREATE TABLE core.values_grady_virtual_points (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_grady_virtual_points_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_grady_virtual_points_entity_id ON core.values_grady_virtual_points USING btree (entity_id);


-- core.values_greengen definition

-- Drop table

-- DROP TABLE core.values_greengen;

CREATE TABLE core.values_greengen (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_greengen_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_greengen_entity_id ON core.values_greengen USING btree (entity_id);
CREATE INDEX values_greengen_ts_idx ON core.values_greengen USING btree (ts DESC);


-- core.values_greengen_current definition

-- Drop table

-- DROP TABLE core.values_greengen_current;

CREATE TABLE core.values_greengen_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_greengen_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_values_greengen_current_entity_id ON core.values_greengen_current USING btree (entity_id);


-- core.values_greengen_virtual_points definition

-- Drop table

-- DROP TABLE core.values_greengen_virtual_points;

CREATE TABLE core.values_greengen_virtual_points (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_greengen_virtual_points_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_greengen_virtual_points_entity_id ON core.values_greengen_virtual_points USING btree (entity_id);


-- core.values_hbssolutions definition

-- Drop table

-- DROP TABLE core.values_hbssolutions;

CREATE TABLE core.values_hbssolutions (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_hbssolutions_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_hbssolutions_entity_id ON core.values_hbssolutions USING btree (entity_id);
CREATE INDEX values_hbssolutions_ts_idx ON core.values_hbssolutions USING btree (ts DESC);


-- core.values_hbssolutions_current definition

-- Drop table

-- DROP TABLE core.values_hbssolutions_current;

CREATE TABLE core.values_hbssolutions_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_hbssolutions_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_values_hbssolutions_current_entity_id ON core.values_hbssolutions_current USING btree (entity_id);


-- core.values_hbssolutions_virtual_points definition

-- Drop table

-- DROP TABLE core.values_hbssolutions_virtual_points;

CREATE TABLE core.values_hbssolutions_virtual_points (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_hbssolutions_virtual_points_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_hbssolutions_virtual_points_entity_id ON core.values_hbssolutions_virtual_points USING btree (entity_id);


-- core.values_iris definition

-- Drop table

-- DROP TABLE core.values_iris;

CREATE TABLE core.values_iris (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_iris_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_iris_entity_id ON core.values_iris USING btree (entity_id);
CREATE INDEX values_iris_ts_idx ON core.values_iris USING btree (ts DESC);


-- core.values_iris_current definition

-- Drop table

-- DROP TABLE core.values_iris_current;

CREATE TABLE core.values_iris_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_iris_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_values_iris_current_entity_id ON core.values_iris_current USING btree (entity_id);


-- core.values_modcon definition

-- Drop table

-- DROP TABLE core.values_modcon;

CREATE TABLE core.values_modcon (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_modcon_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_modcon_entity_id ON core.values_modcon USING btree (entity_id);
CREATE INDEX values_modcon_ts_idx ON core.values_modcon USING btree (ts DESC);


-- core.values_modcon_current definition

-- Drop table

-- DROP TABLE core.values_modcon_current;

CREATE TABLE core.values_modcon_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_modcon_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_values_modcon_current_entity_id ON core.values_modcon_current USING btree (entity_id);


-- core.values_modcon_virtual_points definition

-- Drop table

-- DROP TABLE core.values_modcon_virtual_points;

CREATE TABLE core.values_modcon_virtual_points (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_modcon_virtual_points_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_modcon_virtual_points_entity_id ON core.values_modcon_virtual_points USING btree (entity_id);
CREATE INDEX values_modcon_virtual_points_ts_idx ON core.values_modcon_virtual_points USING btree (ts DESC);


-- core.values_sanctuary definition

-- Drop table

-- DROP TABLE core.values_sanctuary;

CREATE TABLE core.values_sanctuary (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_sanctuary_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_sanctuary_entity_id ON core.values_sanctuary USING btree (entity_id);


-- core.values_sanctuary_current definition

-- Drop table

-- DROP TABLE core.values_sanctuary_current;

CREATE TABLE core.values_sanctuary_current (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	value_dict jsonb NULL,
	status varchar NULL,
	CONSTRAINT values_sanctuary_current_pkey PRIMARY KEY (entity_id)
);
CREATE INDEX ix_core_values_sanctuary_current_entity_id ON core.values_sanctuary_current USING btree (entity_id);


-- core.values_virtual_points definition

-- Drop table

-- DROP TABLE core.values_virtual_points;

CREATE TABLE core.values_virtual_points (
	entity_id int4 NOT NULL,
	ts timestamp DEFAULT now() NOT NULL,
	value_n numeric NULL,
	value_b bool NULL,
	value_s varchar NULL,
	value_ts timestamp NULL,
	status varchar NULL,
	CONSTRAINT values_virtual_points_pkey PRIMARY KEY (entity_id, ts)
);
CREATE INDEX ix_core_values_virtual_points_entity_id ON core.values_virtual_points USING btree (entity_id);
CREATE INDEX values_virtual_points_ts_idx ON core.values_virtual_points USING btree (ts DESC);