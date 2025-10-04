import os
import csv
import psycopg2
import logging
from datetime import datetime
logger = logging.getLogger(__name__)
class EssUpdater():
    def __init__(self, config):
        self.configService = config
        self.conn = self.connect_to_db()

    def update_ess_data(self):
        print ("started")
        #data = self.read_file("./csv/Enertech_Units_for_Onboarding-220817-Phase_1.csv")
        #self.update_data(data)
        data = self.read_file("./csv/Sense_Device_Onboarding.csv", ";")
        self.update_data(data)
        i = 1


    def clean_address(self, address):
        return address.replace(' ,', ',').replace('TX,', 'TX')
    def read_file(self, file_name, delimeter = ','):
        data = []
        if os.path.exists(file_name):
            with open(file_name) as csvfile:
                data = [
                    {k: v for k, v in row.items()}
                    for row in csv.DictReader(
                        csvfile,
                        delimiter=delimeter,
                        skipinitialspace=True)
                ]
        return data

    def update_data(self,data):
        sql = """select e.id equip_id, p.id property_id, e.name device_name, e."type" device_type, e.model serial_number, p."name" property_name, p.address property_address from "ESS".equipment e, "ESS"."space" s, "ESS".property p  where e.space_ref = s.id and s.property_ref  = p.id and e.model = """
        for equip in data:
            if equip["Serial Number"] == 'M19060303':
                i = 2
            equip_copy = {}
            equip_copy["Property Name"] = equip["Lot/Block/Address Assignment"]
            equip_copy["Serial Number"] = equip["Serial Number"]
            equip_copy["Device Type (Sense or Enertech)"] = "Sense"
            equip_copy["Phase"] = equip["Phase"]
            equip_copy["Device Name"] = "Sense"
            cursor = self.conn.cursor()
            cursor.execute(sql + "'{}'".format(equip_copy["Serial Number"]))
            rows = cursor.fetchall()
            if (len(rows) == 0):
                logger.error("model for {} not found".format(str(equip)))
                self.add_equip(equip_copy)
                continue
            if (len(rows) > 1):
                logger.error("more than 1 row for model for {}".format(str(equip)))
                continue

            model = rows[0]
            model_equip_id = model[0]
            model_property_id = model[1]
            model_device_name = model[2]
            model_device_type = model[3]
            model_serial_number = model[4]
            model_property_name = model[5]
            model_property_address = model[6]
            error_line, flag = self.compare_values(model_device_type, equip_copy["Device Type (Sense or Enertech)"])
            temp_error_line, flag = self.compare_values(model_serial_number, equip_copy["Serial Number"])
            error_line += temp_error_line
            temp_error_line, flag= self.compare_values(model_property_name, equip_copy["Property Name"])
            error_line += temp_error_line
            if ["Property Address"] in list(equip_copy.keys()):
                csv_file_equip_address = self.clean_address(equip_copy["Property Address"])
                temp_error_line, flag = self.compare_values(model_property_address, csv_file_equip_address)
                if not flag:
                    self.update_property_address(model_property_id, csv_file_equip_address)
                error_line += temp_error_line
            if error_line != "":
                logger.error("model {} has errors {}".format(equip["Serial Number"], error_line))
            i = 1
            cursor.close()

    def compare_values(self, source_value, target_value):
        if (source_value != target_value):
           return "{} != {}".format(source_value, target_value), False
        return "", True

    def connect_to_db(self):
        conn = psycopg2.connect(dbname=self.configService.getDbName(),
                                user=self.configService.getDbUsername(),
                                password=self.configService.getDbPassword(),
                                host=self.configService.getDbHost(),
                                port=self.configService.getDbPort())
        return conn

    def update_property_address(self, model_property_id, model_property_address):
        cursor = self.conn.cursor()
        cursor.execute("update \"ESS\".property set address = '{}' where id = {}".format(model_property_address, model_property_id))
        self.conn.commit()
        cursor.close()

    def add_equip(self, equip):
        property_id = self.get_property(equip)
        if property_id != "-1":
            space_id = self.get_space(property_id, equip)
            if space_id == -1:
                space_id = self.add_space(property_id, equip)
        else:
            return
            property_id = self.add_property(equip)
            space_id = self.add_space(property_id, equip)

        cursor = self.conn.cursor()
        cursor.execute(
            "insert into \"ESS\".equipment (name, type, model, space_ref, date_created) values ('{}', '{}', '{}', {}, '{}')".format(
                equip["Device Name"], equip["Device Type (Sense or Enertech)"], equip["Serial Number"], space_id, datetime.now()))
        self.conn.commit()
        cursor.close()


    def get_property(self, equip):
        if equip["Property Name"] == "9836 Evening Canopy Drive":
            return 95
        cursor = self.conn.cursor()
        cursor.execute("select id from \"ESS\".property where name ='{}'".format(equip["Property Name"]))
        rows = cursor.fetchall()
        if (len(rows) == 0):
            logger.error("property for {} not found".format(str(equip)))
            cursor.close()
            return "-1"
        if (len(rows) > 1):
            logger.error("more than 1 row for property for {}".format(str(equip)))
            cursor.close()
            return "-1"
        cursor.close()
        return str(rows[0][0])

    def get_space(self, property_id, equip):
        cursor = self.conn.cursor()
        cursor.execute("select id from \"ESS\".space where property_ref ='{}'".format(property_id))
        rows = cursor.fetchall()
        if (len(rows) == 0):
            logger.error("space for property_id {} not found {}".format(property_id, str(equip)))
            cursor.close()
            return -1
        if (len(rows) > 1):
            logger.error("more than 1 row for property_id {} for {}".format(property_id, str(equip)))
            cursor.close()
            return -1
        cursor.close()
        return rows[0][0]

    def add_property(self, equip):
        cursor = self.conn.cursor()
        lat = equip["Latitude"] if "Latitude" in equip else 0
        long = equip["Longitude"] if "Longitude" in equip else 0
        # Geo Grid 1 = 44, Geo Grid 2 = 45, Phase 1 46 Phase 2 49
        cursor.execute("insert into \"ESS\".property (type, name, num_units, community_ref, address, geo_grid_ref, phase_ref, lat, long) values ('Home', '{}', 1, 16, '{}', 44, 46, {}, {})".format(equip["Property Name"], self.clean_address(equip["Property Address"]), lat, long))
        self.conn.commit()
        cursor.close()
        return self.get_property(equip)

    def add_space(self, property_id, equip):
        cursor = self.conn.cursor()
        cursor.execute(
            "insert into \"ESS\".space (name, property_ref, bedrooms, type) values ('Living Space', {}, 1, 'unit')".format(property_id))
        self.conn.commit()
        cursor.close()
        return self.get_space(property_id, equip)

    def update_property(self):
        print("started")
        data = self.read_file("./csv/WV_-_Phase_1_Lat_Long_Data_-_220729.csv", ";")
        self.update_property_from_file(data)
        #data = self.read_file("./csv/WV_-_Phase_2_Lat_Long_Data_-_220715-v2.csv", ";")
        #self.update_property_from_file(data)
        i = 1

    def get_property_by_id(self, property_id):
        cursor = self.conn.cursor()
        cursor.execute("select id, type, name, num_units, community_ref, address, lat, long, geo_grid_ref, phase_ref, tags from \"ESS\".property where id ={}".format(property_id))
        rows = cursor.fetchall()
        if (len(rows) == 0):
            logger.error("property for {} not found".format(str(property_id)))
            cursor.close()
            return "-1"
        if (len(rows) > 1):
            logger.error("more than 1 row for property for {}".format(str(property_id)))
            cursor.close()
            return "-1"
        cursor.close()
        return rows[0]

    def update_property_long_lat(self, property_id, long, lat):
        cursor = self.conn.cursor()
        cursor.execute("update \"ESS\".property set long = {}, lat = {} where id = {}".format(long, lat, property_id))
        self.conn.commit()
        cursor.close()
    def update_property_from_file(self, data):
        for property in data:
            equip = {}
            equip["Property Name"] = property["\ufeffAddress"]
            equip["Property Address"] = property["\ufeffAddress"]
            equip["Latitude"] = property["Latitude"].replace(",", ".")
            equip["Longitude"] = property["Longitude"].replace(",", ".")
            property_id = self.get_property(equip)
            if property_id > "-1":
                db_property = self.get_property_by_id(property_id)
                if db_property[6] == 0 and db_property[7] == 0:
                    self.update_property_long_lat(property_id, equip["Longitude"] , equip["Latitude"])
                    i = 1
            else:
                logger.info(equip["Property Name"])
                self.add_property(equip)
                i = 2
            i = 1
        
    