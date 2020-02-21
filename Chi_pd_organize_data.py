#from zipfile import ZipFile
import os 
import pandas as pd

'''
should update to include web scraping? -get data direct from their GitHub?
Note, currenty no code to grab the context data, before I read it right out of
the chi-pd github folder

need to resolve:
Columns (4,15) have mixed types. Specify dtype option on import or set low_memory=False.
'''
#this is the path to the chicago-police-data GitHub, 
#used to access unified_data.zip and discipline_penalty_codes.csv
#data_path = '/Users/Sarah/Documents/GitHub/chicago-police-data/data'

#Code has been changed so that you can access all of the data from one location
#instences of data_path have been changed to path
#all of the needed data is in my HW5 Repository



#this is the save-to path, this is where the unified_data.zip unzips to
#and where we read the accused, investigators and victims data from (out of the unzipped contents)
#path =  '/Users/Sarah/Documents/GitHub/assignment-4-gillsarah'
path= '/Users/Sarah/Documents/GitHub/Chi_pd_refactor'

#profile_path = 'unified_data/profiles/officer-profiles.csv.gz' #path for reading from chicago-police-data
profile_path = 'fully-unified-data/profiles/officer-profiles.csv.gz'
codes_path = 'context_data/discipline_penalty_codes.csv'
base_path = 'fully-unified-data/complaints/complaints-{}_2000-2016_2016-11.csv.gz'
file_name = ['accused', 'investigators', 'victims']


def pathmaker(base_path, file):
    return base_path.format(file)

#not in use
'''
def unzip(path, filename, save_to_path):
    zf = ZipFile(os.path.join(path, filename), 'r')
    zf.extractall(save_to_path)
    zf.close()
    #cite: https://stackoverflow.com/questions/3451111/unzipping-files-in-python
'''

def read_df(path, filename):
    df = pd.read_csv(os.path.join(path, filename))
    return df


def parse_accused(accused_df):
    accused_df.drop(columns = 'row_id', inplace = True)
    final_dummies = pd.get_dummies(accused_df['final_finding'])
    #recommend_dummies = pd.get_dummies(accused_df['recommended_finding'])
    #cite https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.get_dummies.html
    accused_df['sustained'] = final_dummies['SU']
    #accused_df['recommend_sustain'] = recommend_dummies['SU']
    return accused_df


def parse_investigarots(investigators_df):
    investigators_df.drop(columns = 'row_id', inplace = True)
    investigators_df.rename(columns = {'first_name':'investigator_first_name', 
                                       'last_name':'investigator_last_name',
                                       'middle_initial':'investigator_middle_initial', 
                                       'suffix_name':'investigator_suffix',
                                       'appointed_date': 'date_investigator_appointed', 
                                       'current_star':'investigator_current_star_number',
                                       'current_rank': 'investigator_current_rank', 
                                       'current_unit':'investigator_current_unit'}, inplace = True)
    return investigators_df

def parse_victims(victims_df):
    victims_df.rename(columns = {'gender':'victim_gender', 'age':'victim_age', 
                                 'race':'victim_race'}, inplace = True)
    return victims_df

def parse_profile(profile_df):
    profile_df['org_hire_date'] = pd.to_datetime(profile_df['org_hire_date'], 
                                                 format='%Y-%m-%d')
    #profile_df['birth_year'] = pd.to_datetime(profile_df['birth_year'], format='%Y')
    profile_df['Year_hired'] = profile_df['org_hire_date'].map(lambda d: d.year)
    return profile_df


def merge_dfs(dfs):
    '''
    takes a list of dfs, the order is decided in the list dfs. If you change the order, the function
    may need to be tweeked. The suffixes, and merges 3 and 4
    The frist df is accused, the second is investigators, the third is victims, the third is codes
    '''
    merge_0 = dfs[0].merge(dfs[4], how = 'left', on = 'UID', suffixes = ('_accused', '_profile'))
    merge_1 = merge_0.merge(dfs[1], how = 'inner', on =  "cr_id", suffixes = ('_accused','_investigators'))
    merge_2 = merge_1.merge(dfs[2], how = 'inner', on =  "cr_id")
    merge_3 = merge_2.merge(dfs[3], how = 'left', left_on = 'recommended_discipline', right_on = 'CODE')

    merge_3.drop(columns = 'CODE', inplace = True)
    merge_3.rename(columns={'recommended_discipline': 'recommended_discipline_code',
                            'ACTION_TAKEN'          : 'recommended_discipline'      }, inplace = True)       
    
    merge_4 = merge_3.merge(dfs[3], how = 'left', left_on = 'final_discipline', 
                            right_on = 'CODE',suffixes = ('_recommended_discipline', '_final_discipline'))

    merge_4.drop(columns = 'CODE', inplace = True)

    merge_4.rename(columns={'final_discipline': 'final_discipline_code',
                            'ACTION_TAKEN'    : 'final_discipline'     }, inplace = True) 
    merge_4['count'] = 1 
    return merge_4


