# function to simulate the surface deformation from point forces applied to a
# half sphere. Also includes a function a finetely thik halfsphere is considered.





from tqdm import tqdm
from scipy.integrate import quad
from scipy.special import jv # first order bessel function
import sys
sys.path.insert(0, '/media/user/GINA1-BK/Andreas-Python/tracktion_force_microscopy/')
from TFM_functions import *
from functions_for_cell_colonie import *
from scipy.ndimage.morphology import distance_transform_edt
from scipy.signal import convolve2d
from skimage.filters import gaussian

def reverse_kernel(k): # not necessary because kernel is symmetric anyway
    '''
    "flips kernel by 180 degrees"
    '''
    k=np.flip(k,axis=0)
    k=np.flip(k,axis=1)
    return k


def get_xy_for_quiver(u):
    xs=np.zeros(np.shape(u))
    for i in range(np.shape(u)[0]):
        xs[i,:]=np.arange(0,np.shape(u)[1],1)
    ys = np.zeros(np.shape(u))
    for j in range(np.shape(u)[1]):  ## is inverted in other skript...
        ys[:, j] = np.arange(0,np.shape(u)[0], 1)
    return xs, ys



def force_from_center(Force_magnitude,pos1,pos2):
    new_center = np.array([np.mean([pos1[0], pos2[0]]), np.mean([pos1[1], pos2[1]])])  # new exact center position
    F1 = (pos1 - new_center) * Force_magnitude / np.linalg.norm(pos1 - new_center)  # first force
    F2 = (pos2 - new_center) * Force_magnitude / np.linalg.norm(pos2 - new_center)  # first force
    return F1,F2
#plt.close("all")


def return_force_coordinate_with_offset(fx):
    '''
    deformation exactly at force origin is infinetly large. (point force is not real phyyical appearance)
    therefore it is necassary to let the force act on points between the actual positions
    :param fx:
    :return:
    '''
    pixx = np.arange(fx.shape[0])
    pixy = np.arange(fx.shape[1])
    dist_x, dist_y = np.meshgrid(pixy, pixx)
    dist_x=dist_x.astype("float64")
    dist_y=dist_y.astype("float64")
    dist_x+=0.5
    dist_y+=0.5
    return dist_x,dist_y


def deformation_from_forces(fx,fy,coords_x,coords_y,young,sigma,pixelsize):  ## there should be a much better solution to this...
    '''
    calculating the deformation fieldgiven a tracktion force field using the boussiinesq solution for an
    infinte half sphere of an lineary isotropic elastic material
    :param fx: forces in x direction
    :param fy: forces iny direction
    :param fx_coords: coordinates of these forces shifted by 0.5 pixel. shift is necessayr because we assume point load
    :param fy_coords:
    :param young: youngs modulus of material
    :param sigma: poissonratio of material
    :return:
    '''
    A = (1 + sigma) / (np.pi * young) # a constant factor for boussinesq kernel

    pixx = np.arange(fx.shape[0])
    pixy = np.arange(fx.shape[1])
    dist_x, dist_y = np.meshgrid(pixy, pixx) # matrices of distance

    def_x = np.zeros(fx.shape)
    def_y = np.zeros(fy.shape)

    iter = zip(fx.flatten(), fy.flatten(), coords_x.flatten(),
               coords_y.flatten())  # iterator over all forces and points
    for f_x, f_y, f_pos_x, f_pos_y in tqdm(iter, total=len(fx.flatten())):
        if f_x != 0 or f_y != 0:
            x = (dist_x - f_pos_x) * pixelsize  # distances to origin of force
            y = (dist_y - f_pos_y) * pixelsize
            r = np.sqrt(x ** 2 + y ** 2)
            K1 = ((1 - sigma) * (r ** 2) + sigma * (x ** 2)) * (
                        A / (r ** 3))  # components of the boussinesq kernel (? nameing?)
            K2 = sigma * x * y * (A / (r ** 3))
            K3 = ((1 - sigma) * (r ** 2) + sigma * (y ** 2)) * (A / (r ** 3))
            def_x += f_x * K1 + f_y * K2  # deformations in m
            def_y += f_x * K2 + f_y * K3
    return def_x,def_y



