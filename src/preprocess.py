import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

class mdata (object):
    '''
    Class to import and process the country's data.
    '''

    def __init__(self):

        #Attributes to hold census and geospatial information.
        self.census = None
        self.census_keys = None
        self.geospatial = None
        self.wb_plan = None
        self.names_dict = {}
        self.main_cols = None
        self.created_features = []

    '''
    -------------------------------LOAD-DATA------------------------------------
    '''

    def _build_census_file(self):
        '''
        Import all census tables at Township level.
        Merge with Township Pcode -- pcode_ts
        '''

        filelist = glob.glob(os.path.join('../data/00_population/01_census/township/','*.csv'))

        reference = 'pcode_ts'

        df = pd.read_csv(filelist[0])
        df.set_index(reference, inplace=True)

        self.main_cols = df.columns.tolist()

        #Capture file columns.
        for file in filelist[1:]:

            df_file = pd.read_csv(file)

            if reference in df_file.columns:
                #set index as township code
                df_file.set_index(reference, inplace = True)
                #get new cols only

                cols2use = df_file.columns.difference(df.columns)

                self.names_dict[os.path.basename(file)] = cols2use

                #merge to main dataframe
                df = df.merge(df_file[cols2use], left_index=True, right_index=True, how = 'left')

            else:
                pass
                # print 'File does not have data at township level: ', file
                # NO DATA TOWNSHIP LEVEL FROM MIGRATION OR RELIGION.

        self.census = df

    def _import_keys(self):
        '''
        Import census keys.
        '''
        self.census_keys = pd.read_csv('../data/00_population/01_census/township/key/00_key_dictionary.csv')

        x = self.census_keys.field_name.tolist()
        y = self.census_keys['description '].tolist()

        #convert to dict
        keys_dict = {}

        for (a,b) in zip(x,y):
            keys_dict[a] = b

        #use this dict to rename cols.
        self.renamer = keys_dict

    def _import_WB_plan(self):
        '''
        Import World Banks' electrification plan.
        '''
        self.wb_plan = pd.read_csv('../data/03_transmission_lines_and_infrastructure/03_geospatial_least_cost_national_electrification_plan.csv')
        #merge to main
        self.census.merge(self.wb_plan.set_index('Township_c'), left_index = True, right_index = True, how ='left')

    def _featurize(self):
        '''
        Calls feature functions according to their needs.
        '''
        self._demand()

    '''
    ---------------------------------FEATURES------------------------------------
    '''
    def _demand(self, demand_per_household = 0.01, ten_wat_cost = 60):
        '''
        Calculate basic demand needs for each

        Inputs
        ------
        demand_per_household = 0.010 kW -- Demand Needs for couple LEDs and Charger
        ten_wat_cost = 60 USD -- This a 10 kW system size
        Market (kW) * (60 USD / 10 W) * (1000W / kW)
        '''

        # Get Demand Columns.
        demand_cols.extend(self.names_dict['08_source_of_light.csv'].tolist())

        # Index
        self.demand = self.census.loc[:,demand_cols].rename(columns = self.renamer).copy()

        # Basic Demand Needs Feature, 10 W per Number of Households
        new_col = 'basic_needs_demand_kW'
        self.created_features.append(new_col)
        self.census[new_col] = self.demand['Conventional_households-Number'] * demand_per_household

        # Create Served Demand Feature
        new_col = 'underserved_HH_Total'
        self.created_features.append(new_col)
        self.census[new_col] = self.demand.loc[:,['Source_of_lighting-Candle', 'Source_of_lighting-Kerosene']]

        # Create Demand Market Size kW
        new_col = 'underserved_mkt_size_kW'
        self.created_features.append(new_col)
        self.census[new_col] = self.census['underserved_HH_Total'] * demand_per_household

        # Create Demand Market Size USD
        new_col = 'underserved_mkt_size_USD'
        self.created_features.append(new_col)
        self.census[new_col] = self.census['underserved_mkt_size_kW'] *



    def _is_electrified(self):
        '''
        Percentage of Population Electrified
        '''




    def fit(self):
        '''
        Fit all preprocess.
        '''
        self._build_census_file()
        self._import_WB_plan()
        self._import_keys()
        self._featurize()

if __name__ == '__main__':

    a = mdata()
    a.fit()
