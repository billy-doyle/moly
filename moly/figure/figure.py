"""

Creates main figure 

"""
import numpy as np
import qcelemental as qcel
import plotly.graph_objects as go

from ..molecule.shapes import get_sphere
from ..molecule.shapes import get_single_cylinder
from ..molecule.shapes import rotation_matrix

from ..layers.bonds import get_bond_mesh
from ..layers.geometry import get_sphere_mesh
from ..layers.cube import get_cubes, cube_to_molecule, get_cubes, get_cubes_traces, get_buttons, get_surface, get_buttons_wfn, get_cube
from .layouts import get_layout

from ..advanced import cubeprop


class Figure():
    def __init__(self, surface="matte", figsize=None, **kwargs):

        self.fig = go.Figure()
        self.molecules = {}
        self.geometries = []
        self.surface = surface
        self.resolution = figsize

        self.min_range = 0.0
        self.max_range = 0.0


    def show(self):
        self.fig.show()


    def add_molecule(self, name, molecule, style="ball_and_stick"):

        bonds = get_connectivity(molecule)
        add_bonds(molecule.geometry, molecule.symbols, bonds, self.fig, style, self.surface)
        add_atoms(molecule.geometry, molecule.atomic_numbers, molecule.symbols, self.fig, style, self.surface)
        self.molecules[name] = molecule

        self.assert_range(molecule.geometry)
        self.fig.update_layout(get_layout(molecule.geometry, self.resolution, self.min_range, self.max_range))


    def add_measurement(self, mol_label, m, 
                        line_width=10,
                        line_color='green'):

        molecule = self.molecules[mol_label]
        measurement = molecule.measure(m)

        if len(m) == 2:
            add_line(str(round(measurement, 2)) ,molecule.geometry[m[0]], molecule.geometry[m[1]], 
                    line_width,
                    line_color, self.fig)

        elif len(m) == 3:
            add_angle(str(round(measurement,2)), 
                    molecule.geometry[m[0]], molecule.geometry[m[1]], molecule.geometry[m[2]], 
                    line_color, self.fig)


        elif len(m) == 4:
            print("Unable to add dihedral")


    def add_density(self, wfn, densities, iso, quality=0.2, overage=2.0, style="ball_and_stick"):

        if len(densities) > 4:
            raise ValueError("Up to four densities are availiable: Da, Db, Ds, Dt")

        molecule = qcel.models.Molecule.from_data(wfn.molecule().save_string_xyz())
        bonds = get_connectivity(molecule)
        add_bonds(molecule.geometry, molecule.symbols, bonds, self.fig, style, self.surface)
        add_atoms(molecule.geometry, molecule.atomic_numbers, molecule.symbols, self.fig, style, self.surface)

        L = [4.0, 4.0, 4.0]
        D = [quality, quality, quality]

        O, N =  cubeprop.build_grid(wfn, L, D) 
        block, points, nxyz, npoints =  cubeprop.populate_grid(wfn, O, N, D)
        trace_list = []
        if "Da" in densities:
            density_mesh = cubeprop.compute_density(O, N, D, npoints, points, nxyz, block, wfn.Da(), iso)
            trace = get_surface(density_mesh, quality, O)
            trace_list.append(trace)
        if "Db" in densities:
            density_mesh = cubeprop.compute_density(O, N, D, npoints, points, nxyz, block, wfn.Db(), iso)
            trace = get_surface(density_mesh, quality, O)
            trace_list.append(trace)
        if "Ds" in densities:
            Ds = wfn.Da().clone()
            Ds.axpy(-1.0, wfn.Db())
            density_mesh = cubeprop.compute_density(O, N, D, npoints, points, nxyz, block, Ds, iso)
            trace = get_surface(density_mesh, quality, O)
            trace_list.append(trace)
        if "Dt" in densities:
            Dt = wfn.Da().clone()
            Dt.axpy(1.0, wfn.Db())
            density_mesh = cubeprop.compute_density(O, N, D, npoints, points, nxyz, block, Dt, iso)
            trace = get_surface(density_mesh, quality, O)
            trace_list.append(trace)

        if len(trace_list) == 1:
            self.fig.add_trace(trace_list[0])    

        elif len(trace_list) > 1:
            geometry_traces = len(self.fig.data)

            button_list = get_buttons_wfn(densities, geometry_traces)
            self.fig.update_layout(updatemenus=[dict(showactive=True,
                                                     buttons=button_list,
                                                     font={"family": "Helvetica", "size" : 18},
                                                     borderwidth=0
            ),
            ])

            for trace in trace_list:
                self.fig.add_trace(trace)

        self.assert_range(molecule.geometry)
        self.fig.update_layout(get_layout(molecule.geometry, self.resolution, self.min_range * overage, self.max_range * overage))



    def add_cubes(self, directory=".", iso=0.03, style="ball_and_stick", colorscale="Portland_r", opacity=0.3):
        cubes, details = get_cubes(directory)
        geometry, symbols, atomic_numbers, spacing, origin = cube_to_molecule(details[0]["name"]+".cube")
        bonds = qcel.molutil.guess_connectivity(symbols, geometry)
        add_bonds(geometry, symbols, bonds, self.fig, style, self.surface)
        add_atoms(geometry, atomic_numbers, symbols, self.fig, style, self.surface)

        geometry_traces = len(self.fig.data)

        traces = get_cubes_traces(cubes, spacing, origin, iso, colorscale,opacity)
        for vol in traces:
            self.fig.add_traces(vol)

        
        button_list = get_buttons(details, geometry_traces)

        self.fig.update_layout(updatemenus=[dict(showactive=True,
                                                buttons=button_list,
                                                font={"family": "Helvetica",
                                                      "size" : 18},
                                                borderwidth=0
            ),
        ])

        self.assert_range(geometry)
        self.fig.update_layout(get_layout(geometry, self.resolution, self.max_range, self.min_range, overage=4.0))


    def add_blob_slider(self, path_to_file, iso_slider, style="ball_and_stick"):

        cubes, details = get_cube(path_to_file)
        geometry, symbols, atomic_numbers, spacing, origin = cube_to_molecule(details[0]["name"]+".cube")
        bonds = qcel.molutil.guess_connectivity(symbols, geometry)
        add_bonds(geometry, symbols, bonds, self.fig, style, self.surface)
        add_atoms(geometry, atomic_numbers, symbols, self.fig, style, self.surface)

        iso_min, iso_max, st = iso_slider
        iso_steps = np.arange(iso_min, iso_max + st, st)

        x,y,z = np.mgrid[:cubes[0].shape[0], :cubes[0].shape[1], :cubes[0].shape[2]]
        
        x_r = x * spacing[0] + origin[0]
        y_r = y * spacing[1] + origin[1]
        z_r = z * spacing[2] + origin[2]

        for step in np.arange(iso_min, iso_max + st, st):
            self.fig.add_trace(
                go.Isosurface(
                visible = False,
                x = x_r.flatten(),
                y = y_r.flatten(), 
                z = z_r.flatten(), 
                value = cubes[0].flatten(),
                surface_count = 2,
                colorscale = 'Portland_r',
                showscale=False,
                isomin=-1 * step,
                isomax= 1 * step,
                opacity = 0.2))


        self.fig.data[0].visible = True

        steps = []
        for i in range(len(self.fig.data)):
            step = dict(
                method="restyle",
                args=["visible", [False] * len(self.fig.data)],
            )
            step["args"][1][i] = True  # Toggle i'th trace to "visible"
            steps.append(step)

        sliders = [dict(
            active=10,
            currentvalue={"prefix": "Iso: "},
            pad={"t": 50},
            steps=steps
        )]

        self.fig.update_layout(get_layout(geometry, self.resolution, self.max_range, self.min_range, overage=4.0),
            sliders=sliders
        )

        #print(len(list(iso_steps)))

        for i, ival in enumerate(list(iso_steps), start = 0):
            self.fig['layout']['sliders'][0]['steps'][i]['label'] = str(ival)[:5]



    def add_cube(self, index=0, iso=0.01, color="Portland_r", opacity=0.2, style="ball_and_stick"):
        volume = get_cube(self.molecules[index], iso, opacity, color)
        self.fig.add_trace(volume)

    def add_layer(self, trace):
        self.fig.add_trace(trace)

    def assert_range(self, geometry):

        self.min_range = self.min_range if self.min_range < np.min(geometry) else np.min(geometry)
        self.max_range = self.max_range if self.max_range > np.max(geometry) else np.max(geometry)