def infinite_thickness_convolution(fx,fy,pixelsize,young,sigma,kernel_size=None):  ## there should be a much better solution to this...
    '''
    calculating the deformation fieldgiven a tracktion force field using the boussiinesq solution for an
    infinte half sphere of an lineary isotropic elastic material
    :param fx: forces in x direction
    :param fy: forces iny direction
    :param fx_coords: coordinates of these forces shifted by 0.5 pixel. shift is necessayr because we assume point load
    :param fy_coords:
    :param young: youngs modulus of material
    :param sigma: poisson ratio of material
    :return:
    '''

    # distance for the convolution kernel
    if not kernel_size:
        kernel_size = fx.shape

    pixx = np.arange(kernel_size[1])
    pixy = np.arange(kernel_size[0])
    dist_x, dist_y = np.meshgrid(pixy, pixx)  # matrices of distance
    dist_x = dist_x.astype(float)
    dist_y = dist_y.astype(float)
    # makeing sure coorinates are shifted and distance is never exactly zero ... (maybe just exlude zero????)
    if np.mean(dist_x[0, :]).is_integer() or np.mean(dist_y[:, 0]).is_integer():
        dist_x -= np.mean(dist_x[0, :]) - 0.5  # centering
        dist_y -= np.mean(dist_y[:, 0]) - 0.5
    else:
        dist_x -= np.mean(dist_x[0, :])  # centering
        dist_y -= np.mean(dist_y[:, 0])

    dist_x = dist_x * pixelsize
    dist_y = dist_y * pixelsize
    r=np.sqrt(dist_x**2+dist_y**2)

    # convolution kernels
    A = (1 + sigma) / (np.pi * young)  # a constant factor for boussinesq kernel
    conv_k1=((1 - sigma) * (r ** 2) + sigma * (dist_x ** 2)) * (
                    A / (r ** 3))  # components of the boussinesq kernel (? nameing?)
    conv_k2= sigma * dist_x * dist_y * (A / (r ** 3))
    conv_k3=((1 - sigma) * (r ** 2) + sigma * (dist_y ** 2)) * (A / (r ** 3))





    #deformation by convolution with the kernels
    def_x = convolve2d(fx, conv_k1, mode="same", boundary="fill", fillvalue=0) + convolve2d(fy, conv_k2, mode="same", boundary="fill", fillvalue=0)
    def_y = convolve2d(fx, conv_k2, mode="same", boundary="fill", fillvalue=0) + convolve2d(fy, conv_k3, mode="same", boundary="fill", fillvalue=0)

    return def_x,def_y


def finite_thickness(fx, fy, h, young,pixelsize, coords_x, coords_y, sigma=0.5):
    '''
    calculating the deformation fieldgiven a tracktion force field using the boussiinesq solution for an
     half sphere with finite thickness
     # employs the approximate greens tensor from

     Cell Force Microscopy on Elastic Layers of Finite Thickness
     Rudolf Merkel, Norbert Kirchgeßner, Claudia M. Cesa, and Bernd Hoffman
     Biophysical Journal  Volume 93  November 2007

     This approximation is only spposed to be used for sigma=0.5

    :param fx: forces in x direction
    :param fy: forces iny direction
    :param fx_coords: coordinates of these forces shifted by 0.5 pixel. shift is necessary because we assume point load
    :param fy_coords:
    :param young: youngs modulus of material
    :param sigma: poisson ratio of material
    :return:
    '''

    # distance for the convolution kernel

    # greens tensor with:
    # [K1,K2,K3]
    # [K4,K5,K6]
    # [K7,K8,K9]
    # returns displacement also in z direction (makes sense because of "pulling" at the buttom of the layer)

    E = young


    pixx = np.arange(fx.shape[0])
    pixy = np.arange(fx.shape[1])
    dist_x, dist_y = np.meshgrid(pixy, pixx) # matrices of distance

    def_x = np.zeros(fx.shape)
    def_y = np.zeros(fy.shape)
    def_z= np.zeros(fy.shape)

    iter = zip(fx.flatten(), fy.flatten(), coords_x.flatten(),
               coords_y.flatten())  # iterator over all forces and points
    for f_x, f_y, f_pos_x, f_pos_y in tqdm(iter, total=len(fx.flatten())):
        if f_x != 0 or f_y != 0:

            x = (dist_x - f_pos_x) * pixelsize  # distances to origin of force
            y = (dist_y - f_pos_y) * pixelsize
            r = np.sqrt(x ** 2 + y ** 2)

            ### elements of the greens tensor
            # Usefull parts // this is just an approximation
            # /also only for sigma=0.49
            s = r / h
            mu = E / (2 * (1 + sigma))
            A1 = ((2 - sigma) / (4 * np.pi * mu * h * s)) * (0.12 * np.exp(-0.43 * s) + 0.88 * np.exp(-0.83 * s))
            A2 = -(sigma / (4 * np.pi * mu * h * s)) * (1 + 1.22 * s + 1.31 * (s ** 2.23)) * np.exp(-1.25 * s)
            # A3_b = ((1-2*sigma)/(4*np.pi*mu*h*s))
            A3 = -0.063 * ((np.exp(-0.44 * s) - np.exp(-2.79 * s)) ** 2)  # *A3_b
            A4 = ((2 * (1 - sigma)) / (4 * np.pi * mu * h * s)) * (1 + 0.46 * s - 2.50 * (s ** 2.13)) * np.exp(
                -2.18 * s)

            # componenets of the greesn tensor
            K1 = A1 - (( x ** 2 - y ** 2) / (r ** 2)) * A2
            K2 = -(2 *  x * y / (r ** 2)) * A2
            K3 = -( x / r) * A3
            K4 = -(2 *  x * y / (r ** 2)) * A2  # is K2
            K5 = A1 + ((x ** 2 - y ** 2) / (r ** 2)) * A2
            K6 = -(y / r) * A3
            K7 = ( x / r) * A3
            K8 = (y / r) * A3
            K9 = A4

            def_x += f_x * K1 + f_y * K2  # deformations in m
            def_y += f_x * K4 + f_y * K5
            def_z += f_x * K7 + f_y * K8
    return def_x, def_y, def_z




