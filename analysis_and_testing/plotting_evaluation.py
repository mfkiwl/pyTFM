
# script concerned with evaluating the general accuracy, effects of geometry, pixelsize and fem grid selection.

from pyTFM.utilities_TFM import round_flexible,gaussian_with_nans,make_display_mask,createFolder
from pyTFM.plotting import *
from pyTFM.graph_theory_for_cell_boundaries import mask_to_graph,find_path_circular
import sys
from collections import defaultdict
from skimage.morphology import binary_erosion
from itertools import chain,product
import os
sys.path.insert(0,'/home/user/Software/pyTFM/analysis_and_testing/')
from simulating_deformation import *
from playing_with_strains import *




def display_mask(fig,mask,display_type,type=1,color="C1",d=np.sqrt(2),ax=None, dm=True, lw=9):
    if not dm:
        return
    mask = mask.astype(int)
    if display_type=="outline":
        out_line=mask-binary_erosion((mask))
        out_line=custom_edge_filter(out_line) # risky
        out_line_graph,points=mask_to_graph(out_line,d=d)
        circular_path=find_path_circular(out_line_graph,0)
        circular_path.append(circular_path[0]) # to plot a fully closed loop
        if type == 1:
            ax = fig.axes[0] if ax is None else ax
            ax.plot(points[circular_path][:,1],points[circular_path][:,0],"--",color=color, linewidth=lw)
        if type == 2:
            for ax in fig.axes:
                ax.plot(points[circular_path][:, 1], points[circular_path][:, 0], "--", color=color, linewidth=lw)


    if display_type=="overlay":

        mask_show = make_display_mask(mask)
        if type == 1:
            ax = fig.axes[0] if ax is None else ax
            ax.imshow(mask_show,alpha=0.4)
        if type == 2:
            for ax in fig.axes:
                ax.imshow(mask_show,alpha=0.4)

    if display_type == "windowed":

        mask_show = make_display_mask(mask)
        mask_window=copy.deepcopy(mask_show)
        mask_window[np.isnan(mask_show)]=1
        mask_window[mask_show]=np.nan
        if type == 1:
            ax = fig.axes[0] if ax is None else ax
            ax.imshow(mask_window, alpha=0.4)
        if type == 2:
            for ax in fig.axes:
                ax.imshow(mask_window, alpha=0.4)

def display_stress_tensor(stress_tensor,mask=None,title_str=""):

    fig, axs = plt.subplots(1, 3)
    plt.suptitle(title_str)
    im = axs[0].imshow(stress_tensor[:, :, 0, 0])
    axs[0].set_title("sig_xx", x=0.5, y=0.9, transform=axs[0].transAxes, color="white")
    # plt.colorbar(im)
    im = axs[1].imshow(stress_tensor[:, :, 1, 1])
    axs[1].set_title("sig_yy", x=0.5, y=0.9, transform=axs[1].transAxes, color="white")
    im = axs[2].imshow(stress_tensor[:, :, 1, 0])
    axs[2].set_title("sig_xy", x=0.5, y=0.9, transform=axs[2].transAxes, color="white")

    return fig


def set_axis_attribute(ax, attribute, value):
    for p in ["left", "bottom", "right", "top"]:
        if hasattr(ax.spines[p], attribute):
            try:
                getattr(ax.spines[p], attribute)(value)
            except:
                setattr(ax.spines[p], attribute, value)
        else:
            raise AttributeError("Spines object has no attribute " + attribute)


def get_axis_attribute(ax, attribute):
    l = []
    for p in ["left", "bottom", "right", "top"]:
        l.append(getattr(ax.spines[p], attribute))
    return l


def draw_outline(ax,do=True,lw=2,color="black"):
    if do:
        ax.set_axis_on()
        ax.tick_params(axis="both", which="both", bottom=False, left=False, labelbottom=False,
                       labelleft=False)
        set_axis_attribute(ax, "set_visible", True)
        set_axis_attribute(ax, "set_linewidth", lw)
        set_axis_attribute(ax, "set_color", color)

