# -*- coding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, ERP-PLM-CAD Open Source Solution
#    Copyright (C) 2011-2023 https://OmniaSolutions.website
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this prograIf not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 13 Jan 2023

@author: mboscolo
'''



SQL_SUPPORT_FUNCTION="""
/*
REMOVE THE FOLLOWING OBJECT FROM THE DATABASE RELETED TO THE MODULE
ES: psql -U <odoo_user> -d <odoo_database> -c " select remove_all_views("sale")

those are the object that is removed from the module
'ir.actions.server',
'ir.actions.act_window',
'ir.cron',
'ir.ui.view',
'ir.ui.menu',
'ir.model.access'
*/

CREATE OR replace FUNCTION "remove_all_views"(module_name text) RETURNS boolean
    LANGUAGE plpgsql
AS
$$
DECLARE
    TABLE_RECORD RECORD;
    v_table_name text;
    v_model_ref text;
BEGIN
    for TABLE_RECORD IN SELECT id, res_id, model from ir_model_data where module = module_name and model in ('ir.actions.server',
                                                                           'ir.actions.act_window',
                                                                           'ir.cron',
                                                                           'ir.ui.view',
                                                                           'ir.ui.menu',
                                                                           'res.groups',
                                                                           'ir.model.access') order by model, res_id desc
        loop
            v_model_ref = TABLE_RECORD."model";
            v_table_name = replace(v_model_ref,'.','_');
            if v_model_ref='ir.actions.server' then
                v_table_name = 'ir_actions';
            end if;
            if v_model_ref='ir.actions.act_window' then
                v_table_name = 'ir_actions';
            end if;
            if v_model_ref='ir.actions.report' then
                v_table_name = 'ir_actions';
            end if;
            execute format('ALTER TABLE "%s" DISABLE TRIGGER ALL;',v_table_name);
            execute format('delete from "%s" where id=%s;',v_table_name ,TABLE_RECORD."res_id");
            execute format('ALTER TABLE "%s" ENABLE TRIGGER ALL;',v_table_name);
            delete from ir_model_data where id = TABLE_RECORD."id";
        END LOOP;

    RETURN TRUE;
END
$$;

CREATE or replace FUNCTION public.OdooPLMMigrate()
RETURNS int4 AS
$func$
DECLARE
maxIrAttachmentId bigint := (SELECT max(id) FROM ir_attachment);
newIndex bigint;
BEGIN

update mrp_bom_line set source_id = null where source_id in (select id from plm_document where store_fname is null);
update mrp_bom set source_id = null where source_id in (select id from plm_document where store_fname is null);
delete from plm_document where store_fname is null;

delete from plm_document where datas_fname is null;
raise notice '1\12 Begin update ir_attachment id [%] ', maxIrAttachmentId;
alter table IF EXISTS plm_backupdoc drop constraint IF EXISTS  plm_backupdoc_documentid_fkey;
update plm_backupdoc set documentid = documentid + maxIrAttachmentId;
 
alter table IF EXISTS plm_checkout drop constraint IF EXISTS  plm_checkout_documentid;
alter table IF EXISTS plm_checkout drop constraint IF EXISTS plm_checkout_documentid_fkey;
raise notice '2\12 Update PLM checkout';
update plm_checkout set documentid = documentid + maxIrAttachmentId ;
alter table IF EXISTS plm_document_relation rename to ir_attachment_relation;
alter table IF EXISTS ir_attachment_relation drop constraint IF EXISTS plm_document_relation_relation_uniq;
alter table IF EXISTS ir_attachment_relation drop constraint IF EXISTS plm_document_relation_parent_id_fkey;
alter table IF EXISTS ir_attachment_relation drop constraint IF EXISTS plm_document_relation_child_id_fkey;
raise notice '3\12 Update Attachment Relation';
update ir_attachment_relation set child_id = child_id + maxIrAttachmentId, parent_id=parent_id + maxIrAttachmentId;

alter table  IF EXISTS plm_component_document_rel drop constraint IF EXISTS plm_component_document_rel_document_id_fkey;
alter table  IF EXISTS plm_component_document_rel drop constraint IF EXISTS plm_component_document_rel_relation_unique;
raise notice '4\12 Update plm_component_document_rel';
update plm_component_document_rel set document_id = document_id + maxIrAttachmentId;

alter TABLE  IF EXISTS  mrp_bom_line drop constraint IF EXISTS mrp_bom_line_source_id_fkey;
raise notice '5\12 Update mrp_bom_line'; 
update mrp_bom_line set source_id = source_id +  maxIrAttachmentId;

alter table  IF EXISTS  mrp_bom drop constraint IF EXISTS mrp_bom_source_id_fkey;
raise notice '6\12 Update mrp_bom'; 
update mrp_bom set source_id = source_id +   maxIrAttachmentId;

ALTER TABLE ir_attachment ADD COLUMN IF NOT EXISTS engineering_document_name varchar null;
ALTER TABLE ir_attachment ADD COLUMN IF NOT EXISTS revisionid int4 null;
ALTER TABLE ir_attachment ADD COLUMN IF NOT EXISTS writable bool NULL;
ALTER TABLE ir_attachment ADD COLUMN IF NOT EXISTS printout bytea null;
ALTER TABLE ir_attachment ADD COLUMN IF NOT EXISTS preview bytea null;
ALTER TABLE ir_attachment ADD COLUMN IF NOT EXISTS state varchar null;
ALTER TABLE ir_attachment ADD COLUMN IF NOT EXISTS is_plm  bool NULL;
ALTER TABLE ir_attachment ADD COLUMN IF NOT EXISTS used_for_spare bool null;
alter table ir_attachment ADD COLUMN IF NOT EXISTS  old_state varchar null;
alter table ir_attachment ADD COLUMN IF NOT EXISTS  old_plm_id int4 null;

raise notice '7\12 Update ir_attachment'; 
INSERT INTO ir_attachment (id,
old_plm_id,
old_state,
             engineering_document_name,
             revisionid,
             writable,
             printout,
             preview,
             state,
             is_plm,
             create_date,
             res_model,
             write_uid,
             file_size,
             create_uid,
             company_id,
             res_id,
             index_content,
             db_datas,
             store_fname,
             description,
             write_date,
             url,
             type,
             used_for_spare,
             name) 
  (SELECT id + maxIrAttachmentId,
  id,
  state,
    name,
       revisionid,
       writable,
       printout,
       preview,
       state,
       true,
    create_date,
       res_model,
       write_uid,
       file_size,
       create_uid,
       company_id,
       res_id,
       index_content,
       db_datas,
       store_fname,
       description,
       write_date,
       url,
       type,
       usedforspare,
       datas_fname
       FROM plm_document);

raise notice '8\12 Update ir_attachment state';
newIndex := (select setval('ir_attachment_id_seq', (select max(id)+1 from ir_attachment), false));
raise notice '9\12 Assign new index value for ir_attachment %', newIndex; 
raise notice '10\12 Update ir_attachment state'; 
update ir_attachment set type='2D' where position('.e2' in name) >0;
update ir_attachment set type='3D' where position('.e3' in name) >0;
raise notice '11\12 Update mail message'; 
update mail_message set res_id = res_id + maxIrAttachmentId, model = 'ir.attachment' where model = 'plm.document';
ALTER TABLE mail_message ADD COLUMN IF NOT EXISTS  old_write_uid int4 null;
ALTER TABLE mail_message ADD COLUMN IF NOT EXISTS old_write_date timestamp null;
UPDATE mail_message SET old_write_uid = write_uid, old_write_date = write_date;
raise notice '12\12 update product state';

alter table IF EXISTS plm_cad_open drop constraint IF EXISTS plm_cad_open_document_id_fkey;
UPDATE
  plm_cad_open
SET
  document_id=ir_attachment.id
FROM
  ir_attachment
WHERE
  plm_cad_open.document_id=ir_attachment.old_plm_id and old_plm_id is not null ;

alter table IF EXISTS plm_cad_open_bck drop constraint IF EXISTS plm_cad_open_bck_document_id_fkey;
UPDATE
  plm_cad_open_bck
SET
  document_id=ir_attachment.id
FROM
  ir_attachment
WHERE
  plm_cad_open_bck.document_id=ir_attachment.old_plm_id and old_plm_id is not null ;
 
raise notice 'Well Done';  
RETURN 11;
END

$func$ LANGUAGE plpgsql;
"""