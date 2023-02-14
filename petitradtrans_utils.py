import numpy as np
from petitRADTRANS import Radtrans
from petitRADTRANS import nat_cst as nc

import matplotlib.pyplot as plt
from matplotlib import cm
# from importlib import reload

import astropy.units as u
import astropy.constants as const
# import scipy.constants as cst


from molmass import Formula

from starships.analysis import resamp_model
from starships.spectrum import RotKerTransitCloudy

from astropy.table import Table

from collections import OrderedDict
from itertools import product

from pathlib import Path

from astropy.modeling.physical_models import BlackBody as BB


def calc_single_mass(mol):
    if '_' in mol:
        mol = mol.split('_')[0]

    if mol == 'e-':
        single_mass = 0.00054857990888
    else:
        if '-' in mol:
            #             print('-')
            single_mass = Formula(mol[:-1]).mass
        elif '+' in mol:
            #             print('+')
            single_mass = Formula(mol[:-1]).mass
        else:
            single_mass = Formula(mol).mass  # * const.u.cgs  # cst.atomic_mass

    return single_mass


def mass_fraction(mol, vmr, mmw=2.33):
    return calc_single_mass(mol) / mmw * vmr


# def save_models(atmosphere, mod_array, VMRs, mol, R_star, pl_name, path):
#     for i in range(len(mod_array)):
#         file_name = path+pl_name.replace(' ','_')+'_PRT_'+mol+'_VMR_'+str(VMRs[i])
#         np.savez(file_name,
#             wave = nc.c/atmosphere.freq/1e-4,
#             dppm = np.array(mod_array[i])**2/R_star**2,
#             VMR = VMRs)
#         print(file_name)

def gen_atm(species_list, pressures, mode='lbl', wl_range=[0.95, 2.55],
            rayleigh_species=[], continuum_opacities=[], **kwargs):
    atmosphere = Radtrans(line_species=species_list,
                          rayleigh_species=['H2', 'He'] + rayleigh_species,
                          continuum_opacities=['H2-H2', 'H2-He'] + continuum_opacities,
                          wlen_bords_micron=wl_range,
                          mode=mode,
                          **kwargs)

    atmosphere.setup_opa_structure(pressures)

    return atmosphere


def gen_atm_all(species_list, pressures=None, limP=[-12, 4], n_pts=150, indiv=False, **kwargs):
    print(species_list)
    if pressures is None:
        pressures = np.logspace(*limP, n_pts)

    if 'He' in species_list:
        species_list.remove('He')
    if 'H2' in species_list:
        species_list.remove('H2')

    atmos_full = gen_atm(species_list, pressures, **kwargs)

    print('Generating atmosphere with pressures from {} to {}'.format(pressures.max(), pressures.min()))
    if indiv is True:
        atmos_i_list = []
        for specie in species_list:
            mol = specie.split('_')[0]
            print('Generating pure {} atmosphere'.format(mol))
            atm_i = gen_atm([specie], pressures, **kwargs)
            atmos_i_list.append(atm_i)

        return atmos_full, pressures, atmos_i_list
    else:
        print("You are not getting the individual contributions of the species")
        return atmos_full, pressures


def select_mol_list(list_mols, list_values=None, kind_res='low',
                    change_line_list=None, add_line_list=None):
    species_list = OrderedDict({})

    species_linelists = dict()
    species_linelists['high'] = OrderedDict({
        'H2O': 'H2O_main_iso',
        'CO': 'CO_all_iso',
        'CO2': 'CO2_main_iso',
        'FeH': 'FeH_main_iso',
        'C2H2': 'C2H2_main_iso',
        'CH4': 'CH4_main_iso',
        'HCN': 'HCN_main_iso',
        'NH3': 'NH3_main_iso',
        'TiO': 'TiO_all_iso',
        'VO': 'VO',
        'OH': 'OH',  # 'OH_SCARLET',
        'Na': 'Na',
        'K': 'K',
        'H-': 'H-',
        'H': 'H',
        'e-': 'e-',
    })
    species_linelists['low'] = OrderedDict({
        'H2O': 'H2O_HITEMP',
        'CO': 'CO_all_iso_HITEMP',
        'CO2': 'CO2',
        'FeH': 'FeH',
        'C2H2': 'C2H2',
        'CH4': 'CH4',
        'HCN': 'HCN',
        'NH3': 'NH3',
        'TiO': 'TiO_all_Exomol',
        'VO': 'VO',
        'OH': 'OH',
        'Na': 'Na_allard',
        'K': 'K_allard',
        'H-': 'H-',
        'H': 'H',
        'e-': 'e-',

    })

    if add_line_list is not None:
        print('Adding')
        for added_mol in add_line_list:
            print(added_mol[0], ' as ', added_mol[1])
            species_linelists[kind_res][added_mol[0]] = added_mol[1]

    if change_line_list is not None:
        for changed_mol in change_line_list:
            species_linelists[kind_res][changed_mol[0]] = changed_mol[1]

    for i_mol, mol in enumerate(list_mols):
        if list_values is None:
            species_list[species_linelists[kind_res][mol]] = [1e-99]
        else:
            species_list[species_linelists[kind_res][mol]] = list_values[i_mol]

    return species_list


# def select_mol_list(list_mols, list_values=None, kind_res='low', 
#                     change_line_list=None, add_line_list=[]):

#     species_list = OrderedDict({})

#     if kind_res == 'high':
#         master_list_mol = ['H2O_main_iso','CO_all_iso','CO2_main_iso','FeH_main_iso',
#                    'C2H2_main_iso','CH4_main_iso','HCN_main_iso','NH3_main_iso',
#                    'TiO_all_iso','VO','OH_SCARLET','Na','K','H-','H','e-']+add_line_list

