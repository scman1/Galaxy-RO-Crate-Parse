#plotting library
import matplotlib.pyplot as plt

# plot normalised spectrum wir custom colors and line styles
def plot_normalised(athena_groups = {}, include_groups = {}, aspect = (6,8), xlim=[],ylim=[]):
    plt.figure(figsize=aspect)
    for g_indx, a_group in enumerate(include_groups):
        if athena_groups[a_group].filename in include_groups:
                plt.plot(athena_groups[a_group].energy, 
                         athena_groups[a_group].norm, 
                         label=athena_groups[a_group].filename,
                         color = include_groups[a_group][0],
                         linestyle = include_groups[a_group][1]
                        ) 

    frame1 = plt.gca()
    #frame1.axes.yaxis.set_ticklabels([])
    #frame1.axes.yaxis.set_ticklabels([])
    plt.ylabel("Normalized XANES (a.u.)")
    plt.xlabel("Energy (eV)")
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.legend()
    plt.show()

    return plt


# individaul normal plots
def normal_subplot(a_subplt, athena_groups = {}, include_groups = {}, xlim=[],ylim=[], s_legend = True):
    for g_indx, a_group in enumerate(include_groups):
        a_subplt.plot(athena_groups[a_group].energy,
                      athena_groups[a_group].norm, 
                      label=athena_groups[a_group].filename,
                      color = include_groups[a_group][0],
                      linestyle = include_groups[a_group][1]
                     )                 
    if s_legend:
        a_subplt.legend() # show legend
        a_subplt.set_ylabel("Normalized Absorption $\mu$(E)")
        a_subplt.set_xlabel("Energy (eV)")
    a_subplt.set_xlim(xlim)
    a_subplt.set_ylim(ylim)
    a_subplt.tick_params(axis='both', which='major', labelsize=9)
    return a_subplt

def derivative_subplot(a_subplt, athena_groups = {}, include_groups = {}, xlim=[],ylim=[], s_legend = True):
    for g_indx, a_group in enumerate(include_groups):
        if athena_groups[a_group].filename in include_groups:
                a_subplt.plot(athena_groups[a_group].energy, 
                         athena_groups[a_group].dmude, 
                         label=athena_groups[a_group].filename,
                         color = include_groups[a_group][0],
                         linestyle = include_groups[a_group][1]
                        ) 
    if s_legend:
        a_subplt.legend() # show legend
    a_subplt.set_ylabel("Derivate normalised $\mu$(E)")
    a_subplt.set_xlabel("Energy (eV)")
    a_subplt.set_xlim(xlim)
    a_subplt.set_ylim(ylim)
    a_subplt.tick_params(axis='both', which='major', labelsize=9)
    return a_subplt


# normal plot with inset closeup
def plot_normal_w_inset(athena_groups = {}, include_groups = {}, aspect=(6,8),
                        lp_xlim=[], lp_ylim=[], 
                        sp_xlim=[],  sp_ylim=[]):
    fig, ax1 = plt.subplots(figsize=aspect)
    # These are in unitless percentages of the figure size. (0,0 is bottom left)
    left, bottom, width, height = [0.55, 0.2, 0.3, 0.3]
    ax2 = fig.add_axes([left, bottom, width, height])

    ax1 = normal_subplot(ax1, athena_groups, include_groups, lp_xlim,lp_ylim)
    ax2 = normal_subplot(ax2, athena_groups, include_groups, sp_xlim,sp_ylim, False)
    return plt

# normal plot with derivative inset closeup
def plot_normal_w_derivate(athena_groups = {}, include_groups = {}, aspect=(6,8),
                        lp_xlim=[], lp_ylim=[], 
                        sp_xlim=[],  sp_ylim=[]):
    fig, ax1 = plt.subplots(figsize=aspect)
    # These are in unitless percentages of the figure size. (0,0 is bottom left)
    left, bottom, width, height = [0.55, 0.2, 0.3, 0.3]
    ax2 = fig.add_axes([left, bottom, width, height])

    ax1 = normal_subplot(ax1, athena_groups, include_groups, lp_xlim,lp_ylim)
    ax2 = derivative_subplot(ax2, athena_groups, include_groups, sp_xlim,sp_ylim, False)
    return plt