#proportion sustained: looking at all complaints filed, one entry per accused individual
#not in use
'''
def total_proportion(accused_df):
    return accused_df['sustained'].sum()/len(accused_df.index)


#proportion sustained of complaints that have a line in victims, investigarots and accused 
def outcome_by_race(df, outcome_word):
    grouped = df.groupby('victim_race').sum()
    grouped[outcome_word]
    grouped['proportion_'+outcome_word] = grouped[outcome_word]/len(df.index)
    df = grouped['proportion_'+outcome_word]

    #print('The proportion of complaints '+outcome_word+', by race of the victim:')
    #print(grouped['proportion_'+outcome_word])
    return df
'''

#also not in use
def complaint_type_outcomes(accused_df, outcome, outcome_word):
    '''
    takes the acccused df, the two letter string for final finding: e.g. 'SU' and a string 
    for the final finding abbreviation meaning (e.g. 'sustained' for 'SU')
    output is a list of the complaint catagories for which the outcome (e.g. 'SU')
    is the most likely final finding
    '''
    crosstab = pd.crosstab(accused_df['final_finding'], accused_df['complaint_category'])
    #cite https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.crosstab.html

    #print('The following complaint catagories are most likely to be ' + outcome_word + ':')
    temp_list = []
    for column in crosstab.columns:
        if crosstab[column].idxmax() == outcome:
            print(column)
            temp_list.append(column)
    #cite: https://stackoverflow.com/questions/15741759/find-maximum-value-of-a-column-and-return-the-corresponding-row-values-using-pan
    df = pd.DataFrame(temp_list, columns = ['complaint catagories most likely to be ' + outcome_word]) 
    #cite: https://www.geeksforgeeks.org/create-a-pandas-dataframe-from-lists/
    return df

#not in use?!
def set_id (df, col_name):
    df = df.assign(id=(df[col_name]).astype('category').cat.codes)
    #cite https://stackoverflow.com/questions/45685254/q-pandas-how-to-efficiently-assign-unique-id-to-individuals-with-multiple-ent
    df.rename(columns = {'id': col_name+'_id'}, inplace = True)
    return df 

#not in use
def check_new_col(df, ref_col, new_col, i_list=[10,14,30,55,108]):
    for i in i_list:
        print(df[ref_col][i], df[new_col][i])

#not in use
def dummy_maker(df, col, new_col_name, value):
    '''
    takes a df, sring col name (col of interest), string new col name (col that will be dummy variable)
    and the value in the col that should be a 1
    returns df with this new col
    '''
    final_dummies = pd.get_dummies(df[col])
    df[new_col_name] = final_dummies[value]
    return df


def export_df(df, path, filename):
    df.to_csv(os.path.join(path, filename))



def main():
    files = []
    for f in file_name:
        files.append(pathmaker(base_path, f))

    #commented out for useing only one data path
    #unzip(data_path, 'unified_data/unified_data.zip', path)

    dfs = []
    for filename in files:
        df = read_df(path, filename)
        if filename.__contains__('accused'):
            dfs.append(parse_accused(df))
        elif filename.__contains__('investigators'):
            dfs.append(parse_investigarots(df))
        elif filename.__contains__('victims'):
            dfs.append(parse_victims(df))
        else:
            print('unexpected file')
    dfs.append(read_df(path, codes_path))
    
    df2 = read_df(path, profile_path)
    dfs.append(parse_profile(df2))

    df = merge_dfs(dfs)

    #proportion = total_proportion(dfs[0])
    #print('Total proportion of complaints that are sustained: {:.4f}'.format(proportion))
    #print(' ')

    #race_df = outcome_by_race(df, 'sustained')


    #outcome_df = complaint_type_outcomes(dfs[0], 'SU', 'sustained')

    export_df(df, path, 'full_df.csv')
    #export_df(race_df, path, 'Proportion of compliants sustained by race.csv')
    #export_df(outcome_df, path, 'Most likely to be sustained.csv')

    return df

df = main()

#needed?? I do need the second df, but whole new fn?
def read_profile(path, profile_path):
    profile_df = read_df(path, profile_path)
    parse_profile(profile_df)
    #already happend in parse_profile
    #profile_df['Year_hired'] = profile_df['org_hire_date'].map(lambda d: d.year)
    profile_df['count'] = 1
    return profile_df

profile_df = read_profile(path, profile_path)

#needed for plot2
def group_by_year(df):
    df2 = df.groupby('Year_hired').sum()
    df2.reset_index(inplace = True)
    return df2