#     elif kind_res == 'low':
#         master_list_mol = ['H2O_HITEMP','CO_all_iso_HITEMP','CO2','FeH',
#                            'C2H2', 'CH4', 'HCN', 'NH3',
#                            'TiO_all_Exomol','VO','OH','Na_allard','K_allard','H-','H','e-']+add_line_list


#     # If someone wants to change the default line_list:
#     # Ex: change_line_list = ['TiO_all_Plez']
#     if change_line_list is not None:
#         for change_ll in change_line_list:
#             change_mol = change_ll.split('_')[0]
#             for mol_i, master_mol in enumerate(master_list_mol):
#                 if np.nonzero(change_mol in master_mol)[0].size > 0:
#                     if change_mol == master_mol:
#                         master_list_mol[mol_i] = change_ll
#                     else:
#                         if np.nonzero(change_mol+'_' in master_mol)[0].size > 0:
#                             master_list_mol[mol_i] = change_ll


#     for i_mol, mol in enumerate(list_mols):
#         for master_mol in master_list_mol:
#             if np.nonzero(mol in master_mol)[0].size > 0:
#                 if mol == master_mol:
#                     if list_values is None:
#                         species_list[master_mol] = [1e-99]
#                     else:
#                         species_list[master_mol] = list_values[i_mol]
# #                     if mol == "H-":

#                 else:
#                     if np.nonzero(mol+'_' in master_mol)[0].size > 0:
#                         if list_values is None:
#                             species_list[master_mol] = [1e-99]
#                         else:
#                             species_list[master_mol] = list_values[i_mol]

#     return species_list


## thermal dissociation functions
# Eq 2, Parmentier et al. 2018
def Ad(P, T, alpha, beta, gamma):
    logAd = (alpha * np.log10(P)) + (beta / T) - gamma
    return 10 ** logAd


# Eq 1, Parmentier et al. 2018
def A(A0, Ad):
    A = ((1 / np.sqrt(A0)) + (1 / np.sqrt(Ad))) ** (-2.)
    return A


def association_profile(P, T, A_0, alpha, beta, gamma, A_0_ref):
    '''
    A_0: VMR without dissociation
    alpha, beta, gamma free parameters
    '''
    # Dissociated Abundance
    log_A_shift = np.log10(A_0 / A_0_ref)
    A_d = 10 ** (log_A_shift - gamma) * P ** alpha * 10 ** (beta / T)

    # Combine dissociated abundance with original abundance
    return (A_0 ** 2 + A_d ** 2) ** (0.5)


def diss_profile(P, T, A_0, alpha, beta, gamma, A_0_ref):
    '''
    A_0: VMR without dissociation
    alpha, beta, gamma free parameters
    '''
    # Dissociated Abundance
    log_A_shift = np.log10(A_0 / A_0_ref)
    A_d = 10 ** (log_A_shift - gamma) * P ** alpha * 10 ** (beta / T)

    # Combine dissociated abundance with original abundance
    return ((1 / A_0) ** 0.5 + (1 / A_d) ** 0.5) ** (-2)


# Equation to set the dissociated abundance profile to qmol_lay and add the difference as H2
def update_dissociation_abundance_profile(profile, specie_name, pressures, temperatures,
                                          A0, alpha, beta, gamma, A0_ref, scale=1.0):
    # dissociation abundance profile
    #     profile_updt = A(A0,Ad(pressures,temperatures, alpha,beta,gamma))
    profile_updt = diss_profile(pressures, temperatures, A0, alpha, beta, gamma, A0_ref)
    # set abundance profile
    profile[specie_name] = profile_updt
    # add what is removed as H2
    #     if specie_name != 'H2':
    #         profile['H2'] += (A0 - profile_updt)
    if specie_name == 'H2':
        try:
            profile['H'] += (A0 - profile_updt) * scale
        except KeyError:
            print("You must add H- to your species")
    if (specie_name.split('_')[0] == 'H2O'):
        #         profile['OH_SCARLET'] += (A0 - profile_updt)*scale
        #     if specie_name == 'H2O_HITEMP':
        profile['OH'] += (A0 - profile_updt) * scale


def calc_MMW3(abundances):
    # MMW = np.zeros_like(abundances[abundances.keys()[0]])
    for i, key in enumerate(abundances.keys()):
        mol = key.split('_')[0]
        if i == 0:
            MMW = np.zeros_like(abundances[key])
        #         print(abundances[key], prt.calc_single_mass(mol))
        MMW += abundances[key] * calc_single_mass(mol)
    #         print(MMW)
    return MMW