def finite_thickness_convolution_greens_tensor(fx, fy,pixelsize, h, young, sigma=0.5,kernel_size=None):
    '''
    calculating the deformation fieldgiven a tracktion force field using the boussinesq solution for an
     half sphere with finite thickness
     # employs the approximate greens tensor from

     Cell Force Microscopy on Elastic Layers of Finite Thickness
     Rudolf Merkel, Norbert Kirchgeßner, Claudia M. Cesa, and Bernd Hoffman
     Biophysical Journal  Volume 93  November 2007

     This approximation is only spposed to be used for sigma=0.5

    :param fx: forces in x direction
    :param fy: forces iny direction
    :param fx_coords: coordinates of these forces shifted by 0.5 pixel. shift is necessayr because we assume point load
    :param fy_coords:
    :param young: youngs modulus of material
    :param sigma: poisson ratio of material
    :return:
    '''

    # distance for the convolution kernel

    # greens tensor with:
    # [K1,K2,K3]
    # [K4,K5,K6]
    # [K7,K8,K9]
    # returns displacement also in z direction (makes sense because of "pulling" at the buttom of the layer)

    E = young

    if not kernel_size:
        kernel_size=fx.shape

    pixx = np.arange(kernel_size[1])
    pixy = np.arange(kernel_size[0])
    dist_x, dist_y = np.meshgrid(pixy, pixx)  # matrices of distance
    dist_x=dist_x.astype(float)
    dist_y = dist_y.astype(float)
    # makeing sure coorinates are shifted and distance is never exactly zero ... (maybe just exlude zero????)
    if np.mean(dist_x[0,:]).is_integer() or np.mean(dist_y[:, 0]).is_integer():
        dist_x -= np.mean(dist_x[0, :])-0.5  # centering
        dist_y -= np.mean(dist_y[:, 0])-0.5
    else:
        dist_x -= np.mean(dist_x[0,:]) # centering
        dist_y -= np.mean(dist_y[:, 0])

    dist_x= dist_x* pixelsize
    dist_y = dist_y* pixelsize

    r=np.sqrt(dist_x**2+dist_y**2)


    ### elements of the greens tensor
    # Usefull parts // this is just an approximation
    # /also only for sigma=0.49
    s = r / h
    mu = E / (2 * (1 + sigma))
    A1 = ((2 - sigma) / (4 * np.pi * mu * h * s)) * (0.12 * np.exp(-0.43 * s) + 0.88 * np.exp(-0.83 * s))
    A2 = -(sigma / (4 * np.pi * mu * h * s)) * (1 + 1.22 * s + 1.31 * (s ** 2.23)) * np.exp(-1.25 * s)
    #A3_b = ((1-2*sigma)/(4*np.pi*mu*h*s))
    A3 = -0.063 * ((np.exp(-0.44 * s) - np.exp(-2.79 * s)) ** 2)#*A3_b
    A4 = ((2 * (1 - sigma)) / (4 * np.pi * mu * h * s)) * (1 + 0.46 * s - 2.50 * (s ** 2.13)) * np.exp(-2.18 * s)

    # componenets of the greesn tensor
    K1 = A1 - ((dist_x ** 2 - dist_y ** 2) / (r ** 2)) * A2
    K2 = -(2 * dist_x * dist_y / (r ** 2)) * A2
    K3 = -(dist_x / r) * A3
    K4 = -(2 * dist_x * dist_y / (r ** 2)) * A2  # is K2
    K5 = A1 + ((dist_x ** 2 - dist_y ** 2) / (r ** 2)) * A2
    K6 = -(dist_y / r) * A3
    K7 = (dist_x / r) * A3
    K8 = (dist_y / r) * A3
    K9 = A4




    return ([K1,K2,K3,K4,K5,K6,K7,K8,K9],[A1,A2,A3,A4])




