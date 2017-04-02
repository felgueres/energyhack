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
        self.wb_plan = None
        self.names_dict = {}
        self.main_cols = None   #BAD NAME: THIS ARE COLS FROM FIRST IMPORTED FILE FROM CENSUS.
        self.created_features = []
        self.density = None

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

    def _import_density(self):
        '''
        Import Density File
        '''
        self.density = pd.read_csv('../data/00_population/07_Area-and-Populatin-density-by-State-and-Region.csv')

    def _import_gov_expenditure(self):
        '''
        Import Gov. Expenditure data
        '''
        self.gov_capex = pd.read_csv('../data/09_LabourForce/stateregionsexprev.csv')

    def _import_monthlywages(self):
        '''
        Import monthly wages file
        '''
        self.monthly_wages = pd.read_csv('../data/09_LabourForce/monthlywages-ILOMyanmarSurvey2015.csv')

    def _featurize(self):
        '''
        Calls feature functions according to their needs.
        '''
        self._market_features()
        self._access_features()
        self._impact_features()

    '''
    ---------------------------------FEATURES------------------------------------
    '''
    def _market_features(self, demand_per_household = 0.01, usd_per_kw = 6000):
        '''
        Calculate basic demand needs for each

        Inputs
        ------
        demand_per_household = 0.010 kW -- Demand Needs for couple LEDs and Charger
        usd_per_kw = 60 USD -- This a 10 kW system size
        (60 USD / 10 W) * (1000W / kW) = 6,000 USD / kW
        '''
        #TODO: FACTORIZE DRAMATICALLY.

        #Get Demand Columns.
        demand_cols = self.names_dict['08_source_of_light.csv'].tolist()
        demand_cols.extend(self.names_dict['04_male_female_headers.csv'].tolist())
        demand_cols.extend(self.names_dict['03_mean_household_size.csv'].tolist())

        #Index
        demand = self.census.loc[:,demand_cols].rename(columns = self.renamer).copy()

        #Basic Demand Needs Feature, 10 W per Number of Households
        new_col = 'basic_needs_demand_kW'
        self.created_features.append(new_col)
        self.census[new_col] = demand['Conventional_households-Number'] * demand_per_household

        #Create Served Demand Feature
        new_col = 'underserved_HH_Total'
        self.created_features.append(new_col)
        self.census[new_col] = demand.loc[:,['Source_of_lighting-Candle', 'Source_of_lighting-Kerosene']].sum(axis =1)

        #Create Demand Market Size kW
        new_col = 'underserved_mkt_size_kW'
        self.created_features.append(new_col)
        self.census[new_col] = self.census['underserved_HH_Total'] * demand_per_household

        #Create Demand Market Size USD
        new_col = 'underserved_mkt_size_USD'
        self.created_features.append(new_col)
        self.census[new_col] = self.census['underserved_mkt_size_kW'] * usd_per_kw

        #Proportion
        new_col = 'underserved_HH'
        self.created_features.append(new_col)
        self.census[new_col] = self.census['underserved_HH_Total'].divide(demand['Conventional_households-Number'])

        #Population Underserved
        new_col = 'underserved_population'
        self.created_features.append(new_col)
        self.census[new_col] = self.census['underserved_HH_Total'].multiply(demand['Mean_household_size'])

    def _access_features(self):
        '''
        Calculate
        '''
        access_cols = self.names_dict['09_avail_transportation.csv'].tolist()
        access_cols.extend(self.names_dict['04_male_female_headers.csv'].tolist())
        access_cols.extend(self.names_dict['03_mean_household_size.csv'].tolist())
        access_cols.extend(self.names_dict['06_population_by_gender_ratio.csv'].tolist())
        access_cols.extend(self.main_cols)

        access = self.census.loc[:,access_cols].rename(columns = self.renamer).copy()

        #Access_by_car
        new_col = 'car_access_per_HH'
        self.created_features.append(new_col)
        self.census[new_col] = access['Availability_of_transportation_items-Car_Truck_Van'].divide(access['Conventional_households-Number'])

        #Comunication_Phone_Communication
        new_col = 'mobile_phone_per_HH'
        self.created_features.append(new_col)
        self.census[new_col] = access['Availability_of_communication_and_related_amenities-Mobile_phone'].divide(access['Conventional_households-Number'])


        ## THIS SNIPPET RUNS OKAY BUT NOT WORTH INCLUDING SINCE >90% DATA MISSING; TODO: CALCULATE ALTERNATIVE DISTANCE TO GRID
        # #distance2grid:
        # new_col = 'distance2grid'
        # self.created_features.append(new_col)
        # # distance2grid = self.wb_plan.groupby('Township_c').MV_distance_m.mean().to_frame().rename(columns = {'MV_distance_m': 'distance2grid_m'})
        # distance2grid = self.wb_plan.groupby('Township_c').MV_distance_m.mean().to_frame().rename(columns = {'MV_distance_m': 'distance2grid_m'})
        # # self.census[new_col] = self.census.merge(distance2grid, left_index = True, right_index = True, how = 'left')
        # self.census = self.census.merge(distance2grid, left_index=True, right_index=True, how = 'left')

        #Density people per km2
        new_col = 'density_per_km2'
        self.created_features.append(new_col)
        self.census = self.census.merge(self.density.set_index('Pcode').rename(columns = {'den_2014': new_col}), left_on = 'pcode_st', right_index=True, how = 'left')

        #Gov.Metrics
        new_cols = ['gov_expenditure','gov_revenue']
        self.created_features.extend(new_cols)
        self.gov_capex.set_index('pcode_st', inplace = True)
        self.gov_capex.rename(columns = {'exp_total': new_cols[0],'rev_total':new_cols[1]}, inplace = True)
        self.census = self.census.merge(self.gov_capex, left_on ='pcode_st', right_index = True )

        #Income
        new_col = 'income_per_capita_yr'
        self.created_features.append(new_col)
        revenue_generating_workers = ['usuact_10ab_empyr_t', 'usuact_10ab_govemp_m','usuact_10ab_ownacc_t', 'usuact_10ab_priemp_t']
        self.census['active_workers'] = self.census.loc[:, revenue_generating_workers].copy().sum(axis =1)
        self.census[new_col] = self.census.active_workers * self.

    def _impact_features(self):
        '''
        Create social impact figures
        '''

        system_cost = 60 # USD / kW

        impact_cols = self.names_dict['03_mean_household_size.csv'].tolist()
        impact_cols.extend(self.names_dict['04_male_female_headers.csv'].tolist())
        impact_cols.extend(self.names_dict['06_population_by_gender_ratio.csv'].tolist())
        impact_cols.extend(self.main_cols)

        impact = self.census.loc[:,impact_cols].rename(columns = self.renamer).copy()

        #Comunication_Phone_Communication
        new_col = 'access_per_capita_per_usd'
        self.created_features.append(new_col)
        self.census[new_col] = float(system_cost) / impact['Mean_household_size']

    def _solar_features(self):
        '''
        Create solar features.
        '''
        pass

    def _add_columns(self):
        '''
        Use this function to other relevant columns needed from the census df.
        '''

    def _importer(self):
        '''
        Helper to import all files.
        '''
        self._import_WB_plan()
        self._import_keys()
        self._import_density()
        self._import_gov_expenditure()
        self._import_monthlywages()

    def fit(self):
        '''
        Fit to datasets and fit features
        '''
        self._build_census_file()
        self._importer()
        self._featurize()

if __name__ == '__main__':

    a = mdata()
    a.fit()