def gen_abundances(species_list, VMRs, pressures, temperatures, verbose=False,
                   vmrh2he=[0.85, 0.15], dissociation=False, scale=1.0, plot=False):  # , MMW=2.33):
    abundances = {}
    profile = {}

    species = []
    for specie, vmr in zip(species_list, VMRs):
        mol = specie.split('_')[0]
        #         print(mol)
        species.append(mol)

    if 'H2' not in species_list:
        if verbose:
            print('add H2')
        VMRs_H2 = vmrh2he[0] * (1 - np.array(VMRs).sum())
        species.append('H2')
        species_list.append('H2')
        VMRs.append(VMRs_H2)
    #         print(species, species_list, VMRs)

    if 'He' not in species_list:
        if verbose:
            print('add He')
        if 'H2' in species_list:
            VMRs_He = (1 - np.array(VMRs).sum())
        #             print('H2 in species', VMRs_He, np.array(VMRs).sum(), VMRs)
        else:
            VMRs_He = vmrh2he[1] * (1 - np.array(VMRs).sum())
        #             print('H2 not in species', VMRs_He)
        #         VMRs_He = vmrh2he[1]*(1-np.array(VMRs).sum())
        species.append('He')
        species_list.append('He')
        VMRs.append(VMRs_He)
        #         print(VMRs_He)
        profile['He'] = VMRs_He * np.ones_like(pressures)

    #     if verbose is True:
    #         print(species, VMRs)

    #     MMW = prt.calc_MMW(species, VMRs)
    #     if verbose is True:
    #         print('MMW = {}'.format(MMW))

    #     # if custom_VMRs is None:
    for specie_name, vmr in zip(species_list, VMRs):
        if verbose:
            print(specie_name, vmr)

        profile[specie_name] = vmr * np.ones_like(pressures)

    if ('H-' in species_list) and ('H' not in species_list):
        print('adding H')
        profile['H'] = 1e-99 * np.ones_like(pressures)
        species_list.append('H')
        species.append('H')
        VMRs.append(1e-99)
    if ('H-' in species_list) and ('e-' not in species_list):
        print('adding e-')
        profile['e-'] = 1e-6 * np.ones_like(pressures)
        species_list.append('e-')
        species.append('e-')
        VMRs.append(1e-6)

    #     print(species_list, VMRs)

    if dissociation:
        for MolName, mol, vmr in zip(species_list, species, VMRs):
            #             print(MolName, vmr)
            # if H2O, VO, TiO, H-, Na, K, use dissociation profiles
            # values from Table 1 of Parmentier et al. 2018
            if mol == 'H2':
                #                 print('H2', i, VMRs[i])
                update_dissociation_abundance_profile(profile, MolName, pressures, temperatures,
                                                      vmr, *[1.0, 2.41 * 1e4, 6.5, 10 ** (-0.1)])
            if mol == 'H2O':
                #                 print('H2O', VMRs[i], i)
                update_dissociation_abundance_profile(profile, MolName, pressures, temperatures,
                                                      vmr, *[2.0, 4.83 * 1e4, 15.9, 10 ** (-3.3)], scale=scale)
            elif mol == 'TiO':
                update_dissociation_abundance_profile(profile, MolName, pressures, temperatures,
                                                      vmr, *[1.6, 5.94 * 1e4, 23.0, 10 ** (-7.1)])
            elif mol == 'VO':
                update_dissociation_abundance_profile(profile, MolName, pressures, temperatures,
                                                      vmr, *[1.5, 5.40 * 1e4, 23.8, 10 ** (-9.2)])
            elif mol == 'H-':
                update_dissociation_abundance_profile(profile, MolName, pressures, temperatures,
                                                      vmr, *[0.6, -0.14 * 1e4, 7.7, 10 ** (-8.3)])
            elif mol == 'Na':
                update_dissociation_abundance_profile(profile, MolName, pressures, temperatures,
                                                      vmr, *[0.6, 1.89 * 1e4, 12.2, 10 ** (-5.5)])
            elif mol == 'K':
                update_dissociation_abundance_profile(profile, MolName, pressures, temperatures,
                                                      vmr, *[0.6, 1.28 * 1e4, 12.7, 10 ** (-7.1)])
            elif mol == 'e-':
                update_dissociation_abundance_profile(profile, MolName, pressures, temperatures,
                                                      vmr, *[-0.4, 2.5 * 1e-4, 6.5, 10 ** (-6.0)])

    MMW = calc_MMW3(profile)

    if plot:
        cmap = cm.get_cmap('tab20')
        plt.figure()
        for i, key in enumerate(profile.keys()):
            #             print(key)
            plt.plot(np.log10(profile[key]), np.log10(pressures), label=key, color=cmap.colors[i])
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.ylim(2, -6)
        plt.xlim(-12, 1)

    for mol, specie_name in zip(species, species_list):
        abundances[specie_name] = mass_fraction(mol, profile[specie_name], mmw=MMW)

    #     print(abundances.keys())
    #     if custom_VMRs is None:
    #         for mol, specie_name, vmr in zip(species, species_list, VMRs):
    # #             print(mol, vmr)
    # #             mol = specie.split('_')[0]
    #             abundances[specie_name] = mass_fraction(mol, vmr, MMW=MMW) * np.ones_like(temperature)
    #     else:
    #         for specie in custom_VMRs.keys():
    #             abundances[specie_name] = mass_fraction(mol, custom_VMRs[mol], MMW=MMW)

    #     if plot:
    #         plt.figure()
    #         for i,key in enumerate(abundances.keys()):
    # #             print(key)
    #             plt.plot(np.log10(abundances[key]),np.log10(pressures), label=key)
    #         plt.legend()
    #         plt.ylim(2,-6)
    #         plt.xlim(-12,1)

    return abundances, MMW


# def gen_abundances(species_list, VMRs, temperature, custom_VMRs=None, verbose=True,
#                    vmrh2he = [0.85,0.15]): #, MMW=2.33):
#     abundances = {}

#     species = []
#     for specie,vmr in zip(species_list, VMRs):
#         mol = specie.split('_')[0]
# #         print(mol)
#         species.append(mol)

#     if 'H2' not in species_list: 
#         VMRs_H2 = vmrh2he[0]*(1-np.array(VMRs).sum())
#         species.append('H2')
#         species_list.append('H2')
#     if 'He' not in species_list: 
#         VMRs_He = vmrh2he[1]*(1-np.array(VMRs).sum())
#         species.append('He')
#         species_list.append('He')
#     VMRs.append(VMRs_H2)
#     VMRs.append(VMRs_He)

#     if verbose is True:
#         print(species, VMRs)

#     MMW = calc_MMW(species, VMRs)
#     if verbose is True:
#         print('MMW = {}'.format(MMW))

