import numpy as np 

def get_slider(iso_range, iso_steps, geometry_traces):

    steps = []

    for i in range(iso_steps):
        step = {"method" : "update", 
                "label"  : str(iso_range[i]),
                "args"  : [{"visible" : [True] * geometry_traces + [False] * iso_steps}]}
        step["args"][0]["visible"][geometry_traces + i] = True
        steps.append(step)

    sliders = [{"active" : iso_steps, 
               "currentvalue" : {"prefix" : "Iso Value: "}, 
               "pad" : {"t" : 50},
               "steps" : steps}]

    return sliders

def get_buttons(meta, geo_traces, folder):
    buttons =  []
    dirlenght = len(folder) + 1 

    buttons.append(dict(label="Geometry",
                         method="update",
                         args=[{"visible": [True for traces in range(geo_traces)] + [False for cube_j in meta]},
                               {"title": "",
                                "annotations": []}]))

    for cube_i in meta:
        button = dict(label=cube_i["name"][dirlenght:],
                         method="update",
                         args=[{"visible": [True for traces in range(geo_traces)] + [True if cube_i['name'] == cube_j['name'] else False for cube_j in meta]},
                               {"title": "",
                                "annotations": []}])
        buttons.append(button)

    return buttons

def get_buttons_wfn(meta, geo_traces):
    buttons =  []

    buttons.append(dict(label="Geometry",
                        method="update",
                        args=[{"visible": [True for traces in range(geo_traces)] + [False for trace_j in meta]},
                            {"title": "",
                            "annotations": []}]))

    for trace_i in meta:
        button = dict(label=trace_i,
                      method="update",
                      args=[{"visible": [True for traces in range(geo_traces)] + [True if trace_i == trace_j else False for trace_j in meta]},
                            {"title": "", "annotations": []}])
        buttons.append(button)

    return buttons