def name_add(add="", cb=False, dm=False):

    if dm:
        add=add + "ma"
    if cb:
        add=add + "cb"
    return add



def draw_cbar_only(vmin,vmax,aspect=8,shrink=1,cbar_axes_fraction=1.2,cmap="coolwarm",tick_length=4,tick_width=2,labelsize=20,lablecolor="black"):
    # cbar for stress
    fig = plt.figure(figsize=(3.2, 4.75))
    plt.gca().set_axis_off()
    cbar = add_colorbar(vmin=vmin, vmax=vmax, aspect=aspect, shrink=shrink, cbar_axes_fraction=cbar_axes_fraction, cmap=cmap,
                        cbar_style="not-clickpoints")
    set_axis_attribute(cbar.ax, "set_color", "black")
    cbar.ax.tick_params(axis="both", which="both", color="black", length=tick_length, width=tick_width, labelsize=labelsize, labelcolor=lablecolor)
    return fig


def show_forces_forward(fx_f=None,fy_f=None,figsize=None,arrow_scale=None,arrow_width=None
                        ,headlength=None,headwidth=None,headaxislength=None,cmap=None,max_dict=None,cb=None,
                        do=None, at=None, dm=None, types=None, mask=None, display_type=None,
                        mask_fm=None, mask_fm_color=None, out_folder=None, ext=None, add_name="",**kwargs):

        fig, ax = show_quiver(fx_f, fy_f, figsize=figsize, scale_ratio=arrow_scale - 0.03, filter=[0, 10],
                              width=arrow_width,
                              headlength=headlength, headwidth=headwidth,
                              headaxislength=headaxislength, cbar_tick_label_size=30, cmap=cmap,
                              cbar_style="not-clickpoints",
                              vmin=0, vmax=max_dict["force"], plot_cbar=cb)
        draw_outline(ax, do=do)
        add_title(fig, types["f_f"], at=at)
        display_mask(fig, mask, display_type=display_type, dm=dm)
        display_mask(fig, mask_fm, display_type=display_type, color=mask_fm_color, d=np.sqrt(2), dm=dm)
        plt.tight_layout()
        fig.savefig(os.path.join(out_folder, types["f_f"] + name_add(add=add_name, cb=cb, dm=dm) + ext))
        return fig, ax