#     if custom_VMRs is None:
#         for mol, specie_name, vmr in zip(species, species_list, VMRs):
# #             print(mol, vmr)
# #             mol = specie.split('_')[0]
#             abundances[specie_name] = mass_fraction(mol, vmr, MMW=MMW) * np.ones_like(temperature)
#     else:
#         for specie in custom_VMRs.keys():
#             abundances[specie_name] = mass_fraction(mol, custom_VMRs[mol], MMW=MMW)
# #     abund_sum = 0
# #     for mol in abundances.keys():
# #         abund_sum += VMRs[0]

# #     if 'H2' not in species_list:      
# #         abundances['H2'] = 0.75*(1-np.array(VMRs).sum()) * np.ones_like(temperature)
# #     if 'He' not in species_list: 
# #         abundances['He'] = 0.25*(1-np.array(VMRs).sum()) * np.ones_like(temperature)

# #     print('Calculated abundances for {}'.format(abundances.keys()))
# #     somme = 0
# #     for mol in abundances.keys():
# #         print('Calculated abundances for {} =  {}'.format(mol, abundances[mol][0]))
# #         somme += abundances[mol][0]
# #     print(somme)
# #     print(abundances.keys())
#     return abundances, MMW


def calc_MMW2(abundances):
    MMW = 0.
    for key in abundances.keys():
        mol = key.split('_')[0]
        MMW += abundances[key] / calc_single_mass(mol)

    return 1. / MMW


def calc_MMW(species, VMRs):
    MMW = 0.
    for specie, vmr in zip(species, VMRs):
        mol = specie
        MMW += calc_single_mass(mol) * vmr
    #         print(MMW)
    return MMW


# def calc_full_spectrum(atmos_full, atmos_i, pressures, planet, species_list, VMRs,
#                        P0=0.0001, MMW=2.33, haze=None, cloud=None, path=None):

#     temperature = planet.Tp.value * np.ones_like(pressures)
#     R_pl = planet.R_pl.cgs.value
#     gravity = planet.gp.decompose().cgs.value
#     R_star = planet.R_star.cgs.value
#     MMW *= np.ones_like(temperature)

#     file_name = planet.name.replace(' ','_')+'_PRT'
#     params = {}
#     kwargs = {}
#     if haze is not None:
#         kwargs['haze_factor'] = haze
#     if cloud is not None:
#         kwargs['Pcloud'] = 10**(cloud)

#     abundances = gen_abundances(species_list, VMRs, temperature)
#     print('Calculating full transmission spectrum')
#     atmos_full.calc_transm(temperature, abundances, gravity, MMW, R_pl=R_pl, P0_bar=P0, **kwargs)

#     wave = nc.c/atmos_full.freq/1e-4
#     atmos_full_ts = atmos_full.transm_rad**2/R_star**2

#     atmos_i_ts = []
#     mols = []
#     for specie, vmr, atm_i in zip(species_list, VMRs, atmos_i):
#         mol = specie.split('_')[0]
#         abundances = gen_abundances([specie], [vmr], temperature)
#         print('Calculating pure {} transmission spectrum'.format(mol))
#         atm_i.calc_transm(temperature, abundances, gravity, MMW, R_pl=R_pl, P0_bar=P0, **kwargs)
#         atmos_i_ts.append(atm_i.transm_rad**2/R_star**2)
#         params['VMR_'+mol] = vmr
#         mols.append('dppm[{}]'.format(mol))
#         file_name += '_{}{:.2f}'.format(mol,vmr)

#     print('Done!')
#     params['haze'] = haze
#     params['cloud'] = cloud
#     params['P0'] = P0
#     params['MMW'] = MMW[0]
#     params['pressures'] = pressures
#     params['temperature'] = temperature
#     params['R_pl'] = R_pl
#     params['name'] = planet.name
#     params['gravity'] = gravity
#     params['R_star'] = R_star

#     spec = Table([wave, atmos_full_ts, *atmos_i_ts], names=('wave','dppm',*mols), meta=params)

#     if path is not None:
#         file_name= path+ file_name
#         if haze is not None:
#             file_name += '_haze{:.1f}'.format(haze)
#         if cloud is not None:
#             file_name += '_cloud{:.1f}'.format(cloud)

#         spec.write(file_name+".ecsv", delimiter=",")
#     else:
#         return spec