#plot the derivative       
def plot_derivative(athena_groups = {}, include_groups = {}, aspect = (6,8), xlim=[],ylim=[], s_legend = True):
    plt.figure(figsize=aspect)
    for g_indx, a_group in enumerate(include_groups):
        if athena_groups[a_group].filename in include_groups:
                plt.plot(athena_groups[a_group].energy, 
                         athena_groups[a_group].dmude, 
                         label=athena_groups[a_group].filename,
                         color = include_groups[a_group][0],
                         linestyle = include_groups[a_group][1]
                        ) 

    frame1 = plt.gca()
    #frame1.axes.yaxis.set_ticklabels([])
    #frame1.axes.yaxis.set_ticklabels([])
    plt.ylabel("Normalized Absorption (a.u.)")
    plt.xlabel("Energy (eV)")
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.legend()
    plt.show()

    return plt

#plot chi magnitude (FT)
        
def plot_chi_magnitude(athena_groups = {}, include_groups = {}, aspect = (6,8), xlim=[],ylim=[]):
    plt.figure(figsize=aspect)
    for g_indx, a_group in enumerate(include_groups):
        if athena_groups[a_group].filename in include_groups:
                plt.plot(athena_groups[a_group].r, 
                         athena_groups[a_group].chir_mag, 
                         label=athena_groups[a_group].filename,
                         color = include_groups[a_group][0],
                         linestyle = include_groups[a_group][1]
                        ) 

    frame1 = plt.gca()
    #frame1.axes.yaxis.set_ticklabels([])
    #frame1.axes.yaxis.set_ticklabels([])
    plt.xlabel("$R(\mathrm{\AA})$")
    plt.ylabel("$|\chi(R)|(\mathrm{\AA}^{-3})$")
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.legend()
    plt.show()

    return plt

"""
=============================================
Generate polygons to fill under 3D line graph
=============================================

Demonstrate how to create polygons which fill the space under a line
graph. In this example polygons are semi-transparent, creating a sort
of 'jagged stained glass' effect.
"""

from mpl_toolkits.mplot3d import Axes3D
from matplotlib.collections import PolyCollection
import matplotlib.patches as mpatches
from matplotlib import colors as mcolors
import numpy as np

#plt.figure(figsize=(12,10))



# create see through colours
def cc(arg):
    return mcolors.to_rgba(arg, alpha=0.6)

def plot_normal_3db(groups = [], xlims=[19970, 20150]):
    fig = plt.figure(figsize=(12,12))
    ax = fig.add_subplot(projection = '3d')
    ax.view_init(elev=25., azim=-120)
    
    verts = []
    zs = np.arange(1, len(groups)+1, 1)
    for a_group in groups:

        x1_idx = np.abs(a_group.energy - xlims[0]).argmin()
        x2_idx = np.abs(a_group.energy - xlims[1]).argmin()
        
        ys = a_group.norm[x1_idx:x2_idx]
        # make first and last values of y [0,0] 
        # so the fill is always under the curve
        ys[0], ys[-1] = 0, 0
        xs =a_group.energy[x1_idx:x2_idx]
        verts.append(list(zip(xs, ys)))

    poly = PolyCollection(verts, facecolors=[cc('w'), cc('w'), cc('w'), cc('w')], 
                          edgecolors= ['black'])
    
    transp_val = 1.0
    
    norm = plt.Normalize(vmin=zs.min().min(), vmax=zs.max().max())
    
    x_colours  = plt.cm.plasma(norm(zs))
    
    colour_dict ={}
    for group, colour in zip(groups, x_colours):
        colour_dict[group.filename] = colour  
    
    poly = PolyCollection(verts,facecolors=x_colours,
                          edgecolors= ['black'])
    poly.set_alpha(transp_val)
    
    # add lengends
    colour_patches = []
    for group, colour in zip(groups, x_colours):
        colour_patches.append(mpatches.Patch(color=colour, label=group.filename, alpha=transp_val))  
    
    ax.legend(handles=colour_patches, loc="upper right")
    
    ax.add_collection3d(poly, zs=zs, zdir='y')

    ax.set_xlabel('Energy (eV)')
    ax.set_xlim3d(19960, 20150)
    #ax.set_ylabel('groups')
    ax.set_ylim3d(len(groups),0)
    ax.set_zlabel('Normalized $\mu$(E)')
    ax.set_zlim3d(0, 1.2)
    return plt 