def general_display(plot_types=[],mask=None,pixelsize=1,display_type="outline",f_type="not circular",cmap="coolwarm"
                ,max_dict=defaultdict(lambda: None),
                    mean_normal_list=None, mask_exp_list=None,out_folder="",fx_f=None,fy_f=None,
                    fx_b=None, fy_b=None, mask_fm=None,mask_fem=None,
                    border_ex_test=None, be_avm_list=None, scalar_comaprisons=None, stress_tensor_f=None,
                    stress_tensor_b=None, key_values=None, plot_gt_exp=True, dm=True, at=True, cb=True, do=True):

    '''
    plot_types=["deformation_forward","deformation_backwards","mask","forces_forward","forces_forward","shear_forward","mean_normal_stress_forward",
    "shear_backward","mean_normal_stress_backward","full_stress_tensor_forward","full_stress_tensor_backward"]

    :param plot_types:
    :param pixelsize:
    :return:
    '''
    figs={}
    createFolder(out_folder)
    types={"def_f":"deformation_forward","def_b":"deformation_backwards","mask":"mask",
          "f_f":"forces_forward","f_b":"forces_backward","st_f":"full_stress_tensor_forward",
    "st_b":"full_stress_tensor_backward","sh_f":"shear_forward","sh_b":"shear_backward",
           "norm_f":"mean_normal_stress_forward","norm_b":"mean_normal_stress_backward",
           "m":"key measures","r":"correlation","exp_test1": "be1","exp_test2" : "be2",
           "exp_test3": "be3", "exp_test4": "be4", "exp_test5": "be5",
           "mask_outline":"mask_outline","cbars":"cbars_only"}

    figsize = (7,7)
    arrow_scale = 0.13 #0.1
    arrow_width = 0.004
    headlength = 4
    headwidth = 4 #6
    headaxislength = 3
    ext = ".svg"
    mask_fm_color = "C2"
    mask_fem_color = "#666666"

    ps_new_ex = 0.845 # pixelsize when using windowsiye 20, overlapp 19.25
    vmax_x_ep = 100 * 0.845
    pd={"figsize" : figsize,
    "arrow_scale"  :arrow_scale,
    "arrow_width"  : arrow_width,
    "headlength"  : headlength,
    "headwidth"  : headwidth,
    "headaxislength"  : headaxislength,
    "ext"  : ext,
    "mask_fm_color"  : mask_fm_color,
    "mask_fem_color"  : mask_fem_color}
    paras={**locals(),**pd}

    if isinstance(mask_fem,np.ndarray):
        mask_fem = mask_fem.astype(bool)


    if types["def_f"] in plot_types or plot_types=="all":
        fig, ax = show_quiver(u_f, v_f, figsize=figsize, scale_ratio=arrow_scale, filter=[0, 5], width=arrow_width,
                              headlength=headlength, headwidth=headwidth,
                                      headaxislength=2, cbar_tick_label_size=30, cmap=cmap, cbar_style="not-clickpoints",
                                      vmin=0,vmax=max_dict["def"], plot_cbar=cb)
        add_title(fig, types["def_f"], at=at)
        draw_outline(ax, do=do)
        display_mask(fig, mask,display_type=display_type,d=np.sqrt(2), dm=dm)
        display_mask(fig, mask_fm, display_type=display_type, color=mask_fm_color,d=np.sqrt(2), dm=dm)
        fig.savefig(os.path.join(out_folder,types["def_f"] + name_add(cb=cb, dm=dm) + ext))
    if types["def_b"] in plot_types or plot_types=="all":
        fig, ax = show_quiver(u_b, v_b, scale_ratio=arrow_scale,filter=[0,5],width=arrow_width,
                              headlength=headlength,headwidth=headwidth,
                                    headaxislength=2,cbar_tick_label_size=30,
                                    cmap=cmap,cbar_style="not-clickpoints",vmin=0,vmax=max_dict["def"], plot_cbar=cb)
        draw_outline(ax, do=do)
        add_title(fig, types["def_b"], at=at)
        display_mask(fig, mask,display_type=display_type, dm=dm)
        display_mask(fig, mask_fm, display_type=display_type,color=mask_fm_color,d=np.sqrt(2), dm=dm)
        fig.savefig(os.path.join(out_folder,  types["def_b"] + name_add(cb=cb, dm=dm) + ext))

    if types["cbars"] in plot_types or plot_types=="all":

        # cbar for stress
        fig = plt.figure(figsize=(3.2, 4.75))
        plt.gca().set_axis_off()
        cbar=add_colorbar(vmin=0, vmax=1+0.01,aspect=8, shrink=1, cbar_axes_fraction=1.2, cmap=cmap, cbar_style="not-clickpoints")
        set_axis_attribute(cbar.ax, "set_color", "black")
        cbar.ax.tick_params(axis="both", which="both", color="black",length=4, width=2, labelsize=20, labelcolor="black")
        fig.savefig(os.path.join(out_folder, types["cbars"] + "force" + name_add(cb=cb, dm=dm) + ext))

        # cbar for stress
        fig = plt.figure(figsize=(3.2, 4.75))
        plt.gca().set_axis_off()
        cbar = add_colorbar(vmin=0, vmax=1 + 0.01, aspect=8, shrink=1, cbar_axes_fraction=1.2, cmap=cmap,
                            cbar_style="not-clickpoints")
        set_axis_attribute(cbar.ax, "set_color", "black")
        cbar.ax.tick_params(axis="both", which="both", color="black", length=4, width=2, labelsize=20,
                            labelcolor="black")
        fig.savefig(os.path.join(out_folder, types["cbars"] + "stress" + name_add(cb=cb, dm=dm) + ext))


    if types["mask"] in plot_types or plot_types=="all":

        fig=plt.figure()
        plt.imshow(mask)
        add_title(fig, types["mask"], at=at)
        fig.savefig(os.path.join(out_folder, types["mask"] + ext))

    if types["mask_outline"] in plot_types or plot_types=="all":

        fig = plt.figure()
        plt.imshow(np.zeros(fx_f.shape),cmap=cmap,vmin=0,vmax=1)
        draw_outline(plt.gca(),do=do)
        display_mask(fig, mask, display_type="outline", color="C1", dm=True)
        display_mask(fig, mask_fm, display_type="outline", color=mask_fm_color, d=np.sqrt(2), dm=True)
        display_mask(fig, mask_fem, display_type="outline", color=mask_fem_color, d=np.sqrt(2), dm=True)

    if types["f_f"] in plot_types or plot_types=="all":
        show_forces_forward(**paras)

    if types["f_b"] in plot_types or plot_types=="all":

        if f_type == "circular":
            fx_filtered, fy_filtered = filter_arrows_for_square(fx_b,fy_b,filter=12) # only works when initial forces are circular
            fig, ax = show_quiver(fx_filtered, fy_filtered, figsize=figsize, scale_ratio=arrow_scale, filter=[0, 0], width=arrow_width,
                                  headlength=headlength, headwidth=headwidth,
                                      headaxislength=headaxislength, cbar_tick_label_size=30, cmap=cmap, cbar_style="not-clickpoints",
                                      vmin=0,vmax=max_dict["force"], plot_cbar=cb)
            im = fig.axes[0].imshow(np.sqrt(fx_b**2+fy_b**2),cmap=cmap,
                                      vmin=0,vmax=max_dict["force"])
            if cb:
                fig.axes[1].remove()
                cb = plt.colorbar(im)
                cb.ax.tick_params(labelsize=30)

            plt.tight_layout()
        else:
            fx_filtered, fy_filtered=fx_b,fy_b
            fig, ax = show_quiver(fx_filtered, fy_filtered, figsize=figsize, scale_ratio=arrow_scale - 0.03, filter=[0, 10],
                                  width=arrow_width,
                                  headlength=headlength, headwidth=headwidth,
                                  headaxislength=headaxislength, cbar_tick_label_size=30, cmap=cmap,
                                  cbar_style="not-clickpoints",
                                  vmin=0, vmax=max_dict["force"], plot_cbar=cb)
        draw_outline(ax, do=do)
        add_title(fig, types["f_b"], at=at)
        display_mask(fig, mask, display_type=display_type, dm=dm)
        display_mask(fig, mask_fm, display_type=display_type, color=mask_fm_color,d=np.sqrt(2), dm=dm)
        plt.tight_layout()
        fig.savefig(os.path.join(out_folder, types["f_b"] + name_add(cb=cb, dm=dm) + ext))

    if types["sh_f"] in plot_types or plot_types=="all":
        shear = stress_tensor_f[:, :, 0, 1]  # shear component of the stress tensor
        fig,ax = show_map_clickpoints(shear, show_mask=mask_fem, figsize=figsize, cbar_style="out", cmap=cmap,
                                      cbar_tick_label_size=30, vmin=0,vmax=max_dict["stress"], plot_cbar=cb)
        draw_outline(ax, do=do)
        add_title(fig,types["sh_f"], at=at)
        display_mask(fig, mask,display_type=display_type, dm=dm)
        plt.tight_layout()
        fig.savefig(os.path.join(out_folder, types["sh_f"] + name_add(cb=cb, dm=dm) + ext))
    if types["norm_f"] in plot_types or plot_types=="all":
        mean_normal_stress = ((stress_tensor_f[:, :, 0, 0] + stress_tensor_f[:, :, 1, 1]) / 2)
        mean_normal_stress[~mask_fem] = np.nan
        fig,ax = show_map_clickpoints(mean_normal_stress, show_mask=mask_fem, figsize=figsize, cbar_style="out", background_color="white",
                                      cmap=cmap,
                                      cbar_tick_label_size=30,vmin=0,vmax=max_dict["stress"], plot_cbar=cb)
        draw_outline(ax, do=do)
        add_title(fig, types["norm_f"], at=at)
        display_mask(fig, mask, display_type=display_type, dm=dm)
        plt.tight_layout()
        display_mask(fig, mask_fem, display_type=display_type, color=mask_fem_color, d=np.sqrt(2), dm=dm)
        fig.savefig(os.path.join(out_folder, types["norm_f"] + name_add(cb=cb, dm=dm) + ext))

    if types["sh_b"] in plot_types or plot_types=="all":
        shear = stress_tensor_b[:, :, 0, 1]  # shear component of the stress tensor
        fig,ax = show_map_clickpoints(shear,show_mask=mask_fem, figsize=figsize, cbar_style="out",cmap=cmap,
                                      cbar_tick_label_size=30,vmin=0,vmax=max_dict["stress"], plot_cbar=cb)
        display_mask(fig, mask,display_type=display_type, dm=dm)
        draw_outline(ax, do=do)
        add_title(fig,types["sh_b"], at=at)
        plt.tight_layout()
        fig.savefig(os.path.join(out_folder, types["sh_b"] + name_add(cb=cb, dm=dm) + ext))

    if types["norm_b"] in plot_types or plot_types=="all":
        mean_normal_stress = ((stress_tensor_b[:, :, 0, 0] + stress_tensor_b[:, :, 1,1]) / 2)
        mean_normal_stress[~mask_fem]=np.nan
        fig, ax = show_map_clickpoints(mean_normal_stress,show_mask=np.ones(mean_normal_stress.shape), figsize=figsize, cbar_style="out",background_color="white",
                                      cmap=cmap, cbar_tick_label_size=30, vmin=0,vmax=max_dict["stress"], plot_cbar=cb)
        draw_outline(ax,do=do)
        add_title(fig, types["norm_b"], at=at)
        display_mask(fig, mask, display_type=display_type, dm=dm)
        display_mask(fig, mask_fem, display_type=display_type, color=mask_fem_color, d=np.sqrt(2), dm=dm)
        plt.tight_layout()
        fig.savefig(os.path.join(out_folder, types["norm_b"] + name_add(cb=cb, dm=dm) + ext))

    if types["st_f"] in plot_types or plot_types=="all":
        fig = display_stress_tensor(stress_tensor_f,mask, title_str=types["st_f"])
        display_mask(fig, mask, display_type=display_type, type=2, dm=dm)
        plt.tight_layout()
        fig.savefig(os.path.join(out_folder, types["st_f"] + name_add(cb=cb, dm=dm) + ext))

    if types["st_b"] in plot_types or plot_types=="all":
        fig = display_stress_tensor(stress_tensor_b,mask, title_str=types["st_b"])
        display_mask(fig, mask, display_type=display_type, type=2, dm=dm)
        plt.tight_layout()
        fig.savefig(os.path.join(out_folder, types["st_b"] + name_add(cb=cb, dm=dm) + ext))

    if types["m"] in plot_types or plot_types=="all":
        values_r = list(chain.from_iterable([[key_values[i]/key_values[i],key_values[i+1]/key_values[i]] for i in range(0,len(key_values),2)]))
        lables=["strain energy","strain energy","contractility","contractility",
                "mean normal stress","mean normal stress","mean shear stress","mean shear stress"]
        pos = list(chain.from_iterable([[p-0.2,p+0.2] for p in range(int(len(key_values)/2))]))
        fig = plt.figure()
        #plt.bar(pos[::2],values_r[::2],width=0.4, color="#729fcf",label="backwards",alpha=0.83)
        #plt.bar(pos[1::2], values_r[1::2], width=0.4, color="#cc0066",label="forwards",alpha=0.83)
        plt.bar(pos[::2],values_r[::2],width=0.4, color="C1",label="backwards",alpha=1)
        plt.bar(pos[1::2], values_r[1::2], width=0.4, color="C2",label="forwards",alpha=1)
        for px,py,t in zip(pos[1::2],values_r[1::2],[str(x) for x in np.round(np.array(values_r[1::2]),2)]):
            if py < np.inf:
                print(px,py,t)
                plt.text(px, py - 0.01, t, color="black", fontsize=20, horizontalalignment="center", verticalalignment="bottom")

        #plt.xticks(pos,lables,rotation="70",fontsize=15)
        plt.gca().tick_params(axis="both", which="both", color="black",length=4, width=2, labelsize=20, labelcolor="black",labelbottom=False)
        set_axis_attribute(plt.gca(),"set_color","black")
        set_axis_attribute(plt.gca(), "set_linewidth", 2)
        if at:
            plt.title(types["m"])
        plt.tight_layout()
        fig.savefig(os.path.join(out_folder, types["m"] + ext))

    if types["r"] in plot_types or plot_types=="all":
        rs={key:value['r_squared'] for key,value in scalar_comaprisons.items() if not np.isnan(value['r_squared'])}
        fig = plt.figure(figsize=(3.2,4.75))
        pos=[1,1.7]
        plt.bar(pos, list(rs.values()), width=0.4, color="C5")
        #plt.xticks(rotation="70",fontsize=15)
        plt.xticks(pos)
        plt.gca().tick_params(axis="both", which="both", color="black", length=4, width=2, labelsize=20,
                              labelcolor="black", labelbottom=False)
        set_axis_attribute(plt.gca(), "set_color", "black")
        set_axis_attribute(plt.gca(), "set_linewidth", 2)
        if at:
            plt.title(types["r"])
        plt.ylim((0,1))
        plt.tight_layout()
        fig.savefig(os.path.join(out_folder, types["r"] + ext))

    if types["exp_test1"] in plot_types or plot_types=="all" and len(mean_normal_list)>0:

        fig = show_exp_test(mean_normal_list=mean_normal_list,max_dict=max_dict,mask_exp_list=mask_exp_list)
        fig.savefig(os.path.join(out_folder, types["exp_test1"] + ext))

    if types["exp_test2"] in plot_types or plot_types=="all" and len(mean_normal_list)>0:
    # average normal stress relative to groundtruth stress
        fig = plt.figure()
        be = np.array(border_ex_test) * ps_new_ex
        if plot_gt_exp:
            plt.plot(be, be_avm_list, color="C3", linewidth=5)
            plt.plot(be, [1]*(len(be_avm_list)),color="C4", linewidth=5)
            plt.ylim((0, max_dict["stress"] * 1.2))
        else:
            plt.plot(be, be_avm_list, color="C3", linewidth=5)
            plt.ylim((0, max_dict["stress"] * 1.2))
        plt.xlim(0, vmax_x_ep)
        plt.gca().tick_params(axis="both", which="both", color="black", length=4, width=2, labelsize=20,
                          labelcolor="black")
        set_axis_attribute(plt.gca(), "set_color", "black")
        set_axis_attribute(plt.gca(), "set_linewidth", 2)

       # plt.title(types["exp_test2"])
        plt.tight_layout()
        fig.savefig(os.path.join(out_folder, types["exp_test2"] + ext))

    if types["exp_test3"] in plot_types or plot_types=="all" and len(mean_normal_list)>0:
        # displaying forces and masks
        nf = createFolder(os.path.join(out_folder, "exp_plots_forces"))
        for i, m_exp in enumerate(mask_exp_list):
            pl = copy.deepcopy(paras)
            pl["dm"] = True
            pl["mask_fm"] = m_exp.astype(bool)
            pl["add_name"]="m_exp"+ str(i)
            pl["out_folder"]=nf
            try:
                fig, ax = show_forces_forward(**pl)
            except RecursionError:
                pass

    if types["exp_test4"] in plot_types or plot_types=="all" and len(mean_normal_list)>0:
        sub_folder_stress = createFolder(os.path.join(out_folder,"stresses"))
        sub_folder_force = createFolder(os.path.join(out_folder, "forces"))
        for i,(ms,mask_expand) in enumerate(zip(mean_normal_list,mask_exp_list)):
            fig, ax = show_map_clickpoints(ms, cbar_style="out", figsize=figsize, cmap=cmap, cbar_tick_label_size=30, vmin=0,
                                   vmax=max_dict["stress"])
            add_title(fig, types["norm_b"], at=at)
            display_mask(fig, mask, display_type=display_type, color="#FFEF00")
            display_mask(fig, mask_expand, display_type=display_type,color="C3")
            fig.savefig(os.path.join(sub_folder_stress, types["exp_test4"] + "%s"%str(i)+ ext))

            fig, ax = show_quiver(fx_f, fy_f, figsize=figsize, scale_ratio=arrow_scale, filter=[0, 10], width=arrow_width, headlength=3,
                              headwidth=4,
                              headaxislength=2, cbar_tick_label_size=30, cmap=cmap, cbar_style="not-clickpoints",
                              vmin=0, vmax=1600)
            add_title(fig, types["f_f"], at=at)
            display_mask(fig, mask, display_type=display_type, color="#FFEF00", dm=dm)
            display_mask(fig, mask_expand, display_type=display_type, color="C3", dm=dm)
            plt.tight_layout()
            fig.savefig(os.path.join(sub_folder_force, types["exp_test4"] + "%s"%str(i)+ ext))

    if types["exp_test5"] in plot_types or plot_types=="all" and len(mean_normal_list)>0:
        pl = copy.deepcopy(paras)
        pl["dm"] = False
        pl["figsize"] = (np.mean(paras["figsize"])*mask.shape[1]/mask.shape[0],np.mean(paras["figsize"])*1.022*mask.shape[0]/mask.shape[1])
        try:
            fig, ax = show_forces_forward(**pl)
            ax.set_xlim(-0.5,0.5+mask.shape[1])
            ax.set_ylim(0.5 + mask.shape[0],-0.5)
            add_title(fig, types["f_f"], at=at)

            be = np.array(border_ex_test) * ps_new_ex

            #display_mask(fig, mask_exp_list[0], display_type=display_type, color=mask_fm_color, d=np.sqrt(2), dm=True, lw=7)
            max_id = np.argmax(be_avm_list)
            #max_id=23
            display_mask(fig, mask_exp_list[max_id], display_type=display_type, color=mask_fm_color, d=np.sqrt(2), dm=True, lw=7)
            end_id=np.argmin(np.abs(be-vmax_x_ep))
            display_mask(fig, mask_exp_list[end_id], display_type=display_type, color=mask_fm_color, d=np.sqrt(2),
                         dm=True, lw=7)
            display_mask(fig, mask, display_type=display_type, color="C1", dm=True, lw=7)
            ax.set_position([0,0,1,1])
            fig.set_frameon(False)
            if ext==".svg":
                fig.savefig(os.path.join(out_folder, types["exp_test5"] + ext))
            else:
                fig.savefig(os.path.join(out_folder, types["exp_test5"] + ext),dpi=300)


        except RecursionError:
            pass