def calc_multi_full_spectrum(planet, species, atmos_full=None, pressures=None, T=None, temperature=None,
                             P0=1, haze=None, cloud=None, contribution=False, custom_VMRs=None,  # MMW=2.33,
                             path=None, rp=None, rstar=None, kind_trans='transmission', filetag='', plot=False,
                             kappa_zero=None, kappa_factor=None, gamma_scat=None, vmrh2he=[0.85, 0.15],
                             verbose=False, dissociation=False, fct_star=None, plot_abundance=False):
    if path is not None:
        print('Checking if path exists...')
        my_file = Path(path)
        if my_file.is_dir():
            print('Yes it does!')
        else:
            print('No it doesnt, but it is being created :')
            print(path)
            my_file.mkdir()
    if filetag != '':
        filetag = '_' + filetag
    if verbose:
        print(species.keys())
    file_name0 = planet.name.replace(' ', '_')
    # --- If the atmosphere object doesn't exists, it creates it
    if atmos_full is None:
        atmos_full, pressures = gen_atm_all([*species.keys()])

    # --- If T isn't given, it takes the equil temp of the planet
    if T is None:
        T = planet.Tp.value
    # --- If no temprature profile is provided, it assumes an isothermal profile
    if temperature is None:
        temperature = T * np.ones_like(pressures)
        temp_type = 'iso'
    else:
        temp_type = 'tp'

    #     plt.plot(temperature, np.log10(pressures))

    if rp is None:
        R_pl = planet.R_pl.cgs.value
    else:
        R_pl = rp.cgs.value

    if R_pl.ndim >0:
        R_pl = R_pl[0]

    gravity = (const.G * planet.M_pl / R_pl ** 2).cgs.value
    if rstar is None:
        R_star = planet.R_star.cgs.value
    else:
        R_star = rstar.cgs.value
    print('R_pl = {} // R_star = {} // grav = {}'.format(R_pl * u.cm.to(u.R_jup),
                                                         R_star * u.cm.to(u.R_sun),
                                                         gravity * u.cm ** 2 / u.s))

    # --- Testing all combinations of all the given parameters
    combinations = list(product(*species.values()))
    print('There will be {} files'.format(len(combinations)))

    wave = None
    spectra_list = []
    for j, combi in enumerate(combinations):

        file_name = file_name0

        for i, k in enumerate(species.keys()):
            mol = k.split('_')[0]
            file_name += '_{}{}'.format(mol, combi[i])
            if verbose:
                print('VMR_{} = {}'.format(mol, combi[i]))

        if temp_type == 'iso':
            file_name += '_Tiso{}K'.format(T)
        else:
            file_name += '_TP{}K'.format(T)

        kwargs = {}
        if haze is not None:
            kwargs['haze_factor'] = haze
        # if (cloud is not None) or (cloud != -99):
        #     kwargs['Pcloud'] = cloud
        if gamma_scat is not None:
            kwargs['gamma_scat'] = gamma_scat
        if kappa_zero is not None:
            kwargs['kappa_zero'] = kappa_zero
        if kappa_factor is not None:
            kwargs['kappa_factor'] = kappa_factor #* (5.31e-31 * u.m ** 2 / u.u).cgs.value

        print('Calculating full {} spectrum {}/{}'.format(kind_trans, j + 1, len(combinations)))
        # species.values = combi

        for i, mol_i in enumerate(species.keys()):
            #         print(list_mols[i],10**params[i])
            species[mol_i] = combi[i]

        wave, atmos_full_spectrum = retrieval_model_plain(atmos_full, species,
                                                          planet, pressures, temperature,
                                                          gravity, P0, cloud, R_pl, R_star,
                                                          vmrh2he=vmrh2he, kind_trans=kind_trans,
                                                          dissociation=dissociation, fct_star=fct_star,
                                                          plot_abundance=plot_abundance,
                                                          contribution=contribution,
                                                          **kwargs)
        if kind_trans == 'transmission':
            atmos_full_spectrum = atmos_full_spectrum * 1e6  # to put in ppm

        # #         print('Previous MMW = {}'.format(MMW))
        # abundances, MMW = gen_abundances([*species.keys()], [*c], pressures, temperature,
        #                                  verbose=verbose, vmrh2he=vmrh2he,
        #                                  dissociation=dissociation, plot=plot_abundance)  # , MMW=MMW)
        # # --- Calculating a more precise MMW
        # #         MMW2 = calc_MMW2(abundances)
        # #         print('MMW2 = {}, MMM3 = {}'.format(MMW2, MMW))
        #
        # #         print(abundances.keys(), MMW)
        #
        # if kind_trans == 'transmission':
        #     print('Calculating full transmission spectrum {}/{}'.format(j + 1, len(combinations)))
        #     atmos_full.calc_transm(temperature, abundances, gravity, MMW, R_pl=R_pl, P0_bar=P0,
        #                            contribution=contribution, **kwargs)
        # elif kind_trans == 'emission':
        #     print('Calculating full emission spectrum {}/{}'.format(j + 1, len(combinations)))
        #     atmos_full.calc_flux(temperature, abundances, gravity, MMW,
        #                          contribution=contribution, **kwargs)
        # #             print(temperature, abundances, gravity, MMW, kwargs)
        # #             print(atmos_full.flux)
        # if wave is None:
        #     wave = nc.c / atmos_full.freq / 1e-4
        #
        # if kind_trans == 'transmission':
        #     atmos_full_spectrum = atmos_full.transm_rad ** 2 / R_star ** 2 * 1e6  # to put in ppm
        # elif kind_trans == 'emission':
        #     if fct_star is None:
        #         bb_mod = BB(planet.Teff)
        #         # -- Converting u.erg/u.cm**2/u.s/u.Hz to u.erg/u.cm**2/u.s/u.cm
        #         star_spectrum = (bb_mod(wave * u.um) * np.pi * u.sr * const.c / (wave * u.um) ** 2).to(
        #             u.erg / u.cm ** 2 / u.s / u.cm)
        #     else:
        #         star_spectrum = fct_star(wave) * (u.erg / u.cm ** 2 / u.s / u.cm)
        #
        #     atmos_full_spectrum = (atmos_full.flux * (u.erg / u.cm ** 2 / u.s / u.Hz) *
        #                            const.c / (wave * u.um) ** 2).to(u.erg / u.cm ** 2 / u.s / u.cm) * \
        #                           R_pl ** 2 / R_star ** 2 / star_spectrum

        if plot is True:
            plt.figure()
            plt.plot(wave, atmos_full_spectrum)
        print(wave[[0, -1]], atmos_full_spectrum[[0, -1]])
        if np.isnan(atmos_full_spectrum).all():
            print('ITS ALL NANs... Something is wrong.')
        if contribution is True:
            wlen_mu = nc.c / atmos_full.freq / 1e-4
            X, Y = np.meshgrid(wlen_mu, pressures)
            if kind_trans == 'transmission':
                plt.contourf(X, Y, atmos_full.contr_tr, 30, cmap=plt.cm.bone_r)
                plt.title('Transmission contribution function')
            elif kind_trans == 'emission':
                plt.contourf(X, Y, atmos_full.contr_em, 30, cmap=plt.cm.bone_r)
                plt.title('Emission contribution function')

            plt.yscale('log')
            plt.xscale('log')
            plt.ylim([1e2, 1e-6])
            plt.xlim([np.min(wlen_mu), np.max(wlen_mu)])

            plt.xlabel('Wavelength (microns)')
            plt.ylabel('P (bar)')

            plt.show()
            plt.clf()

        if haze is not None:
            file_name += '_haze{:.1f}'.format(haze)
        if cloud is not None:
            file_name += '_cloud{:.2f}'.format(cloud * u.bar.to(u.Pa))

        if rp is not None:
            print((R_pl * u.cm).to(u.R_jup).value)
            file_name += '_Rp{:.2f}'.format((R_pl * u.cm).to(u.R_jup).value)
        if path is not None:
            print('Saving...')
            np.save(path + 'PRT_' + file_name + '_' + kind_trans + filetag, atmos_full_spectrum)
            del atmos_full_spectrum
            if j == 0:
                np.save(path + 'PRT_' + planet.name.replace(' ', '_') + '_Spectrum_wave', wave)
                print('Wave : ', 'PRT_' + planet.name.replace(' ', '_') + '_Spectrum_wave')

            print('Flux : ', 'PRT_' + file_name + '_' + kind_trans + filetag)
        else:
            # wave = nc.c / atmos_full.freq / 1e-4
            spectra_list.append(atmos_full_spectrum)
            print('{}/{} Done!'.format(j + 1, len(combinations)))
    if path is None:
        return atmos_full, wave, spectra_list


