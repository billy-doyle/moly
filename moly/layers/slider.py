import plotly.graph_objects as go

from ..figure.colors import *
from ..figure.layouts import *


def orbital_trace(cubes, iso, spacing, origin):

    x,y,z = np.mgrid[:cubes[0].shape[0], :cubes[0].shape[1], :cubes[0].shape[2]]

    x_r = x * spacing[0] + origin[0]
    y_r = y * spacing[1] + origin[1]
    z_r = z * spacing[2] + origin[2]

    iso_surf = go.Isosurface(visible = False,
                             x = x_r.flatten(),
                             y = y_r.flatten(), 
                             z = z_r.flatten(), 
                             value = cubes[0].flatten(),
                             surface_count = 2,
                             colorscale = 'Portland_r',
                             showscale=False,
                             isomin=-1 * iso,
                             isomax= 1 * iso,
                             opacity = 0.2, 
                             flatshading = False,
                             lighting = surface_materials["matte"],
                             caps=dict(x_show=False, y_show=False, z_show=False))

    return iso_surf