def finite_thickness_convolution(fx, fy,pixelsize, h, young, sigma=0.5,kernel_size=None):
    '''
    calculating the deformation fieldgiven a tracktion force field using the boussinesq solution for an
     half sphere with finite thickness
     # employs the approximate greens tensor from
     #### only supposed to work for sigma=0.5

     Cell Force Microscopy on Elastic Layers of Finite Thickness
     Rudolf Merkel, Norbert Kirchgeßner, Claudia M. Cesa, and Bernd Hoffman
     Biophysical Journal  Volume 93  November 2007

     This approximation is only spposed to be used for sigma=0.5

    :param fx: forces in x direction
    :param fy: forces iny direction
    :param fx_coords: coordinates of these forces shifted by 0.5 pixel. shift is necessayr because we assume point load
    :param fy_coords:
    :param young: youngs modulus of material
    :param sigma: poisson ratio of material
    :return:
    '''

    # distance for the convolution kernel

    # greens tensor with:
    # [K1,K2,K3]
    # [K4,K5,K6]
    # [K7,K8,K9]
    # returns displacement also in z direction (makes sense because of "pulling" at the buttom of the layer)

    E = young

    if not kernel_size:
        kernel_size=fx.shape
    fx=fx.astype(np.float128)
    fy = fy.astype(np.float128)
    pixx = np.arange(kernel_size[1])
    pixy = np.arange(kernel_size[0])
    dist_x, dist_y = np.meshgrid(pixy, pixx)  # matrices of distance
    dist_x=dist_x.astype(np.float)
    dist_y = dist_y.astype(np.float)
    # makeing sure coorinates are shifted and distance is never exactly zero ... (maybe just exlude zero????)
    if np.mean(dist_x[0,:]).is_integer() or np.mean(dist_y[:, 0]).is_integer():
        dist_x -= np.mean(dist_x[0, :])-0.5  # centering
        dist_y -= np.mean(dist_y[:, 0])-0.5
    else:
        dist_x -= np.mean(dist_x[0,:]) # centering
        dist_y -= np.mean(dist_y[:, 0])

    dist_x=dist_x.astype(np.float128)
    dist_y = dist_y.astype(np.float128)

    dist_x= dist_x* pixelsize
    dist_y = dist_y* pixelsize

    r=np.sqrt(dist_x**2+dist_y**2)


    ### elements of the greens tensor
    # Usefull parts // this is just an approximation
    # /also only for sigma=0.49
    s = r / h
    mu = E / (2 * (1 + sigma))
    A1 = ((2 - sigma) / (4 * np.pi * mu * h * s)) * (0.12 * np.exp(-0.43 * s) + 0.88 * np.exp(-0.83 * s))
    A2 = -(sigma / (4 * np.pi * mu * h * s)) * (1 + 1.22 * s + 1.31 * (s ** 2.23)) * np.exp(-1.25 * s)
    # A3_b = ((1-2*sigma)/(4*np.pi*mu*h*h/r))
    A3 = -0.063 * ((np.exp(-0.44 * s) - np.exp(-2.79 * s)) ** 2)
    #A4 = ((2 * (1 - sigma)) / (4 * np.pi * mu * h * s)) * (1 + 0.46 * s - 2.50 * (s ** 2.13)) * np.exp(-2.18 * s)

    # componenets of the greesn tensor
    K1 = A1 - ((dist_x ** 2 - dist_y ** 2) / (r ** 2)) * A2
    K2 = -(2 * dist_x * dist_y / (r ** 2)) * A2
    #K3 = -(dist_x / r) * A3
    K4 = -(2 * dist_x * dist_y / (r ** 2)) * A2  # is K2
    K5 = A1 + ((dist_x ** 2 - dist_y ** 2) / (r ** 2)) * A2
    #K6 = -(dist_y / r) * A3
    K7 = (dist_x / r) * A3
    K8 = (dist_y / r) * A3
    #K9 = A4





    #deformation by convolution with the kernels
    def_x = convolve2d(fx, K1, mode="same", boundary="fill", fillvalue=0) + convolve2d(fy, K2, mode="same", boundary="fill", fillvalue=0)
    def_y = convolve2d(fx, K4, mode="same", boundary="fill", fillvalue=0) + convolve2d(fy, K5, mode="same", boundary="fill", fillvalue=0)
    def_z = convolve2d(fx, K7, mode="same", boundary="fill", fillvalue=0) + convolve2d(fy, K8, mode="same", boundary="fill", fillvalue=0)


    return def_x,def_y,def_z