def add_bonds(geometry, symbols, bonds, figure, style, surface):

    for idx1, idx2 in bonds:

        vec1 = geometry[idx1]
        vec2 = geometry[idx2]
        length = np.linalg.norm(vec2-vec1)
        R = rotation_matrix(np.array([0,0,1]), vec2 - vec1)

        if style is "ball_and_stick" or style is "tubes":
            r = 0.3
        elif style is "wireframe":
            r = 0.06
        elif style is "spacefilling":
            return
        else:
            raise ValueError("Only avaliable styles are \"ball_and_stick\", \"tubes\", \"spacefilling\" and \"wireframe\" ")

        if symbols[idx1] == symbols[idx2]:

            cyl = get_single_cylinder(radius=r)
            cyl[:,2] *= length
            cyl = R.dot(cyl.T).T
            cyl += vec1

            mesh = get_bond_mesh(cyl, idx1, symbols, surface)
            figure.add_trace(mesh)

        if symbols[idx1] != symbols[idx2]:

            cyl = get_single_cylinder(radius=r)
            cyl[:,2] *= length / 2
            cyl = R.dot(cyl.T).T
            cyl_1 = cyl + vec1
            cyl_2 = cyl + (vec1+vec2)/2

            mesh = get_bond_mesh(cyl_1, idx1, symbols, surface)
            figure.add_trace(mesh)
            mesh = get_bond_mesh(cyl_2, idx2, symbols, surface)
            figure.add_trace(mesh)
            