def gen_cases_file(planet, temps, cloudTop, haze, P0, MMW, R_pl, species, cases_name='',
                   path0=None, temperature=None, kind='transmission', filetag='', ):
    if kind != '':
        kind = '_' + kind
    if filetag != '':
        filetag = '_' + filetag

    if path0 is None:
        path = '/home/boucher/spirou/planetModels/' + planet.name.replace(' ', '_') + '/'
    else:
        path = path0
    combinations = list(product(*species.values(), temps, cloudTop, haze, P0, MMW, R_pl))

    cases = []
    names_col = []
    for k in species.keys():
        names_col.append(k.split('_')[0])
    names_col += ['Tmid', 'pCloud', 'haze', 'P0', 'MMW', 'R_pl', 'filename']

    for i, c in enumerate(combinations):

        case_i = []
        species_name = []
        VMRs = []
        filename = planet.name.replace(' ', '_')
        for j, k in enumerate(species.keys()):
            mol = k.split('_')[0]
            #             print(mol,c[j])
            #             print('_{}{}'.format(mol,c[j]))
            filename += '_{}{}'.format(mol, c[j])
            case_i.append(c[j])
            species_name.append(mol)
            VMRs.append(c[j])

        VMRs_H2 = 0.75 * (1 - np.array(VMRs).sum())
        VMRs_He = 0.25 * (1 - np.array(VMRs).sum())
        species_name.append('H2')
        species_name.append('He')
        VMRs.append(VMRs_H2)
        VMRs.append(VMRs_He)

        MMW = calc_MMW(species_name, VMRs)
        #         print(MMW)
        #         c[j+1+4] = MMW
        #         for i,k in enumerate(species.keys()):
        #             mol = k.split('_')[0]
        #             file_name += '_{}{:.1f}'.format(mol,c[i])
        #             print('VMR_{} = {}'.format(mol, c[i]))

        case_i += [c[j + 1 + 0], c[j + 1 + 1] * u.bar.to(u.Pa), c[j + 1 + 2], c[j + 1 + 3], MMW,
                   c[-1].to(u.R_jup).value]

        if temperature is None:
            filename += '_Tiso{}K'.format(c[j + 1 + 0])
        else:
            filename += '_TP{}K'.format(c[j + 1 + 0])

        if haze[0] is not None:
            filename += '_haze{:.1f}'.format(c[j + 1 + 2])
        if c[1] is not None:
            filename += '_cloud{:.2f}'.format(c[j + 1 + 1] * u.bar.to(u.Pa))
        if c[-1] is not None:
            filename += '_Rp{:.2f}'.format(c[-1].to(u.R_jup).value)
        case_i.append('PRT_' + filename + kind + filetag + '.npy')

        cases.append(case_i)

    cases2 = Table(rows=cases, names=names_col)

    if path0 is not None:
        cases2.write(path + 'PRT_CasesTable' + cases_name + '.ecsv',  # '/PRT_CasesTable.csv'
                     delimiter=",", overwrite=True)
        print(path + 'PRT_CasesTable' + cases_name + '.ecsv')
    else:
        return cases2

    # def gen_cases_file(planet, temps, cloudTop, haze, P0, MMW, species,


#                    path=None, temperature=None, kind='transmission', filetag=''):
#     if path is None:
#         path = '/home/boucher/spirou/planetModels/'+pl_name.replace(' ','_')+'/'
#     combinations = list(product(*species.values(),temps, cloudTop, haze, P0, MMW))

#     cases = []
#     names_col = []
#     for k in species.keys():
#         names_col.append(k.split('_')[0])
#     names_col += ['Tmid', 'pCloud', 'haze', 'P0','MMW','filename']
# #     names_col.append()

#     for i,c in enumerate(combinations):

#         case_i = []
#         for j,k in enumerate(species.keys()):
#             mol = k.split('_')[0]
# #             filename += '_{}{:.2f}'.format(mol,c[j]) 
#             case_i.append(c[j])

