# Copyright (c) 2007-2019 The Psi4 Developers.
# Copyright (c) 2014-2018, The Psi4NumPy Developers.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:

#     * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.

#     * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided
#        with the distribution.

#     * Neither the name of the Psi4NumPy Developers nor the names of any
#        contributors may be used to endorse or promote products derived
#        from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import numpy as np
import psi4


def build_grid(wfn, L, D):
    """
    Creates origin and extent of the cube file

    Parameters
    ----------

    wfn : psi4.core.Wavefunction
        Wavefunction object from Psi4 energy calculation
    L : List
        Spacial Extent for x,y,z directions
    D : List
        Grid Spacing in bohrs for x,y,z directions


    Returns
    -------

    O : List
        Origin for the cubefile

    N : List
        Number of points for each coordinate

    """

    geometry = wfn.molecule().full_geometry().np

    Xmin = np.zeros(3)
    Xmax = np.zeros(3)
    Xdel = np.zeros(3)

    N = np.zeros(3)
    O = np.zeros(3)

    for k in [0,1,2]:
        Xmin[k] = Xmax[k] = geometry[0,k]

        for atom in range(len(geometry)):
            Xmin[k] = geometry[atom, k] if Xmin[k] > geometry[atom, k] else Xmin[k]
            Xmax[k] = geometry[atom, k] if Xmax[k] < geometry[atom, k] else Xmax[k]

        Xdel[k] = Xmax[k] - Xmin[k]
        N[k] = int((Xmax[k] - Xmin[k] + 2.0 * L[k]) / D[k])

        if D[k] * N[k] < (Xmax[k] - Xmin[k] + 2.0 * L[k]):
            N[k] += 1

        O[k] = Xmin[k] - (D[k] * N[k] - (Xmax[k] - Xmin[k])) / 2.0

    return O, N


def populate_grid(wfn, O, N, D):
    """
    Build cube grid

    Parameters
    ----------

    wfn : psi4.core.Wavefunction
        Wavefunction object from Psi4 energy calculation
    O : List
        Origin for the cubefile
    N : List
        Number of points for each coordinate
    D : List
        Grid Spacing in bohrs for x,y,z directions


    Returns
    -------

    block : List
        Set of psi4.core.BlockOPoints for cube grid
    points : psi4.core.RKSFunctions
    nxyz : integer
        number of points in each direction for rectangular grid
    npoints : int
        total number of points in grid

    """

    epsilon = psi4.core.get_global_option("CUBIC_BASIS_TOLERANCE")
    basis  = psi4.core.BasisSet.build(wfn.molecule(), 'ORBITAL', wfn.basisset().name())
    extens = psi4.core.BasisExtents(basis, epsilon)

    npoints = (N[0]) * (N[1]) * (N[2])

    x = np.zeros(int(npoints))
    y = np.zeros(int(npoints))
    z = np.zeros(int(npoints))
    w = np.zeros(int(npoints))


    max_points = psi4.core.get_global_option("CUBIC_BlOCK_MAX_POINTS")
    nxyz = int(np.round(max_points**(1/3)))

    block = []
    offset = 0
    i_start = 0
    j_start = 0
    k_start = 0

    x_plot, y_plot, z_plot = [], [], []

    for i in range(i_start, int(N[0] + 1), nxyz):
        ni = int(N[0]) - i if i + nxyz > N[0] else nxyz
        for j in range(j_start, int(N[1] + 1), nxyz):
            nj = int(N[1]) - j if j + nxyz > N[1] else nxyz
            for k in range(k_start, int(N[2] + 1), nxyz):
                nk = int(N[2]) - k if k + nxyz > N[2] else nxyz

                x_in, y_in, z_in, w_in = [], [], [], []

                block_size = 0
                for ii in range(i , i + ni):
                    for jj in range(j, j + nj):
                        for kk in range(k, k + nk):

                            x[offset] = O[0] + ii * D[0]
                            y[offset] = O[1] + jj * D[1]
                            z[offset] = O[2] + kk * D[2]
                            w[offset] = D[0] * D[1] * D[2]

                            x_plot.append(x[offset])
                            y_plot.append(y[offset])
                            z_plot.append(z[offset])

                            x_in.append(x[offset])
                            y_in.append(y[offset])
                            z_in.append(z[offset])
                            w_in.append(w[offset])

                            offset     += 1
                            block_size += 1

                x_out = psi4.core.Vector.from_array(np.array(x_in))
                y_out = psi4.core.Vector.from_array(np.array(y_in))
                z_out = psi4.core.Vector.from_array(np.array(z_in))
                w_out = psi4.core.Vector.from_array(np.array(w_in))

                block.append(psi4.core.BlockOPoints(x_out, y_out, z_out, w_out, extens))

    max_functions = 0
    for i in range(max_functions, len(block)):
        max_functions = max_functions if max_functions > len(block[i].functions_local_to_global()) else len(block[i].functions_local_to_global())

    points = psi4.core.RKSFunctions(basis, int(npoints), max_functions)
    points.set_ansatz(0)