def add_atoms(geometry, atomic_numbers, symbols, figure, style, surface):
    sphere = np.array(get_sphere())
    for atom, xyz in enumerate(geometry):
        if style is "ball_and_stick":
            reshaped_sphere = sphere * (atomic_numbers[atom]/30 + 0.6)
        elif style is "tubes":
            reshaped_sphere = sphere * 0.3
        elif style is "spacefilling":
            reshaped_sphere = sphere * (atomic_numbers[atom]/20 + 1.5)
        elif style is "wireframe":
            reshaped_sphere = sphere * 0.06
        else:
            raise ValueError("Only avaliable styles are \"ball_and_stick\", \"tubes\", \"spacefilling\" and \"wireframe\" ")
        mesh = get_sphere_mesh(reshaped_sphere,symbols[atom], xyz, surface)
        figure.add_trace(mesh)

def add_angle(measurement, p1, p2, p3, line_color, figure):
    
    midpoint = p2

    triangle = go.Mesh3d(x=[p1[0],p2[0],p3[0]],
                         y=[p1[1],p2[1],p3[1]],
                         z=[p1[2],p2[2],p3[2]],
                         alphahull = 0,
                         opacity = 1, 
                         color="lightpink")

    label = go.Scatter3d(x=[midpoint[0]], y=[midpoint[1]], z=[midpoint[2]], 
                        mode="text",
                        text=measurement,
                        textposition="middle center")
     
    figure.add_trace(label)
    figure.add_trace(triangle)

def add_line(measurement, p1, p2, line_width, line_color, figure):

    midpoint = (p1 + p2)/2

    line = go.Scatter3d(x=[p1[0], p2[0]],y=[p1[1],p2[1]],z=[p1[2],p2[2]], 
                        mode="lines",
                        line={"width": line_width,
                              "color": line_color, 
                              "dash" : "dot"})
    label = go.Scatter3d(x=[midpoint[0]], y=[midpoint[1]], z=[midpoint[2]], 
                        mode="text",
                        text=measurement,
                        textposition="middle center")
    figure.add_trace(line)
    figure.add_trace(label)

def get_connectivity(molecule):

    mol_dict = molecule.dict()
    symbols = molecule.symbols
    geometry = molecule.geometry
    
    if not "connectivity" in mol_dict:
        return qcel.molutil.guess_connectivity(symbols, geometry)
    
    elif mol_dict["connectivity"] is None:
        return  qcel.molutil.guess_connectivity(symbols, geometry)

    elif "connectivity" in mol_dict:
        return self.dict["connectivity"]