def finite_thickenss_convolution_exact(fx, fy,pixelsize, h, young, sigma=0.5,kernel_size=None):
    '''
       calculating the deformation fieldgiven a tracktion force field using the boussinesq solution for an
        half sphere with finite thickness
        # employs the approximate greens tensor from

        Cell Force Microscopy on Elastic Layers of Finite Thickness
        Rudolf Merkel, Norbert Kirchgeßner, Claudia M. Cesa, and Bernd Hoffman
        Biophysical Journal  Volume 93  November 2007

        This is the "exact solution

       :param fx: forces in x direction
       :param fy: forces iny direction
       :param fx_coords: coordinates of these forces shifted by 0.5 pixel. shift is necessayr because we assume point load
       :param fy_coords:
       :param young: youngs modulus of material
       :param sigma: poisson ratio of material
       :return:
       '''

    # distance for the convolution kernel

    # greens tensor with:
    # [K1,K2,K3]
    # [K4,K5,K6]
    # [K7,K8,K9]
    # returns displacement also in z direction (makes sense because of "pulling" at the buttom of the layer)

    E = young

    if not kernel_size:
        kernel_size = fx.shape

    pixx = np.arange(kernel_size[1])
    pixy = np.arange(kernel_size[0])
    dist_x, dist_y = np.meshgrid(pixy, pixx)  # matrices of distance
    dist_x = dist_x.astype(float)
    dist_y = dist_y.astype(float)
    # makeing sure coorinates are shifted and distance is never exactly zero ... (maybe just exlude zero????)
    if np.mean(dist_x[0, :]).is_integer() or np.mean(dist_y[:, 0]).is_integer():
        dist_x -= np.mean(dist_x[0, :]) - 0.5  # centering
        dist_y -= np.mean(dist_y[:, 0]) - 0.5
    else:
        dist_x -= np.mean(dist_x[0, :])  # centering
        dist_y -= np.mean(dist_y[:, 0])

    dist_x = dist_x * pixelsize
    dist_y = dist_y * pixelsize

    r = np.sqrt(dist_x ** 2 + dist_y ** 2)

    ### elements of the greens tensor
    mu = young / (2 * (1 + sigma))

    A1 = np.zeros(r.shape)
    A2 = np.zeros(r.shape)
    A3 = np.zeros(r.shape)
    A4 = np.zeros(r.shape)

    ## filling the arrays for the green tensor at every r position

    # functions to be integrated when calculating the greens tensor
    def integrand_A1(t, s):
        N = (3 - 4 * sigma) * np.exp(-4 * t) + (-24 * sigma + 10 + 4 * t ** 2 + 16 * sigma ** 2) * np.exp(-2 * t) + (
                3 - 4 * sigma)
        phi1 = (-np.exp(-2 * t) / (N * (1 + np.exp(-2 * t)))) * (
                2 * (sigma - 1) * t ** 2 + 2 * (1 - sigma) * t + 8 * sigma ** 3 - 20 * sigma ** 2 + 21 * sigma - 8 +
                (2 * (sigma - 3) * t ** 2 + 2 * (
                        1 - sigma) * t + 8 * sigma ** 3 - 40 * sigma ** 2 + 48 * sigma - 18) * np.exp(-2 * t)
                + (-4 * sigma ** 2 + 11 * sigma - 6) * np.exp(-4 * t))
        return (phi1 * jv(0, s * t))  # jv(0,t) is zero order besselfunction

    def integrand_A2(t, s):
        N = (3 - 4 * sigma) * np.exp(-4 * t) + (-24 * sigma + 10 + 4 * t ** 2 + 16 * sigma ** 2) * np.exp(-2 * t) + (
                    3 - 4 * sigma)

        phi2 = (-np.exp(-2 * t) / (N * (1 + np.exp(-2 * t)))) * (
                    2 * (sigma - 1) * t ** 2 + 2 * (1 - sigma) * t + 8 * sigma ** 3 - 20 * sigma ** 2 + 13 * sigma - 2 +
                    (2 * (sigma + 1) * t ** 2 + 2 * (1 - sigma) * t + 8 * (sigma - 1) * sigma ** 2 + 2) * np.exp(-2 * t)
                    + sigma * (3 - 4 * sigma) * np.exp(-4 * t))
        return (phi2 * jv(2, s * t))  # jv(2,t) is second order besselfunction

    def integrand_A3(t, s):
        N = (3 - 4 * sigma) * np.exp(-4 * t) + (-24 * sigma + 10 + 4 * t ** 2 + 16 * sigma ** 2) * np.exp(-2 * t) + (
                3 - 4 * sigma)

        phi3 = ((4 * (1 - sigma) * np.exp(-2 * t)) / N) * (t ** 2 + 2 * (2 * sigma - 1) * (sigma - 1))

        return (phi3 * jv(1, s * t))  # jv(1,t) is first order besselfunction

    def integrand_A4(t, s):
        N = (3 - 4 * sigma) * np.exp(-4 * t) + (-24 * sigma + 10 + 4 * t ** 2 + 16 * sigma ** 2) * np.exp(-2 * t) + (
                3 - 4 * sigma)

        phi4 = ((2 * (1 - sigma) * np.exp(-2 * t)) / N) * (
                2 * t * (t + 1) + 8 * sigma ** 2 - 12 * sigma + 5 + (3 - 4 * sigma) * np.exp(-2 * t))

        return (phi4 * jv(0, s * t))  # jv(0,t) is second order besselfunction

    for j, r_s in tqdm(enumerate(r.flatten()), total=r.shape[0] * r.shape[1]):
        s = r_s / h

        # "derivatory part to boussinesq solution"
        A1A = (-1 / (2 * np.pi * mu * h)) * quad(integrand_A1, 0, np.inf, args=s)[0]
        A2A = (-1 / (2 * np.pi * mu * h)) * quad(integrand_A2, 0, np.inf, args=s)[0]
        A3A = (-1 / (2 * np.pi * mu * h)) * quad(integrand_A3, 0, np.inf, args=s)[0]
        #A4A = (-1 / (2 * np.pi * mu * h)) * quad(integrand_A4, 0, np.inf, args=s)[0]

        # part of the boussinesq solution
        A1B = (2 - sigma) / (4 * np.pi * mu * h * s)
        A2B = -sigma / (4 * np.pi * mu * h * s)
        A3B = (1 - 2 * sigma) / (4 * np.pi * mu * h * s)
        A4B = (2 * (1 - sigma)) / (4 * np.pi * mu * h * s)
        index = np.unravel_index(j, r.shape)
        A1[index] = A1A + A1B
        A2[index] = A2A + A2B
        A3[index] = A3A + A3B
        #A4[index] = A4A + A4B

    # componenets of the greens tensor
    K1 = A1 - ((dist_x ** 2 - dist_y ** 2) / (r ** 2)) * A2
    K2 = -(2 * dist_x * dist_y / (r ** 2)) * A2
    #K3 = -(dist_x / r) * A3
    K4 = -(2 * dist_x * dist_y / (r ** 2)) * A2  # is K2
    K5 = A1 + ((dist_x ** 2 - dist_y ** 2) / (r ** 2)) * A2
    #K6 = -(dist_y / r) * A3
    K7 = (dist_x / r) * A3
    K8 = (dist_y / r) * A3
    #K9 = A4


    #deformation by convolution with the kernels
    def_x = convolve2d(fx, K1, mode="same", boundary="fill", fillvalue=0) + convolve2d(fy, K2, mode="same", boundary="fill", fillvalue=0)
    def_y = convolve2d(fx, K4, mode="same", boundary="fill", fillvalue=0) + convolve2d(fy, K5, mode="same", boundary="fill", fillvalue=0)
    def_z = convolve2d(fx, K7, mode="same", boundary="fill", fillvalue=0) + convolve2d(fy, K8, mode="same", boundary="fill", fillvalue=0)


    return def_x,def_y,def_z