def show_exp_test(mean_normal_list=None,max_dict=None,mask_exp_list=None):
    n=int(np.ceil(np.sqrt(len(mean_normal_list))))
    fig,axs=plt.subplots(n,n)
    axs=axs.flatten()
    for i in range(len(mean_normal_list)):
        axs[i].imshow(mean_normal_list[i],vmax=max_dict["stress"])
        axs[i].set_title("mean normal stress #%s"%str(i), x=0.5, y=0.9, transform=axs[i].transAxes, color="white")
        display_mask(fig, mask_exp_list[i], display_type="outline", type=1, color="C1", d=np.sqrt(2), ax=axs[i])

    return fig
def plot_gradient_normal_stress(stress_tensor):

    dsxx_x = np.gradient(stress_tensor[:, :, 0, 0], axis=1)
    dsyy_y = np.gradient(stress_tensor[:, :, 1, 1], axis=0)
    dsxx_y = np.gradient(stress_tensor[:, :, 0, 0], axis=0)
    dsyy_x = np.gradient(stress_tensor[:, :, 1, 1], axis=1)

    fig, axs = plt.subplots(2, 2)
    plt.suptitle("gradient")
    im = axs[0,0].imshow(dsxx_x)
    axs[0,0].set_title("dsxx_x", x=0.5, y=0.9, transform=axs[0,0].transAxes, color="white")
    im = axs[0,1].imshow(dsyy_y)
    axs[0,1].set_title("dsyy_y", x=0.5, y=0.9, transform=axs[0,1].transAxes, color="white")
    im = axs[1,0].imshow(dsxx_y)
    axs[1,0].set_title("dsxx_y", x=0.5, y=0.9, transform=axs[1,0].transAxes, color="white")
    im = axs[1,1].imshow(dsyy_x)
    axs[1,1].set_title("dsyy_x", x=0.5, y=0.9, transform=axs[1,1].transAxes, color="white")