#         case_i += [c[j+1+0], c[j+1+1], c[j+1+2], c[j+1+3], c[j+1+4]]

# #         filename = planet.name.replace(' ','_')+'_Tiso{}K'.format(c[0])

#         if temperature is None:
# #             file_name0 += '_Tiso{}K'.format(T)
#             filename = planet.name.replace(' ','_')+'_Tiso{}K'.format(c[j+1+0])

#         else:
# #             file_name0 += '_TP'
#             filename = planet.name.replace(' ','_')+'_TP'


#         for j,k in enumerate(species.keys()):
#             mol = k.split('_')[0]
#             filename += '_{}{:.2f}'.format(mol,c[j]) 
# #             case_i.append(c[j+5])

#         if haze[0] is not None:
#             filename += '_haze{:.1f}'.format(c[j+1+2])
#         if c[1] is not None:
#             filename += '_cloud{}'.format(np.log10(c[j+1+1]))

#         case_i.append('PRT_' + filename + '_' + kind + filetag + '.npy')

#         cases.append(case_i)

#     cases2 = Table(rows = cases, names=names_col)

#     if path is not None:
#         cases2.write(path+'PRT_CasesTable.ecsv', #'/PRT_CasesTable.csv'
#                  delimiter=",", overwrite=True)
#     else:
#         return cases2

# examples

# species_list = ['H2O_main_iso','CO_all_iso','CO2_main_iso', 'CH4_main_iso']
# atmos_full, pressures, atmos_i_list = gen_atm_all(species_list, indiv=True)
# species = OrderedDict({'H2O_main_iso':[-3], 
#                        'CO_all_iso':[-3, -4, -8, -12],
#                        'CO2_main_iso':[-3, -4, -5], 
#                        'CH4_main_iso':[-6, -10]})


def prepare_model(modelWave0, modelTD0, Rbf, Raf=64000, rot_params=None,
                  # left_val=1., right_val=1.,
                  **kwargs):
    if rot_params is not None:
        rot_ker = RotKerTransitCloudy(rot_params[0], rot_params[1], rot_params[2],
                                      np.array(rot_params[3]) / u.day, Raf,
                                      # left_val=left_val, right_val=right_val,
                                      step_smooth=250., v_mid=0., **kwargs)
    #     if rot_params is not None:
    #         R_pl, M_pl, T_pl, freq, right_cl = rot_params
    #         rot_ker = RotKerTransitCloudy(R_pl, M_pl, T_pl, np.array(freq) / u.day, Raf,
    #                                                   left_val=1., right_val=right_cl,
    #                                                step_smooth=250., v_mid=0., **kwargs)
    else:
        rot_ker = None

    resampled = np.ma.masked_invalid(resamp_model(modelWave0[:-1], modelTD0[:-1], Rbf,
                                                  Raf=Raf, rot_ker=rot_ker))

    return modelWave0[:-1][15:-15], resampled[15:-15]


def retrieval_model_plain(atmos_object, species, planet, pressures, temperatures,
                          gravity, P0, cloud, R_pl, R_star,
                          kappa_factor=None, gamma_scat=None, vmrh2he=None, plot_abundance=False,
                          kind_trans='transmission', dissociation=False, fct_star=None,
                          contribution=False, **kwargs):
    if vmrh2he is None:
        vmrh2he = [0.85, 0.15]
    if kappa_factor is not None:
        kappa_zero = kappa_factor * (5.31e-31 * u.m ** 2 / u.u).cgs.value
    else:
        kappa_zero = None

    abundances, MMW = gen_abundances([*species.keys()], [*species.values()],
                                     pressures, temperatures,
                                     verbose=False, vmrh2he=vmrh2he,
                                     dissociation=dissociation, plot=plot_abundance)

    if kind_trans == 'transmission':
        atmos_object.calc_transm(temperatures, abundances, gravity, MMW,
                                 R_pl=R_pl, P0_bar=P0, Pcloud=cloud,
                                 gamma_scat=gamma_scat, kappa_zero=kappa_zero,
                                 contribution=contribution,
                                 **kwargs)
        out = atmos_object.transm_rad ** 2 / R_star ** 2
    elif kind_trans == "emission":
        #         bb_mod = bb(planet.Teff)
        atmos_object.calc_flux(temperatures, abundances, gravity, MMW,
                               Pcloud=cloud,
                               gamma_scat=gamma_scat, kappa_zero=kappa_zero,
                               contribution=contribution,
                               **kwargs)
        wave = nc.c / atmos_object.freq / 1e-4
        if fct_star is None:
            # --- if no star spectrum function has been provided, it takes a black body model
            bb_mod = BB(planet.Teff)
            # -- Converting u.erg/u.cm**2/u.s/u.Hz to u.erg/u.cm**2/u.s/u.cm
            star_spectrum = (bb_mod(wave * u.um) * np.pi * u.sr * const.c / (wave * u.um) ** 2).to(
                u.erg / u.cm ** 2 / u.s / u.cm)
        else:
            star_spectrum = fct_star(wave) * (u.erg / u.cm ** 2 / u.s / u.cm)

        out = ((atmos_object.flux * (u.erg / u.cm ** 2 / u.s / u.Hz) *
                const.c / (wave * u.um) ** 2).to(u.erg / u.cm ** 2 / u.s / u.cm) *
               (R_pl ** 2 / R_star ** 2) / star_spectrum).decompose()

    return nc.c / atmos_object.freq / 1e-4, out  # .decompose()#, MMW