def finite_thickenss_convolution_exact_greens_tensor(fx, fy,pixelsize, h, young, sigma=0.5,kernel_size=None):
    '''
    calculating the deformation fieldgiven a tracktion force field using the boussinesq solution for an
     half sphere with finite thickness
     # employs the approximate greens tensor from

     Cell Force Microscopy on Elastic Layers of Finite Thickness
     Rudolf Merkel, Norbert Kirchgeßner, Claudia M. Cesa, and Bernd Hoffman
     Biophysical Journal  Volume 93  November 2007

     This is the "exact solution

    :param fx: forces in x direction
    :param fy: forces iny direction
    :param fx_coords: coordinates of these forces shifted by 0.5 pixel. shift is necessayr because we assume point load
    :param fy_coords:
    :param young: youngs modulus of material
    :param sigma: poisson ratio of material
    :return:
    '''

    # distance for the convolution kernel

    # greens tensor with:
    # [K1,K2,K3]
    # [K4,K5,K6]
    # [K7,K8,K9]
    # returns displacement also in z direction (makes sense because of "pulling" at the buttom of the layer)

    E = young

    if not kernel_size:
        kernel_size = fx.shape

    pixx = np.arange(kernel_size[1])
    pixy = np.arange(kernel_size[0])
    dist_x, dist_y = np.meshgrid(pixy, pixx)  # matrices of distance
    dist_x = dist_x.astype(float)
    dist_y = dist_y.astype(float)
    # makeing sure coorinates are shifted and distance is never exactly zero ... (maybe just exlude zero????)
    if np.mean(dist_x[0, :]).is_integer() or np.mean(dist_y[:, 0]).is_integer():
        dist_x -= np.mean(dist_x[0, :]) - 0.5  # centering
        dist_y -= np.mean(dist_y[:, 0]) - 0.5
    else:
        dist_x -= np.mean(dist_x[0, :])  # centering
        dist_y -= np.mean(dist_y[:, 0])

    dist_x = dist_x * pixelsize
    dist_y = dist_y * pixelsize

    r = np.sqrt(dist_x ** 2 + dist_y ** 2)


    ### elements of the greens tensor
    mu = young / (2 * (1 + sigma))



    A1 = np.zeros(r.shape)
    A2 = np.zeros(r.shape)
    A3 = np.zeros(r.shape)
    A4=np.zeros(r.shape)
    ## filling the arrays for the green tensor at every r position (could be abit faster i guess with applying symetries...
    # aslo leave out A4


    # functions to be integrated when calcualting the greens tensor
    def integrand_A1(t,s):
        N = (3 - 4 * sigma) * np.exp(-4 * t) + (-24 * sigma + 10 + 4 * t ** 2 + 16 * sigma ** 2) * np.exp(-2 * t) + (
                    3 - 4 * sigma)
        phi1 = (-np.exp(-2 * t) / (N * (1 + np.exp(-2 * t)))) * (
                    2 * (sigma - 1) * t ** 2 + 2 * (1 - sigma) * t + 8 * sigma ** 3 - 20 * sigma ** 2 + 21 * sigma - 8 +
                    (2 * (sigma - 3) * t ** 2 + 2 * (
                                1 - sigma) * t + 8 * sigma ** 3 - 40 * sigma ** 2 + 48 * sigma - 18) * np.exp(-2 * t)
                    + (-4 * sigma ** 2 + 11 * sigma - 6) * np.exp(-4 * t))
        return (phi1 * jv(0, s * t))  # jv(0,t) is zero order besselfunction

    def integrand_A2(t,s):
        N = (3 - 4 * sigma) * np.exp(-4*t)+(-24*sigma+10+4*t**2+16*sigma**2)*np.exp(-2*t)+(3-4*sigma)

        phi2=(-np.exp(-2*t)/(N*(1+np.exp(-2*t))))*(2*(sigma-1)*t**2+2*(1-sigma)*t+8*sigma**3-20*sigma**2+13*sigma-2+
                                           (2*(sigma+1)*t**2+2*(1-sigma)*t+8*(sigma-1)*sigma**2+2)*np.exp(-2*t)
                                           +sigma*(3-4*sigma)*np.exp(-4*t))
        return(phi2*jv(2,s*t)) # jv(2,t) is second order besselfunction

    def integrand_A3(t,s):
        N = (3 - 4 * sigma) * np.exp(-4 * t) + (-24 * sigma + 10 + 4 * t ** 2 + 16 * sigma ** 2) * np.exp(-2 * t) + (
                    3 - 4 * sigma)

        phi3 = ((4 * (1 - sigma) * np.exp(-2 * t)) / N) * (t ** 2 + 2 * (2 * sigma - 1) * (sigma - 1))

        return (phi3 * jv(1, s * t))  # jv(1,t) is first order besselfunction

    def integrand_A4(t,s):
        N = (3 - 4 * sigma) * np.exp(-4 * t) + (-24 * sigma + 10 + 4 * t ** 2 + 16 * sigma ** 2) * np.exp(-2 * t) + (
                    3 - 4 * sigma)

        phi4 = ((2 * (1 - sigma) * np.exp(-2 * t)) / N) * (
                    2 * t * (t + 1) + 8 * sigma ** 2 - 12 * sigma + 5 + (3 - 4 * sigma) * np.exp(-2 * t))

        return (phi4 * jv(0, s * t))  # jv(0,t) is second order besselfunction



    for j,r_s in tqdm(enumerate(r.flatten()),total=r.shape[0]*r.shape[1]):
        s = r_s / h

        # "derivatory part to boussinesq solution"
        A1A=(-1/(2*np.pi*mu*h))*quad(integrand_A1,0,np.inf,args=s)[0]
        A2A=(-1/(2*np.pi*mu*h))*quad(integrand_A2,0,np.inf,args=s)[0]
        A3A=(-1/(2*np.pi*mu*h))*quad(integrand_A3,0,np.inf,args=s)[0]
        A4A=(-1/(2*np.pi*mu*h))*quad(integrand_A4,0,np.inf,args=s)[0]

        # part of the boussinesq solution
        A1B=(2-sigma)/(4*np.pi*mu*h*s)
        A2B=-sigma/(4*np.pi*mu*h*s)
        A3B=(1-2*sigma)/(4*np.pi*mu*h*s)
        A4B=(2*(1-sigma))/(4*np.pi*mu*h*s)
        index=np.unravel_index(j,r.shape)
        A1[index]=A1A+A1B
        A2[index]=A2A+A2B
        A3[index]=A3A+A3B
        A4[index]=A4A+A4B

    # componenets of the greesn tensor
    K1 = A1 - ((dist_x ** 2 - dist_y ** 2) / (r ** 2)) * A2
    K2 = -(2 * dist_x * dist_y / (r ** 2)) * A2
    K3 = -(dist_x / r) * A3
    K4 = -(2 * dist_x * dist_y / (r ** 2)) * A2  # is K2
    K5 = A1 + ((dist_x ** 2 - dist_y ** 2) / (r ** 2)) * A2
    K6 = -(dist_y / r) * A3
    K7 = (dist_x / r) * A3
    K8 = (dist_y / r) * A3
    K9 = A4
    return ([K1,K2,K3,K4,K5,K6,K7,K8,K9],[A1,A2,A3,A4])
def finite_thickenss_convolution_only(fx,fy,greens_tensor):
    '''
    uses greens_tensor only
    :param greens_tensor: list of tensor components
    :return:
    '''
    K1, K2, K3, K4, K5, K6, K7, K8, K9=greens_tensor
    #deformation by convolution with the kernels
    def_x = convolve2d(fx, K1, mode="same", boundary="fill", fillvalue=0) + convolve2d(fy, K2, mode="same", boundary="fill", fillvalue=0)
    def_y = convolve2d(fx, K4, mode="same", boundary="fill", fillvalue=0) + convolve2d(fy, K5, mode="same", boundary="fill", fillvalue=0)
    def_z = convolve2d(fx, K7, mode="same", boundary="fill", fillvalue=0) + convolve2d(fy, K8, mode="same", boundary="fill", fillvalue=0)
    return def_x,def_y,def_z