def add_title(fig,title_str,at=True):
    if at:
        ax = fig.axes[0]
        ax.set_title(title_str, x=0.5, y=0.9, transform=ax.transAxes, color="white")

def add_mask(fig,mask):
    mask_show = make_display_mask(mask)
    ax = fig.axes[0]
    ax.imshow(mask,alpha=0.4)

def filter_arrows_for_square(fx,fy,filter=6):
    mask_filtered=np.zeros(fx.shape)
    fx_filtered, fy_filtered=np.zeros(fx.shape),np.zeros(fx.shape)

    mask_uf=np.logical_or(fx!=0,fy!=0)
    out_line_graph, points = mask_to_graph(mask_uf, d=np.sqrt(2))
    circular_path = find_path_circular(out_line_graph, 0)
    circular_path=[x for i,x in enumerate(circular_path) if i%filter==0]
    circular_path.append(circular_path[0])  # to plot a fully closed loop
    mask_filtered[points[circular_path][:,0],points[circular_path][:,1]]=1
    mask_filtered=mask_filtered.astype(bool)

    fx_filtered[mask_filtered] = fx[mask_filtered]
    fy_filtered[mask_filtered] = fy[mask_filtered]
    return fx_filtered, fy_filtered

from scipy.signal import convolve2d

def custom_edge_filter(arr):
    arr_out = copy.deepcopy(arr).astype(int)
    shape1 = np.array([[0, 1, 0], [1, 1, 0], [0, 0, 0]])
    shape2 = np.array([[0, 1, 0], [0, 1, 1], [0, 0, 0]])
    shape3 = np.array([[0, 0, 0], [0, 1, 1], [0, 1, 0]])
    shape4 = np.array([[0, 0, 0], [1, 1, 0], [0, 1, 0]])
    for s in [shape1,shape2,shape3,shape4]:
        rem_mask=convolve2d(arr,s,mode="same")==3
        arr_out[rem_mask]=0
    return arr_out.astype(bool)
