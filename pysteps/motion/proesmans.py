"""
pysteps.motion.proesmans
========================

Implementation of the anisotropic diffusion method by Proesmans et al. (1994).

.. autosummary::
    :toctree: ../generated/

    proesmans
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from pysteps.motion._proesmans import _compute_advection_field

def proesmans(input_images, lam=50.0, num_iter=100, num_levels=6, filter_std=0.0):
    """Implementation of the anisotropic diffusion method by Proesmans et al. (1994).

    Parameters
    ----------
    input_images : array_like
        Array of shape (2, m, n) containing the first and second input image.
    lam : float
        Multiplier of the smoothness term. Smaller values give smoother motion
        field.
    num_iter : float
        The number of iterations to use.
    num_levels : int
        The number of image pyramid levels to use.
    filter_std : float
        Standard deviation of an optional Gaussian filter that is applied before
        computing the optical flow.

    References
    ----------
    :cite:`PGPO1994`

    """
    if (input_images.ndim != 3) or input_images.shape[0] != 2:
        raise ValueError("input_images dimension mismatch.\n" +
                         "input_images.shape: " + str(input_images.shape) +
                         "\n(2, m, n) expected")
    
    im1 = input_images[-2, :, :].copy()
    im2 = input_images[-1, :, :].copy()

    im = np.stack([im1, im2])
    im_min = np.min(im)
    im_max = np.max(im)
    im = (im - im_min) / (im_max - im_min) * 255.0

    if filter_std > 0.0:
        im[0, :, :] = gaussian_filter(im[0, :, :], filter_std)
        im[1, :, :] = gaussian_filter(im[1, :, :], filter_std)

    return _compute_advection_field(im, lam, num_iter, num_levels)