# def retrieval_model_plain_retrieval_version(atmos_object, species, planet, pressures, temperatures,
#                           gravity, P0, cloud, \
#                           R_pl, R_star, kappa_factor=None, gamma_scat=None, 
#                           kind_trans = 'emission', dissociation=True, fct_star=None, **kwargs):
#     if kappa_factor is not None:
#         kappa_zero = kappa_factor * (5.31e-31*u.m**2/u.u).cgs.value
#     else:
#         kappa_zero = None

#     abundances, MMW = prt.gen_abundances([*species.keys()], [*species.values()], 
#                                      pressures, temperatures, verbose=False, 
#                                      dissociation=dissociation, plot=False)  #, MMW=MMW)

#     if kind_trans == 'transmission':
#         atmos_object.calc_transm(temperatures, abundances, gravity, MMW, \
#                               R_pl = R_pl, P0_bar = P0, Pcloud=cloud, 
#                              gamma_scat=gamma_scat, kappa_zero=kappa_zero, **kwargs)
#         out = atmos_object.transm_rad**2/R_star**2
#     elif kind_trans == "emission":
#         atmos_object.calc_flux(temperatures, abundances, gravity, MMW,
#                               Pcloud=cloud, 
#                              gamma_scat=gamma_scat, kappa_zero=kappa_zero, **kwargs)
# #         out = atmos_object.flux*(R_pl**2/R_star**2).decompose()/\
# #                     (bb_mod((nc.c/atmos_object.freq/1e-4)*u.um) *\
# #                      np.pi *u.sr).to(u.erg/u.cm**2/u.s/u.Hz)  # in erg cm-2 s-1 Hz-1
#         wave = nc.c/atmos_object.freq/1e-4
#         if fct_star is None:
#             bb_mod = bb(planet.Teff)
#             # -- Converting u.erg/u.cm**2/u.s/u.Hz to u.erg/u.cm**2/u.s/u.cm
#             star_spectrum = (bb_mod(wave*u.um) * np.pi *u.sr * const.c / (wave*u.um)**2 ).to(u.erg/u.cm**2/u.s/u.cm)
#         else:
#             star_spectrum = fct_star(wave)*(u.erg/u.cm**2/u.s/u.cm)

#         out = ((atmos_object.flux * (u.erg / u.cm**2 /u.s /u.Hz) *\
#                                const.c / (wave*u.um)**2).to(u.erg/u.cm**2/u.s/u.cm) * \
#                                 (R_pl**2/R_star**2) / star_spectrum ).decompose()


#     return nc.c/atmos_object.freq/1e-4, out


# def retrieval_model_plain(atmos_object, species, pressures, temperatures, gravity, P0, cloud, \
#                           R_pl, R_star, kappa_factor=None, gamma_scat=None, 
#                           kind_trans = 'transmission', Teff=5000*u.K, dissociation=False, **kwargs):
#     if kappa_factor is not None:
#         kappa_zero = kappa_factor * (5.31e-31*u.m**2/u.u).cgs.value
#     else:
#         kappa_zero = None

#     abundances, MMW = gen_abundances([*species.keys()], [*species.values()], 
#                                      pressures, temperatures, verbose=False, dissociation=dissociation)#, MMW=MMW)
#     # --- Calculating a more precise MMW
# #     MMW = calc_MMW2(abundances)
# #     MMW2 = calc_MMW2(abundances)
# #     print('MMW2 = {}, MMM3 = {}'.format(MMW2, MMW))

#     if kind_trans == 'transmission':
#         atmos_object.calc_transm(temperatures, abundances, gravity, MMW, \
#                               R_pl = R_pl, P0_bar = P0, Pcloud=cloud, 
#                              gamma_scat=gamma_scat, kappa_zero=kappa_zero, **kwargs)
#         out = atmos_object.transm_rad**2/R_star**2
#     elif kind_trans == "emission":
#         bb_mod = bb(Teff)
#         atmos_object.calc_flux(temperatures, abundances, gravity, MMW,
#                               Pcloud=cloud, 
#                              gamma_scat=gamma_scat, kappa_zero=kappa_zero, **kwargs)
#         out = atmos_object.flux*R_pl**2/R_star**2/\
#                     (bb_mod((nc.c/atmos_object.freq/1e-4)*u.um) *\
#                      np.pi *u.sr).to(u.erg/u.cm**2/u.s/u.Hz)  # in erg cm-2 s-1 Hz-1

#     return nc.c/atmos_object.freq/1e-4, out


#################
# Prior Functions
#################
# Taken from petitRADTRANS


# SQRT2 = math.sqrt(2.)
# import math as math
# from scipy.special import gamma,erfcinv

# # Stolen from https://github.com/JohannesBuchner/MultiNest/blob/master/src/priors.f90
# def log_prior(cube,lx1,lx2):
#     return 10**(lx1+cube*(lx2-lx1))

# def uniform_prior(cube,x1,x2):
#     return x1+cube*(x2-x1)

def gaussian_prior(cube, mu, sigma):
    #     SQRT2 = math.sqrt(2.)
    #     return mu + sigma*SQRT2*erfcinv(2.0*(1.0 - cube))
    return -(((cube - mu) / sigma) ** 2.) / 2.


# def log_gaussian_prior(cube,mu,sigma):
#     SQRT2 = math.sqrt(2.)
#     bracket = sigma*sigma + sigma*SQRT2*erfcinv(2.0*cube)
#     return mu*np.exp(bracket)

# def delta_prior(cube,x1,x2):
#     return x1

# # Sanity checks on parameter ranges
# def b_range(x, b):
#     if x > b:
#         return -np.inf
#     else:
#         return 0.

def a_b_range(x, a, b):
    if x < a:
        return -np.inf
    elif x > b:
        return -np.inf
    else:
        return 0.
