import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from glob import glob
import statistics
from scipy import integrate

# Change Directory here, end with / (Windows: change \ to /)
Directory = "Y:/experiments/Experiments_004600/004637/After registration G2/Fully/Control siRNA/6h Lineprofiles orthogonal to Vermicelli/"


def seperation_bulkDNA_local(dataframe):
    df = dataframe
    i=0
    # Testing for Scc1 in Columns (in G2 sample) else Mitotic sample
    if 'Scc1' in df.columns:
        standart = pd.DataFrame()
        standart['Distance'] = df['Distance']
        # z- standartdization
        standart['Scc1'] = (df['Scc1']-df['Scc1'].mean())/df['Scc1'].std()
        standart['f-ara-EdU'] = (df['f-ara-EdU']-df['f-ara-EdU'].mean())/df['f-ara-EdU'].std()
        standart['Hoechst'] = (df['Hoechst']-df['Hoechst'].mean())/df['Hoechst'].std()

        # defiing chromosomal region according to hoechst threshhold
        standart['Chromosome'] = "no"
        # standart['Chromosome_2'] = standart.loc[standart['Hoechst'] > -1] = 'yes'
        standart.loc[standart['Hoechst'] > -1, ['Chromosome']] = 'yes'

        # splitting values over threshhold into consecutive dictionaries
        s = (standart['Chromosome'] == 'yes')
        s = (s.gt(s.shift(fill_value=False)) + 0).cumsum() * s
        grp = {}
        for i in np.unique(s)[1:]:
            grp[i] = standart.loc[s == i, ['Distance', 'Scc1', 'f-ara-EdU', 'Hoechst']]
    else:
        standart = pd.DataFrame()
        standart['Distance'] = df['Distance']
        # z- standartdization
        # standart['Scc1'] = (df['Scc1']-df['Scc1'].mean())/df['Scc1'].std()
        standart['f-ara-EdU'] = (df['f-ara-EdU']-df['f-ara-EdU'].mean())/df['f-ara-EdU'].std()
        standart['Hoechst'] = (df['Hoechst']-df['Hoechst'].mean())/df['Hoechst'].std()

        # defiing chromosomal region according to hoechst threshhold
        standart['Chromosome'] = "no"
        # standart['Chromosome_2'] = standart.loc[standart['Hoechst'] > -1] = 'yes'
        standart.loc[standart['Hoechst'] > -1, ['Chromosome']] = 'yes'

        # splitting values over threshhold into consecutive dictionaries
        s = (standart['Chromosome'] == 'yes')
        s = (s.gt(s.shift(fill_value=False)) + 0).cumsum() * s
        grp = {}
        for i in np.unique(s)[1:]:
            grp[i] = standart.loc[s == i, ['Distance', 'f-ara-EdU', 'Hoechst']]

    # extracting the biggest block over threshhold as Chromosomal mass
    dicts = list(range(1, i+1))
    dicts
    names = {}
    for i in dicts:
        names["Block{0}".format(i)] = [i, len(grp[i])]
    currentDF = pd.DataFrame.from_dict(names, orient='index', columns=['grp_number', 'Length'])
    # Determining largest consecutive block and assuming this one as chromosome
    Chromosome_block = currentDF.loc[currentDF['Length'] == currentDF['Length'].max(), 'grp_number']
    x = int(Chromosome_block)
    chromosome = grp[x]

    # shifting curves above 0
    if (chromosome['f-ara-EdU'].min() < 0):
        chromosome["f-ara-EdU"] = chromosome["f-ara-EdU"] - chromosome['f-ara-EdU'].min()
    if (chromosome['Hoechst'].min() < 0):
        chromosome["Hoechst"] = chromosome["Hoechst"] - chromosome['Hoechst'].min()

    # seperating in left and right sister
    Hoechst_median = statistics.median(chromosome['Distance'])
    left = chromosome.loc[chromosome['Distance'] <= Hoechst_median]
    right = chromosome.loc[chromosome['Distance'] >= Hoechst_median]

    # calculating integrals
    left_Hoechst = integrate.trapz(left['Hoechst'], left['Distance'])
    left_EdU = integrate.trapz(left['f-ara-EdU'], left['Distance'])

    right_Hoechst = integrate.trapz(right['Hoechst'], right['Distance'])
    right_EdU = integrate.trapz(right['f-ara-EdU'], right['Distance'])

    # determining EdU heavy side
    if right_EdU >= left_EdU:
        ratio_EdU = right_EdU/left_EdU
        ratio_Hoechst = right_Hoechst/left_Hoechst
        percentage_EdU = right_EdU/(left_EdU+right_EdU)
        percentage_Hoechst = right_Hoechst/(left_Hoechst+right_Hoechst)
    else:
        ratio_EdU = left_EdU/right_EdU
        ratio_Hoechst = left_Hoechst/right_Hoechst
        percentage_EdU = left_EdU/(left_EdU+right_EdU)
        percentage_Hoechst = left_Hoechst/(left_Hoechst+right_Hoechst)

    results = [left_EdU, right_EdU, ratio_EdU, percentage_EdU, left_Hoechst, right_Hoechst, ratio_Hoechst, percentage_Hoechst]
    return results


#getting files from choosen directory
files_dir = Directory + "**/*.csv"
files = glob(files_dir, recursive=True)

ratios_dict = {}
index = 0
for file in files:
    try:
        ratios_dict[f'{index}'] = [file] + seperation_bulkDNA_local(pd.read_csv(file))
        index += 1
    # skipping files without the requirements in Columns
    except KeyError:
        print(f'{file}was skipped')
    # skipping Datasets where two Hoechst blocks have the same size
    except TypeError:
        print(f'{file}was skipped')
ratios_df = pd.DataFrame.from_dict(ratios_dict, orient='index', columns=['File', 'left_EdU', 'right_EdU', 'ratio_EdU', 'percentage_EdU', 'left_Hoechst', 'right_Hoechst', 'ratio_Hoechst', 'percentage_Hoechst'])
ratios_df.describe()

# saving csv file in chosen directory
Save_dir = Directory + 'bulkDNA_separation.csv'
ratios_df.to_csv(Save_dir)

plt.hist(ratios_df['ratio_Hoechst'], color='b')
plt.hist(ratios_df['ratio_EdU'], color='r')

plt.hist(ratios_df['percentage_Hoechst'], color='b', alpha=0.6)
plt.hist(ratios_df['percentage_EdU'], color='r', alpha=0.6)