#    return block, points, nxyz, npoints, [x_plot, y_plot, z_plot]
    return block, points, nxyz, npoints


def add_density(npoints, points, block, matrix):
    """
    Computes density in new grid


    Parameters
    ----------

    npoints: int
        total number of points
    points : psi4.core.RKSFunctions
    block : list
        Set of psi4.core.BlockOPoints for cube grid
    matrix : psi4.core.Matrix
        One-particle density matrix


    Returns
    -------

    v : numpy array
        Array with density values on the grid
    """

    v = np.zeros(int(npoints))

    points.set_pointers(matrix)
    rho = points.point_values()["RHO_A"]

    offset = 0
    for i in range(len(block)):
        points.compute_points(block[i])
        n_points = block[i].npoints()
        offset += n_points
        v[offset-n_points:offset] = 0.5 * rho.np[:n_points]

    return v





def compute_isocontour_range(v, npoints):
    """
    Computes threshold for isocontour range

    Parameters
    ----------

    v : numpy array
        Array with scalar values on the grid

    npopints : int
        Total number of points on the grid


    Returns
    -------

    values : list
        Value of positive and negative isocontour

    cumulative_threshold: float

    """
    cumulative_threshold = 0.85

    sum_weight = 0

    #Store the points with their weights and compute the sum of weights
    sorted_points = np.zeros((int(npoints),2))
    for i in range(0, int(npoints)):
        value = v[i]
        weight = np.power(np.abs(value), 1.0)
        sum_weight += weight
        sorted_points[i] = [weight, value]

    #Sort the points
    sorted_points = sorted_points[np.argsort(sorted_points[:,1])][::-1]

    #Determine the positve and negative bounds

    sum = 0

    negative_isocontour = 0.0
    positive_isocontour = 0.0

    for i in range(len(sorted_points)):

        if sorted_points[i,1] >=  0:
            positive_isocontour = sorted_points[i,1]

        if sorted_points[i,1] <  0:
            negative_isocontour = sorted_points[i,1]

        sum += sorted_points[i,0] / sum_weight

        if sum > cumulative_threshold:
            break
    values = [positive_isocontour, negative_isocontour]

    return values, cumulative_threshold


def reorder_array(O, N, D, nxyz, npoints, v):

    #Reorder the grid

    v2 = np.zeros_like(v)

    offset = 0
    for istart in range(0, int(N[0]+1), nxyz):
        ni = int(N[0]) - istart if istart + nxyz > N[0] else nxyz
        for jstart in range(0, int(N[1] + 1), nxyz):
            nj = int(N[1]) - jstart if jstart + nxyz > N[1] else nxyz
            for kstart in range(0, int(N[2] + 1), nxyz):
                nk = int(N[2]) - kstart if kstart + nxyz > N[2] else nxyz

                for i in range(istart, istart + ni):
                    for j in range(jstart, jstart + nj):
                        for k in range(kstart, kstart + nk):


                            index = i * (N[1]) * (N[2]) + j * (N[2]) + k
                            v2[int(index)] = v[offset]

                            offset += 1

    return v2

def compute_density(O, N, D, npoints, points, nxyz, block, matrix):

    v = add_density(npoints, points, block, matrix)
    isocontour_range, threshold = compute_isocontour_range(v, npoints)
    density_percent = 100.0 * threshold
    v2 = reorder_array(O, N, D, nxyz, npoints, v)
    v2 = v2.reshape(int(N[0]),int(N[1]),int(N[2]))

    # it = np.nditer(v2, flags=['multi_index'])
    # x, y, z = [], [], []
    # while not it.finished:
    #     if np.isclose(it[0],iso,atol=0.005):
    #         x.append(it.multi_index[0])
    #         y.append(it.multi_index[1])
    #         z.append(it.multi_index[2])
    #     it.iternext()

    return v2


def compute_orbitals(O, N, D,npoints, points, nxyz, block, C, orbitals, iso):

    v = np.zeros(len(orbitals), npoints)
    v = add_orbitals(npoints, points, block, v, C) 

    return v

     
def add_density(npoints, points, block, matrix):
    """
    Computes density in new grid


    Parameters
    ----------

    npoints: int
        total number of points
    points : psi4.core.RKSFunctions
    block : list
        Set of psi4.core.BlockOPoints for cube grid
    matrix : psi4.core.Matrix
        One-particle density matrix


    Returns
    -------

    v : numpy array
        Array with density values on the grid
    """

    v = np.zeros(int(npoints))

    points.set_pointers(matrix)
    rho = points.point_values()["RHO_A"]

    offset = 0
    for i in range(len(block)):
        points.compute_points(block[i])
        n_points = block[i].npoints()
        offset += n_points
        v[offset-n_points:offset] = 0.5 * rho.np[:n_points]

    return v
