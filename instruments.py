

instrum = {}

instrum['spirou'] = {
'name': 'spirou',
'nord': 49,
'npix': 4088,
'resol': 64000,
'high_res_wv_lim': [0.9, 2.55] 

}

instrum['nirps_he'] = {
'name': 'nirps_he',
'nord': 75,
'npix': 4088,
'resol': 80000,
'high_res_wv_lim': [0.95, 1.96]

}

instrum['nirps_hr'] = {
'name': 'nirps_hr',
'nord': 75,
'npix': 4088,
'resol': 90000,
'high_res_wv_lim': [0.95, 1.96]

}


def load_instrum(instrum_name):
    return instrum[instrum_name]
